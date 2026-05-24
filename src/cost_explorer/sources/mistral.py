from __future__ import annotations

from cost_explorer.models import SourceResult
from cost_explorer.sources.base import SourceAdapter


class MistralSource(SourceAdapter):
    vendor = "Mistral"
    source_url = "https://mistral.ai/pricing"
    supported = False

    def fetch(self, fetched_at: str) -> SourceResult:
        return SourceResult(
            records=[],
            status=self.unsupported_status(
                fetched_at,
                "Official public page does not currently expose a stable API token pricing table suitable for accurate automated parsing.",
            ),
        )
