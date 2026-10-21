"""Download the yearly Price Paid files and load them into DuckDB."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

import duckdb
import requests

from ukhousing.config import PPD_COLUMNS, year_url, years

log = logging.getLogger(__name__)


def download_year(year: int, raw_dir: Path, force: bool = False) -> Path:
    """Stream one yearly CSV to disk. Past years never change, so they are cached."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    target = raw_dir / f"pp-{year}.csv"
    if target.exists() and target.stat().st_size > 0 and not force:
        log.info("pp-%s.csv already downloaded", year)
        return target
    tmp = target.with_suffix(".part")
    with requests.get(year_url(year), stream=True, timeout=120) as response:
        response.raise_for_status()
        with tmp.open("wb") as fh:
            for chunk in response.iter_content(chunk_size=1 << 20):
                fh.write(chunk)
    tmp.replace(target)
    log.info("downloaded pp-%s.csv (%.0f MB)", year, target.stat().st_size / 1e6)
    return target


def download_all(raw_dir: Path) -> list[Path]:
    # The current year grows every month, and late registrations still change last year's file.
    current = date.today().year
    return [download_year(y, raw_dir, force=(y >= current - 1)) for y in years()]


def load(db_path: Path, csv_paths: list[Path]) -> int:
    """(Re)build the `ppd` table from the CSV files and return its row count."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    files = ", ".join(f"'{p.as_posix()}'" for p in csv_paths)
    columns = ", ".join(f"'{name}': '{dtype}'" for name, dtype in PPD_COLUMNS.items())
    con = duckdb.connect(str(db_path))
    try:
        con.execute(
            f"""
            create or replace table ppd as
            select * from read_csv(
                [{files}],
                header = false,
                columns = {{{columns}}},
                quote = '"',
                null_padding = true
            )
            """
        )
        count = con.execute("select count(*) from ppd").fetchone()[0]
    finally:
        con.close()
    log.info("loaded %s rows into %s", f"{count:,}", db_path)
    return count
