"""Turn the CSV results into a single static HTML dashboard."""

from __future__ import annotations

import csv
import json
import logging
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from typing import Any

from jinja2 import Template

log = logging.getLogger(__name__)


def _value(text: str) -> Any:
    if text == "":
        return None
    if text in ("true", "false"):
        return text == "true"
    try:
        number = float(text)
    except ValueError:
        return text
    return int(number) if number.is_integer() and "." not in text else number


def read_outputs(output_dir: Path) -> dict[str, list[dict[str, Any]]]:
    data = {}
    for path in sorted(output_dir.glob("*.csv")):
        with path.open(newline="") as fh:
            data[path.stem] = [{k: _value(v) for k, v in row.items()} for row in csv.DictReader(fh)]
    return data


def _gbp(x: float) -> str:
    return f"£{x / 1000:,.0f}k" if x < 1_000_000 else f"£{x / 1_000_000:,.2f}m"


def headline(data: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """A few numbers for the top of the page, computed here so the text never goes stale."""
    yearly = data["yearly_summary"]
    latest = data["coverage"][0]["latest_complete_year"]

    def pick(area: str, year: int) -> dict[str, Any]:
        return next(r for r in yearly if r["area"] == area and r["sale_year"] == year)

    ew, ldn, rest = (pick(a, latest) for a in ("England and Wales", "London", "Outside London"))
    ew_years = [r for r in yearly if r["area"] == "England and Wales" and r["is_complete_year"]]
    peak = max(ew_years, key=lambda r: r["transactions"])
    boroughs = data["london_boroughs"]
    top, bottom = boroughs[0], boroughs[-1]
    return {
        "latest_year": latest,
        "ew_median": _gbp(ew["median_price"]),
        "london_median": _gbp(ldn["median_price"]),
        "rest_median": _gbp(rest["median_price"]),
        "london_ratio": round(ldn["median_price"] / rest["median_price"], 1),
        "transactions": f"{ew['transactions']:,}",
        "peak_year": peak["sale_year"],
        "vs_peak": round(ew["transactions"] / peak["transactions"] - 1, 3),
        "top_borough": top["borough"],
        "top_borough_median": _gbp(top["median_price"]),
        "bottom_borough": bottom["borough"],
        "bottom_borough_median": _gbp(bottom["median_price"]),
        "borough_gap": round(top["median_price"] / bottom["median_price"], 1),
    }


def build_site(output_dir: Path, out_dir: Path) -> Path:
    data = read_outputs(output_dir)
    payload = {"data": data, "headline": headline(data), "built_at": datetime.now(UTC).isoformat()}
    template = Template(files("ukhousing").joinpath("templates/dashboard.html").read_text())
    safe = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "index.html"
    target.write_text(template.render(payload_json=safe, h=payload["headline"]), encoding="utf-8")
    log.info("site written to %s", target)
    return target
