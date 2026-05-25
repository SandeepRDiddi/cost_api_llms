from __future__ import annotations

from io import StringIO

import pandas as pd

from cost_explorer.http import fetch_html
from cost_explorer.models import PriceRecord, SourceResult
from cost_explorer.parsing import money_to_float
from cost_explorer.sources.base import SourceAdapter


class XAISource(SourceAdapter):
    vendor = "xAI"
    source_url = "https://docs.x.ai/docs/pricing"

    def fetch(self, fetched_at: str) -> SourceResult:
        html = fetch_html(self.source_url)
        tables = pd.read_html(StringIO(html), flavor="html5lib")

        records: list[PriceRecord] = []
        for frame in tables:
            columns = [str(column) for column in frame.columns]
            if columns[:5] != ["Model", "Context", "Input", "Cached input", "Output"]:
                continue

            for _, row in frame.iterrows():
                model_name = str(row["Model"]).strip()
                records.append(
                    PriceRecord(
                        vendor=self.vendor,
                        model_name=model_name,
                        model_family=model_name.split("-")[0],
                        service_tier="standard",
                        modality="text",
                        context_window=str(row["Context"]).strip(),
                        input_price_per_1m_tokens=money_to_float(str(row["Input"])),
                        output_price_per_1m_tokens=money_to_float(str(row["Output"])),
                        cached_input_price_per_1m_tokens=money_to_float(str(row["Cached input"])),
                        cache_write_price_per_1m_tokens=None,
                        cache_read_price_per_1m_tokens=None,
                        storage_price_per_1m_tokens_per_hour=None,
                        price_unit="USD per 1M tokens",
                        currency="USD",
                        pricing_notes="Official xAI Chat API pricing.",
                        source_url=self.source_url,
                        fetched_at=fetched_at,
                    )
                )
            break

        return SourceResult(
            records=records,
            status=self.ok_status(
                fetched_at,
                "Parsed xAI Chat API token pricing from docs.x.ai.",
                len(records),
            ),
        )
