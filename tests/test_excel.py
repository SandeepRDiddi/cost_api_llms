import pandas as pd

from cost_explorer.excel import export_workbook
from cost_explorer.models import PriceRecord, SourceStatus
from cost_explorer.normalize import build_vendor_summary, records_to_dataframe, statuses_to_dataframe


def _current_prices(fetched_at: str) -> pd.DataFrame:
    return records_to_dataframe(
        [
            PriceRecord(
                vendor="OpenAI",
                model_name="gpt-test",
                model_family="gpt",
                service_tier="standard",
                modality="text",
                context_window="128k",
                input_price_per_1m_tokens=1.0,
                output_price_per_1m_tokens=2.0,
                cached_input_price_per_1m_tokens=None,
                cache_write_price_per_1m_tokens=None,
                cache_read_price_per_1m_tokens=None,
                storage_price_per_1m_tokens_per_hour=None,
                price_unit="per_1m_tokens",
                currency="USD",
                pricing_notes="test",
                source_url="https://example.com",
                fetched_at=fetched_at,
            )
        ]
    )


def _source_status(fetched_at: str) -> pd.DataFrame:
    return statuses_to_dataframe(
        [
            SourceStatus(
                vendor="OpenAI",
                status="ok",
                supported=True,
                source_url="https://example.com",
                detail="ok",
                records_count=1,
                fetched_at=fetched_at,
            )
        ]
    )


def test_export_workbook_uses_one_master_file_and_appends_history(tmp_path):
    workbook_path = tmp_path / "llm_costs.xlsx"

    first_prices = _current_prices("2026-05-24T10:00:00+00:00")
    export_workbook(
        workbook_path=workbook_path,
        current_prices=first_prices,
        source_status=_source_status("2026-05-24T10:00:00+00:00"),
        vendor_summary=build_vendor_summary(first_prices),
        metadata={
            "generated_at": "2026-05-24T10:00:00+00:00",
            "records_count": 1,
            "status_rows": 1,
            "partial_run": False,
        },
    )

    second_prices = _current_prices("2026-05-25T10:00:00+00:00")
    export_workbook(
        workbook_path=workbook_path,
        current_prices=second_prices,
        source_status=_source_status("2026-05-25T10:00:00+00:00"),
        vendor_summary=build_vendor_summary(second_prices),
        metadata={
            "generated_at": "2026-05-25T10:00:00+00:00",
            "records_count": 1,
            "status_rows": 1,
            "partial_run": False,
        },
    )

    export_workbook(
        workbook_path=workbook_path,
        current_prices=second_prices,
        source_status=_source_status("2026-05-25T10:00:00+00:00"),
        vendor_summary=build_vendor_summary(second_prices),
        metadata={
            "generated_at": "2026-05-25T10:00:00+00:00",
            "records_count": 1,
            "status_rows": 1,
            "partial_run": False,
        },
    )

    workbook = pd.ExcelFile(workbook_path, engine="openpyxl")
    assert set(workbook.sheet_names) == {
        "prices_current",
        "source_status",
        "vendor_summary",
        "price_history",
        "run_metadata",
    }

    current_prices = pd.read_excel(workbook_path, sheet_name="prices_current", engine="openpyxl")
    history = pd.read_excel(workbook_path, sheet_name="price_history", engine="openpyxl")
    metadata = pd.read_excel(workbook_path, sheet_name="run_metadata", engine="openpyxl")

    assert current_prices["fetched_at"].tolist() == ["2026-05-25T10:00:00+00:00"]
    assert history["fetched_at"].tolist() == [
        "2026-05-24T10:00:00+00:00",
        "2026-05-25T10:00:00+00:00",
    ]
    assert metadata.loc[0, "generated_at"] == "2026-05-25T10:00:00+00:00"
