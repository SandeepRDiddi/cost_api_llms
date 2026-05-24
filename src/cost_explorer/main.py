from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from cost_explorer.excel import export_workbook
from cost_explorer.models import SourceStatus
from cost_explorer.normalize import build_vendor_summary, combine_history, records_to_dataframe, statuses_to_dataframe
from cost_explorer.sources import get_sources


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch official LLM pricing pages and export analysis files.")
    parser.add_argument("--output-dir", default="data", help="Directory for current outputs.")
    parser.add_argument("--history-dir", default="data/history", help="Directory for dated snapshot files.")
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Continue and write outputs even if a supported source fails.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    history_dir = Path(args.history_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    history_dir.mkdir(parents=True, exist_ok=True)

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

    snapshot_path = history_dir / f"prices_{fetched_at.replace(':', '-').replace('+00:00', 'Z')}.csv"
    current_prices.to_csv(snapshot_path, index=False)
    history = combine_history(history_dir)

    current_prices.to_csv(output_dir / "prices_current.csv", index=False)
    current_prices.to_json(output_dir / "prices_current.json", orient="records", indent=2)
    source_status.to_csv(output_dir / "source_status.csv", index=False)
    history.to_csv(output_dir / "prices_history.csv", index=False)

    export_workbook(
        workbook_path=output_dir / "llm_costs.xlsx",
        current_prices=current_prices,
        source_status=source_status,
        vendor_summary=vendor_summary,
        history=history,
    )

    metadata = {
        "generated_at": fetched_at,
        "records_count": len(records),
        "status_rows": len(statuses),
        "partial_run": bool(failures),
    }
    (output_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return 0
