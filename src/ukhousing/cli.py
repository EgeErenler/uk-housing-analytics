"""`ukhousing download | load | analyse | site | sample | all`."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ukhousing import config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ukhousing", description=__doc__)
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("download", help="download the yearly Price Paid files")
    sub.add_parser("load", help="load the downloaded files into DuckDB")
    sub.add_parser("analyse", help="run the SQL and export results to CSV")
    site = sub.add_parser("site", help="build the static dashboard from the CSV results")
    site.add_argument("--out", type=Path, default=Path("site"))
    charts = sub.add_parser("charts", help="make PNG charts from the CSV results")
    charts.add_argument("--out", type=Path, default=Path("docs/img"))
    sub.add_parser("sample", help="write synthetic files in the real format")
    sub.add_parser("all", help="download, load and analyse")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    from ukhousing import analyse, ingest

    if args.command in ("download", "all"):
        ingest.download_all(config.RAW_DIR)
    if args.command in ("load", "all"):
        ingest.load(config.DB_PATH, sorted(config.RAW_DIR.glob("pp-*.csv")))
    if args.command in ("analyse", "all"):
        analyse.analyse(config.DB_PATH, config.SQL_DIR, config.OUTPUT_DIR)
    if args.command == "site":
        from ukhousing.site import build_site

        build_site(config.OUTPUT_DIR, args.out)
    if args.command == "charts":
        from ukhousing.charts import make_all

        make_all(config.OUTPUT_DIR, args.out)
    if args.command == "sample":
        from ukhousing.sample import write_sample

        write_sample(config.RAW_DIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
