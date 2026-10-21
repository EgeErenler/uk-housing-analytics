"""Paths and constants. Override paths with environment variables."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

BASE_URL = "https://price-paid-data.publicdata.landregistry.gov.uk"
FIRST_YEAR = 2018

# Paths are relative to the folder you run the command from (the repository root).
SQL_DIR = Path(os.getenv("UKH_SQL_DIR", "sql"))
RAW_DIR = Path(os.getenv("UKH_RAW_DIR", "data/raw"))
DB_PATH = Path(os.getenv("UKH_DB_PATH", "data/housing.duckdb"))
OUTPUT_DIR = Path(os.getenv("UKH_OUTPUT_DIR", "outputs"))

# The files have no header row. Column order is documented by HM Land Registry.
PPD_COLUMNS = {
    "transaction_id": "VARCHAR",
    "price": "BIGINT",
    "transfer_date": "TIMESTAMP",
    "postcode": "VARCHAR",
    "property_type": "VARCHAR",
    "old_new": "VARCHAR",
    "duration": "VARCHAR",
    "paon": "VARCHAR",
    "saon": "VARCHAR",
    "street": "VARCHAR",
    "locality": "VARCHAR",
    "town_city": "VARCHAR",
    "district": "VARCHAR",
    "county": "VARCHAR",
    "ppd_category": "VARCHAR",
    "record_status": "VARCHAR",
}


def years(today: date | None = None) -> list[int]:
    today = today or date.today()
    return list(range(FIRST_YEAR, today.year + 1))


def year_url(year: int) -> str:
    return f"{BASE_URL}/pp-{year}.csv"
