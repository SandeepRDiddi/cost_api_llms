from __future__ import annotations

from io import StringIO

import pandas as pd
from bs4 import BeautifulSoup, Tag

from cost_explorer.http import fetch_html
from cost_explorer.models import PriceRecord, SourceResult
from cost_explorer.parsing import (
    extract_all_money_values,
    money_to_float,
    normalize_whitespace,
    split_labeled_money_values,
    slugify,
)
from cost_explorer.sources.base import SourceAdapter


class GoogleSource(SourceAdapter):
    vendor = "Google"
    source_url = "https://ai.google.dev/gemini-api/docs/pricing?hl=en"

    def fetch(self, fetched_at: str) -> SourceResult:
        html = fetch_html(self.source_url)
        soup = BeautifulSoup(html, "html.parser")

        records: list[PriceRecord] = []
        for heading in soup.find_all("h2"):
            model_name = normalize_whitespace(heading.get_text(" ", strip=True))
            if not model_name.startswith("Gemini"):
                continue

            current_tier = ""
            for element in heading.next_elements:
                if element is heading:
                    continue
                if isinstance(element, Tag) and element.name == "h2":
                    break
                if not isinstance(element, Tag):
                    continue
                if element.name == "h3":
                    current_tier = slugify(element.get_text(" ", strip=True))
                    continue
                if element.name != "table" or not current_tier:
                    continue

                frame = pd.read_html(StringIO(str(element)), flavor="html5lib")[0]
                records.extend(self._parse_table(model_name, current_tier, frame, fetched_at))

        return SourceResult(
            records=records,
            status=self.ok_status(
                fetched_at,
                "Parsed Gemini API pricing tables from ai.google.dev.",
                len(records),
            ),
        )

    def _parse_table(
        self,
        model_name: str,
        service_tier: str,
        frame: pd.DataFrame,
        fetched_at: str,
    ) -> list[PriceRecord]:
        first_column = frame.columns[0]
        if "Input price" not in frame[first_column].astype(str).tolist():
            return []

        row_map = {
            normalize_whitespace(str(row[first_column])): normalize_whitespace(str(row[frame.columns[-1]]))
            for _, row in frame.iterrows()
        }
        input_pairs = split_labeled_money_values(row_map.get("Input price", ""))
        output_value = money_to_float(row_map.get("Output price (including thinking tokens)", ""))
        cache_pairs = split_labeled_money_values(row_map.get("Context caching price", ""))
        storage_values = extract_all_money_values(row_map.get("Context caching price", ""))
        storage_price = storage_values[-1] if len(storage_values) > 1 else None

        if not input_pairs and output_value is None:
            return []

        if not input_pairs:
            input_pairs = [("default", None)]

        cache_map = {label: value for label, value in cache_pairs}
        if "default" in cache_map:
            default_cache = cache_map["default"]
        else:
            default_cache = None

        records: list[PriceRecord] = []
        for label, input_price in input_pairs:
            modality = "text" if label == "default" else label
            cached_price = cache_map.get(label, default_cache)
            records.append(
                PriceRecord(
                    vendor=self.vendor,
                    model_name=model_name,
                    model_family=model_name.split()[1].lower() if len(model_name.split()) > 1 else "gemini",
                    service_tier=service_tier,
                    modality=modality,
                    context_window=None,
                    input_price_per_1m_tokens=input_price,
                    output_price_per_1m_tokens=output_value,
                    cached_input_price_per_1m_tokens=cached_price,
                    cache_write_price_per_1m_tokens=None,
                    cache_read_price_per_1m_tokens=None,
                    storage_price_per_1m_tokens_per_hour=storage_price,
                    price_unit="USD per 1M tokens",
                    currency="USD",
                    pricing_notes=row_map.get("Context caching price", ""),
                    source_url=self.source_url,
                    fetched_at=fetched_at,
                )
            )
        return records
