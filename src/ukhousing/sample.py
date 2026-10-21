"""Synthetic Price Paid rows in the exact file format, for tests and offline demos."""

from __future__ import annotations

import csv
import random
import uuid
from datetime import date, timedelta
from pathlib import Path

BOROUGHS = ["KENSINGTON AND CHELSEA", "CAMDEN", "HACKNEY", "BARKING AND DAGENHAM", "CROYDON"]
BOROUGH_BASE = {
    "KENSINGTON AND CHELSEA": 1_300_000,
    "CAMDEN": 850_000,
    "HACKNEY": 620_000,
    "BARKING AND DAGENHAM": 340_000,
    "CROYDON": 420_000,
}
OUTSIDE = [
    ("LEEDS", "LEEDS", "WEST YORKSHIRE", 230_000),
    ("BRISTOL", "BRISTOL", "BRISTOL", 330_000),
]
TYPE_FACTOR = {"D": 1.6, "S": 1.15, "T": 1.0, "F": 0.7}


def _row(
    rng: random.Random, d: date, london: bool, home: dict | None = None
) -> tuple[list[str], dict]:
    if home is None:
        if london:
            borough = rng.choice(BOROUGHS)
            town, district, county, base = (
                "LONDON",
                borough,
                "GREATER LONDON",
                BOROUGH_BASE[borough],
            )
        else:
            town, district, county, base = rng.choice(OUTSIDE)
        ptype = rng.choices("DSTF", weights=[1, 2, 3, 4 if london else 2])[0]
        home = {
            "postcode": f"{'E' if london else 'LS'}{rng.randint(1, 20)} {rng.randint(1, 9)}AB",
            "paon": str(rng.randint(1, 200)),
            "street": rng.choice(["HIGH STREET", "PARK ROAD", "CHURCH LANE"]),
            "town": town,
            "district": district,
            "county": county,
            "base": base,
            "type": ptype,
        }
    growth = 1.04 ** (d.year - 2018)
    price = home["base"] * TYPE_FACTOR[home["type"]] * growth * rng.uniform(0.75, 1.3)
    new = "Y" if rng.random() < 0.1 else "N"
    if new == "Y":
        price *= 1.15
    duration = "L" if home["type"] == "F" else "F"
    return [
        "{" + str(uuid.UUID(int=rng.getrandbits(128))).upper() + "}",
        str(int(price)),
        f"{d:%Y-%m-%d} 00:00",
        home["postcode"],
        home["type"],
        new,
        duration,
        home["paon"],
        "",
        home["street"],
        "",
        home["town"],
        home["district"],
        home["county"],
        rng.choices("AB", weights=[9, 1])[0],
        "A",
    ], home


def write_sample(
    raw_dir: Path, start_year: int = 2018, end: date | None = None, n: int = 6000, seed: int = 11
) -> list[Path]:
    """Write one CSV per year, like the real files. Some homes sell twice (repeat sales)."""
    rng = random.Random(seed)
    end = end or date(2025, 12, 31)
    start = date(start_year, 1, 1)
    span = (end - start).days
    raw_dir.mkdir(parents=True, exist_ok=True)
    by_year: dict[int, list[list[str]]] = {}
    homes = []
    for _ in range(n):
        d = start + timedelta(days=rng.randint(0, span))
        london = rng.random() < 0.4
        if homes and rng.random() < 0.25:
            # Resell a known home at a later date.
            home, first = rng.choice(homes)
            d = min(end, first + timedelta(days=rng.randint(400, 2000)))
            row, _ = _row(rng, d, london, home)
        else:
            row, home = _row(rng, d, london)
            homes.append((home, d))
        by_year.setdefault(d.year, []).append(row)
    paths = []
    for year, rows in sorted(by_year.items()):
        path = raw_dir / f"pp-{year}.csv"
        with path.open("w", newline="") as fh:
            csv.writer(fh, quoting=csv.QUOTE_ALL).writerows(rows)
        paths.append(path)
    return paths
