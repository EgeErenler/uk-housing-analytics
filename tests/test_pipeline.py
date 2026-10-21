"""End-to-end run on synthetic files that use the real file format."""

from __future__ import annotations

import csv

from ukhousing.analyse import analyse
from ukhousing.config import SQL_DIR, year_url, years
from ukhousing.ingest import load
from ukhousing.sample import write_sample


def test_year_urls_and_range():
    assert year_url(2024).endswith("/pp-2024.csv")
    assert years()[0] == 2018


def test_full_pipeline_on_sample(tmp_path):
    files = write_sample(tmp_path / "raw", n=2000)
    assert load(tmp_path / "h.duckdb", files) == 2000

    outputs = analyse(tmp_path / "h.duckdb", SQL_DIR, tmp_path / "out")
    assert len(outputs) >= 10

    with (tmp_path / "out" / "london_boroughs.csv").open() as fh:
        boroughs = list(csv.DictReader(fh))
    ranks = sorted(int(b["price_rank"]) for b in boroughs)
    assert ranks == list(range(1, len(boroughs) + 1))
    assert {b["borough"] for b in boroughs} <= {
        "Kensington and Chelsea",
        "Camden",
        "Hackney",
        "Barking and Dagenham",
        "Croydon",
    }
