from __future__ import annotations

import re

from bs4 import BeautifulSoup

from cost_explorer.http import fetch_html
from cost_explorer.models import PriceRecord, SourceResult
from cost_explorer.sources.base import SourceAdapter


class AnthropicSource(SourceAdapter):
    vendor = "Anthropic"
    source_url = "https://www.anthropic.com/pricing#api"

    _BLOCK_PATTERN = re.compile(
        r"((?:Opus|Sonnet|Haiku)\s+[0-9.]+).*?Input\s+\$\s*([0-9.]+)\s*/\s*MTok"
        r".*?Output\s+\$\s*([0-9.]+)\s*/\s*MTok.*?Prompt caching\s+Write\s+\$\s*([0-9.]+)\s*/\s*MTok"
        r".*?Read\s+\$\s*([0-9.]+)\s*/\s*MTok",
        re.IGNORECASE | re.DOTALL,
    )

    def fetch(self, fetched_at: str) -> SourceResult:
        html = fetch_html(self.source_url)
        text = BeautifulSoup(html, "html.parser").get_text("\n")
        compact = " ".join(line.strip() for line in text.splitlines() if line.strip())

        records: list[PriceRecord] = []
        for match in self._BLOCK_PATTERN.finditer(compact):
            short_name, input_price, output_price, cache_write, cache_read = match.groups()
            model_name = f"Claude {short_name}"
            records.append(
                PriceRecord(
                    vendor=self.vendor,
                    model_name=model_name,
                    model_family=short_name.split()[0].lower(),
                    service_tier="standard",
                    modality="text",
                    context_window=None,
                    input_price_per_1m_tokens=float(input_price),
                    output_price_per_1m_tokens=float(output_price),
                    cached_input_price_per_1m_tokens=None,
                    cache_write_price_per_1m_tokens=float(cache_write),
                    cache_read_price_per_1m_tokens=float(cache_read),
                    storage_price_per_1m_tokens_per_hour=None,
                    price_unit="USD per 1M tokens",
                    currency="USD",
                    pricing_notes="Official Anthropic API pricing page.",
                    source_url=self.source_url,
                    fetched_at=fetched_at,
                )
            )

        return SourceResult(
            records=records,
            status=self.ok_status(
                fetched_at,
                "Parsed latest and legacy Claude token pricing from anthropic.com.",
                len(records),
            ),
        )
