from __future__ import annotations

from cost_explorer.models import SourceResult
from cost_explorer.sources.base import SourceAdapter


class CohereSource(SourceAdapter):
    vendor = "Cohere"
    source_url = "https://cohere.com/pricing"
    supported = False

    def fetch(self, fetched_at: str) -> SourceResult:
        return SourceResult(
            records=[],
            status=self.unsupported_status(
                fetched_at,
                "Official public page exposes enterprise and Model Vault pricing, not a stable public API token pricing table.",
            ),
        )
