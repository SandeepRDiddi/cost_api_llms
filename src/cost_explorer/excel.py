from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl.utils import get_column_letter

from cost_explorer.normalize import PRICE_COLUMNS, merge_price_history


METADATA_COLUMNS = ["generated_at", "records_count", "status_rows", "partial_run"]


def _load_existing_history(workbook_path: Path) -> pd.DataFrame:
    if not workbook_path.exists():
        return pd.DataFrame(columns=PRICE_COLUMNS)

    workbook = pd.ExcelFile(workbook_path, engine="openpyxl")
    if "price_history" not in workbook.sheet_names:
        return pd.DataFrame(columns=PRICE_COLUMNS)

    history = pd.read_excel(workbook_path, sheet_name="price_history", engine="openpyxl")
    return history.reindex(columns=PRICE_COLUMNS)


def export_workbook(
    workbook_path: Path,
    current_prices: pd.DataFrame,
    source_status: pd.DataFrame,
    vendor_summary: pd.DataFrame,
    metadata: dict[str, object],
) -> pd.DataFrame:
    workbook_path.parent.mkdir(parents=True, exist_ok=True)
    history = merge_price_history(_load_existing_history(workbook_path), current_prices)
    metadata_frame = pd.DataFrame([metadata]).reindex(columns=METADATA_COLUMNS)

    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        current_prices.to_excel(writer, index=False, sheet_name="prices_current")
        source_status.to_excel(writer, index=False, sheet_name="source_status")
        vendor_summary.to_excel(writer, index=False, sheet_name="vendor_summary")
        history.to_excel(writer, index=False, sheet_name="price_history")
        metadata_frame.to_excel(writer, index=False, sheet_name="run_metadata")

        for sheet_name, frame in {
            "prices_current": current_prices,
            "source_status": source_status,
            "vendor_summary": vendor_summary,
            "price_history": history,
            "run_metadata": metadata_frame,
        }.items():
            worksheet = writer.sheets[sheet_name]
            for index, column in enumerate(frame.columns, start=1):
                width = max([len(column), *(len(str(value)) for value in frame[column].head(200))]) + 2
                worksheet.column_dimensions[get_column_letter(index)].width = min(width, 50)

    return history
