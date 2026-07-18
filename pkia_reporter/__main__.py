"""
pkia_reporter CLI entry point.

Usage:
    python -m pkia_reporter                          # today, default storage path
    python -m pkia_reporter --date 2026-07-17        # specific date
    python -m pkia_reporter --storage /tmp/data.json # custom data source
    python -m pkia_reporter --output-dir /tmp/reports
"""

import os
import sys
import logging
import argparse
from datetime import date

from .reporter import load_json, generate_report, write_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pkia_reporter")

DEFAULT_STORAGE = os.getenv(
    "PKIA_STORAGE_PATH",
    os.path.join(os.getcwd(), "latest_run.json"),
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PKIA Daily Report Generator")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Report date (YYYY-MM-DD). Defaults to today.",
    )
    parser.add_argument(
        "--storage",
        type=str,
        default=DEFAULT_STORAGE,
        help="Path to JSON/JSONL data file. Default: latest_run.json",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=os.getenv("PKIA_REPORTS_DIR", os.path.join(os.getcwd(), "reports")),
        help="Output directory for generated reports. Default: reports/",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None):
    args = parse_args(argv)

    report_date = args.date or str(date.today())

    projects = load_json(args.storage)
    if not projects:
        logger.warning("No data loaded — generating empty report")

    report = generate_report(projects, report_date=report_date)
    path = write_report(report, args.output_dir, report_date=report_date)

    print(f"\n✅ Report generated: {path} ({len(projects)} projects)")


if __name__ == "__main__":
    main()
