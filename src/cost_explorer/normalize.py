from __future__ import annotations

from pathlib import Path

import pandas as pd

from cost_explorer.models import PriceRecord, SourceStatus


PRICE_COLUMNS = [
    "vendor",
    "model_name",
    "model_family",
    "service_tier",
    "modality",
    "context_window",
    "input_price_per_1m_tokens",
    "output_price_per_1m_tokens",
    "cached_input_price_per_1m_tokens",
    "cache_write_price_per_1m_tokens",
    "cache_read_price_per_1m_tokens",
    "storage_price_per_1m_tokens_per_hour",
    "price_unit",
    "currency",
    "pricing_notes",
    "source_url",
    "fetched_at",
]


def records_to_dataframe(records: list[PriceRecord]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=PRICE_COLUMNS)
    frame = pd.DataFrame([record.to_dict() for record in records])
    return frame[PRICE_COLUMNS].sort_values(
        by=["vendor", "model_name", "service_tier", "modality"], kind="stable"
    ).reset_index(drop=True)


def statuses_to_dataframe(statuses: list[SourceStatus]) -> pd.DataFrame:
    if not statuses:
        return pd.DataFrame(
            columns=["vendor", "status", "supported", "source_url", "detail", "records_count", "fetched_at"]
        )
    frame = pd.DataFrame([status.to_dict() for status in statuses])
    return frame.sort_values(by=["vendor"], kind="stable").reset_index(drop=True)


def build_vendor_summary(current_prices: pd.DataFrame) -> pd.DataFrame:
    if current_prices.empty:
        return pd.DataFrame(
            columns=["vendor", "model_count", "min_input_price", "max_input_price", "min_output_price", "max_output_price"]
        )

    summary = (
        current_prices.groupby("vendor", dropna=False)
        .agg(
            model_count=("model_name", "nunique"),
            min_input_price=("input_price_per_1m_tokens", "min"),
            max_input_price=("input_price_per_1m_tokens", "max"),
            min_output_price=("output_price_per_1m_tokens", "min"),
            max_output_price=("output_price_per_1m_tokens", "max"),
        )
        .reset_index()
    )
    return summary


def combine_history(history_dir: Path) -> pd.DataFrame:
    snapshots = sorted(history_dir.glob("prices_*.csv"))
    if not snapshots:
        return pd.DataFrame(columns=PRICE_COLUMNS)

    frames = [pd.read_csv(path) for path in snapshots]
    history = pd.concat(frames, ignore_index=True)
    history = history.drop_duplicates(
        subset=["vendor", "model_name", "service_tier", "modality", "fetched_at"], keep="last"
    )
    return history.sort_values(
        by=["fetched_at", "vendor", "model_name", "service_tier", "modality"], kind="stable"
    ).reset_index(drop=True)
