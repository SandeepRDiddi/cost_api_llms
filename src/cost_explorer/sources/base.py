from __future__ import annotations

from abc import ABC, abstractmethod

from cost_explorer.models import SourceResult, SourceStatus


class SourceAdapter(ABC):
    vendor: str
    source_url: str
    supported: bool = True

    @abstractmethod
    def fetch(self, fetched_at: str) -> SourceResult:
        raise NotImplementedError

    def ok_status(self, fetched_at: str, detail: str, records_count: int) -> SourceStatus:
        return SourceStatus(
            vendor=self.vendor,
            status="ok",
            supported=self.supported,
            source_url=self.source_url,
            detail=detail,
            records_count=records_count,
            fetched_at=fetched_at,
        )

    def unsupported_status(self, fetched_at: str, detail: str) -> SourceStatus:
        return SourceStatus(
            vendor=self.vendor,
            status="unsupported",
            supported=False,
            source_url=self.source_url,
            detail=detail,
            records_count=0,
            fetched_at=fetched_at,
        )
