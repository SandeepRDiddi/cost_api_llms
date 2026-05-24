from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from cost_explorer.excel import export_workbook
from cost_explorer.models import SourceStatus
from cost_explorer.normalize import build_vendor_summary, records_to_dataframe, statuses_to_dataframe
from cost_explorer.sources import get_sources


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch official LLM pricing pages and update a master Excel workbook.")
    parser.add_argument("--output-dir", default="data", help="Directory for the master workbook output.")
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Continue and write outputs even if a supported source fails.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    records = []
    statuses = []
    failures: list[str] = []

    for source in get_sources():
        try:
            result = source.fetch(fetched_at)
            if source.supported and not result.records:
                raise RuntimeError("supported source returned zero pricing records")
            records.extend(result.records)
            statuses.append(result.status)
        except Exception as exc:  # noqa: BLE001
            message = f"{source.vendor}: {exc}"
            failures.append(message)
            statuses.append(
                SourceStatus(
                    vendor=source.vendor,
                    status="error",
                    supported=source.supported,
                    source_url=source.source_url,
                    fetched_at=fetched_at,
                    detail=f"ERROR: {exc}",
                    records_count=0,
                )
            )

    if failures and not args.allow_partial:
        raise RuntimeError("Supported source fetch failed: " + " | ".join(failures))

    current_prices = records_to_dataframe(records)
    source_status = statuses_to_dataframe(statuses)
    vendor_summary = build_vendor_summary(current_prices)

    export_workbook(
        workbook_path=output_dir / "llm_costs.xlsx",
        current_prices=current_prices,
        source_status=source_status,
        vendor_summary=vendor_summary,
        metadata={
            "generated_at": fetched_at,
            "records_count": len(records),
            "status_rows": len(statuses),
            "partial_run": bool(failures),
        },
    )
    return 0
