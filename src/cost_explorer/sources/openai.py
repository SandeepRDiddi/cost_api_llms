from __future__ import annotations

from io import StringIO

import pandas as pd
from bs4 import BeautifulSoup

from cost_explorer.http import fetch_html
from cost_explorer.models import PriceRecord, SourceResult
from cost_explorer.parsing import first_non_empty, money_to_float, normalize_whitespace, slugify
from cost_explorer.sources.base import SourceAdapter


class OpenAISource(SourceAdapter):
    vendor = "OpenAI"
    source_url = "https://developers.openai.com/api/docs/pricing?latest-pricing=flex"

    def fetch(self, fetched_at: str) -> SourceResult:
        html = fetch_html(self.source_url)
        soup = BeautifulSoup(html, "html.parser")
        table_tags = soup.find_all("table")
        tables = pd.read_html(StringIO(html), flavor="html5lib")

        records: list[PriceRecord] = []
        seen: set[tuple[str, str, str, str]] = set()

        for index, frame in enumerate(tables):
            if index >= len(table_tags):
                break
            records.extend(self._parse_table(frame, table_tags[index], fetched_at, seen))

        return SourceResult(
            records=records,
            status=self.ok_status(
                fetched_at,
                "Parsed official OpenAI pricing tables from developers.openai.com.",
                len(records),
            ),
        )

    def _parse_table(
        self,
        frame: pd.DataFrame,
        table_tag,
        fetched_at: str,
        seen: set[tuple[str, str, str, str]],
    ) -> list[PriceRecord]:
        frame = frame.copy()
        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = [
                normalize_whitespace(" ".join(str(part) for part in column if str(part) != "nan"))
                for column in frame.columns
            ]
        else:
            frame.columns = [normalize_whitespace(str(column)) for column in frame.columns]

        headings = self._context_headings(table_tag)
        heading_text = " | ".join(headings)
        tier = self._service_tier_from_headings(headings)
        records: list[PriceRecord] = []

        if "Model" not in frame.columns:
            model_candidates = [column for column in frame.columns if column.endswith("Model")]
            if model_candidates:
                frame = frame.rename(columns={model_candidates[0]: "Model"})

        if "Model" not in frame.columns:
            return records

        if any(column.startswith("Short context") for column in frame.columns):
            for _, row in frame.iterrows():
                model_name = str(row["Model"]).strip()
                records.extend(
                    self._add_context_record(
                        model_name=model_name,
                        service_tier=f"{tier}-short-context",
                        modality="text",
                        context_window="short",
                        input_value=row.get("Short context Input"),
                        cached_value=row.get("Short context Cached input"),
                        output_value=row.get("Short context Output"),
                        heading_text=heading_text,
                        fetched_at=fetched_at,
                        seen=seen,
                    )
                )
                records.extend(
                    self._add_context_record(
                        model_name=model_name,
                        service_tier=f"{tier}-long-context",
                        modality="text",
                        context_window="long",
                        input_value=row.get("Long context Input"),
                        cached_value=row.get("Long context Cached input"),
                        output_value=row.get("Long context Output"),
                        heading_text=heading_text,
                        fetched_at=fetched_at,
                        seen=seen,
                    )
                )
            return records

        if {"Input", "Output"}.issubset(frame.columns):
            for _, row in frame.iterrows():
                model_name = str(row["Model"]).strip()
                modality = first_non_empty(str(row.get("Modality", "")), "text").lower()
                input_price = money_to_float(str(row.get("Input", "")))
                output_price = money_to_float(str(row.get("Output", row.get("Output / cost", ""))))
                cached_price = money_to_float(str(row.get("Cached input", "")))
                if input_price is None and output_price is None:
                    continue

                key = (model_name, tier, modality, heading_text)
                if key in seen:
                    continue
                seen.add(key)
                records.append(
                    PriceRecord(
                        vendor=self.vendor,
                        model_name=model_name,
                        model_family=model_name.split("-")[0],
                        service_tier=tier,
                        modality=modality,
                        context_window=None,
                        input_price_per_1m_tokens=input_price,
                        output_price_per_1m_tokens=output_price,
                        cached_input_price_per_1m_tokens=cached_price,
                        cache_write_price_per_1m_tokens=None,
                        cache_read_price_per_1m_tokens=None,
                        storage_price_per_1m_tokens_per_hour=None,
                        price_unit="USD per 1M tokens",
                        currency="USD",
                        pricing_notes=heading_text,
                        source_url=self.source_url,
                        fetched_at=fetched_at,
                    )
                )
        return records

    def _add_context_record(
        self,
        model_name: str,
        service_tier: str,
        modality: str,
        context_window: str,
        input_value,
        cached_value,
        output_value,
        heading_text: str,
        fetched_at: str,
        seen: set[tuple[str, str, str, str]],
    ) -> list[PriceRecord]:
        input_price = money_to_float(str(input_value))
        output_price = money_to_float(str(output_value))
        cached_price = money_to_float(str(cached_value))
        if input_price is None and output_price is None:
            return []

        key = (model_name, service_tier, modality, heading_text)
        if key in seen:
            return []
        seen.add(key)
        return [
            PriceRecord(
                vendor=self.vendor,
                model_name=model_name,
                model_family=model_name.split("-")[0],
                service_tier=service_tier,
                modality=modality,
                context_window=context_window,
                input_price_per_1m_tokens=input_price,
                output_price_per_1m_tokens=output_price,
                cached_input_price_per_1m_tokens=cached_price,
                cache_write_price_per_1m_tokens=None,
                cache_read_price_per_1m_tokens=None,
                storage_price_per_1m_tokens_per_hour=None,
                price_unit="USD per 1M tokens",
                currency="USD",
                pricing_notes=heading_text,
                source_url=self.source_url,
                fetched_at=fetched_at,
            )
        ]

    def _context_headings(self, table_tag) -> list[str]:
        headings: list[str] = []
        cursor = table_tag
        while len(headings) < 4:
            cursor = cursor.find_previous(["h2", "h3", "h4", "p"])
            if cursor is None:
                break
            text = normalize_whitespace(cursor.get_text(" ", strip=True))
            if text and text not in headings:
                headings.append(text)
        return list(reversed(headings))

    def _service_tier_from_headings(self, headings: list[str]) -> str:
        for heading in reversed(headings):
            lower = heading.lower()
            for candidate in ("standard", "flex", "priority", "batch"):
                if lower == candidate:
                    return candidate
        for heading in reversed(headings):
            lower = heading.lower()
            for candidate in ("standard", "flex", "priority", "batch"):
                if candidate in lower:
                    return candidate
        return slugify(headings[-1] if headings else "standard")
