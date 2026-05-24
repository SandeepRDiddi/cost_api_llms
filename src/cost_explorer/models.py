from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass(frozen=True)
class PriceRecord:
    vendor: str
    model_name: str
    model_family: str
    service_tier: str
    modality: str
    context_window: Optional[str]
    input_price_per_1m_tokens: Optional[float]
    output_price_per_1m_tokens: Optional[float]
    cached_input_price_per_1m_tokens: Optional[float]
    cache_write_price_per_1m_tokens: Optional[float]
    cache_read_price_per_1m_tokens: Optional[float]
    storage_price_per_1m_tokens_per_hour: Optional[float]
    price_unit: str
    currency: str
    pricing_notes: str
    source_url: str
    fetched_at: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SourceStatus:
    vendor: str
    status: str
    supported: bool
    source_url: str
    detail: str
    records_count: int
    fetched_at: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SourceResult:
    records: list[PriceRecord]
    status: SourceStatus
