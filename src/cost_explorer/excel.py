from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl.utils import get_column_letter


def export_workbook(
    workbook_path: Path,
    current_prices: pd.DataFrame,
    source_status: pd.DataFrame,
    vendor_summary: pd.DataFrame,
    history: pd.DataFrame,
) -> None:
    workbook_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        current_prices.to_excel(writer, index=False, sheet_name="prices_current")
        source_status.to_excel(writer, index=False, sheet_name="source_status")
        vendor_summary.to_excel(writer, index=False, sheet_name="vendor_summary")
        history.to_excel(writer, index=False, sheet_name="price_history")

        for sheet_name, frame in {
            "prices_current": current_prices,
            "source_status": source_status,
            "vendor_summary": vendor_summary,
            "price_history": history,
        }.items():
            worksheet = writer.sheets[sheet_name]
            for index, column in enumerate(frame.columns, start=1):
                width = max([len(column), *(len(str(value)) for value in frame[column].head(200))]) + 2
                worksheet.column_dimensions[get_column_letter(index)].width = min(width, 50)
