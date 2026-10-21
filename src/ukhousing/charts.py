"""Static PNG charts for the README and the report, made from the CSV results."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FuncFormatter, PercentFormatter  # noqa: E402

INK, MUTED, LINE = "#13212F", "#5B6878", "#E3E7ED"
LONDON, REST, ACCENT = "#D9480F", "#3B6E8F", "#0F766E"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.edgecolor": LINE,
        "axes.labelcolor": MUTED,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": LINE,
        "axes.titleweight": "bold",
        "axes.titlesize": 14,
        "axes.titlecolor": INK,
        "axes.titlelocation": "left",
    }
)
gbp_k = FuncFormatter(lambda v, _: f"£{v / 1000:.0f}k")


def _save(fig, path: Path) -> Path:
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def price_trend(results: Path, out: Path) -> Path:
    df = pd.read_csv(results / "yearly_summary.csv")
    df = df[df["is_complete_year"]]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    for area, colour in (("London", LONDON), ("Outside London", REST)):
        d = df[df["area"] == area]
        ax.plot(d["sale_year"], d["median_price"], marker="o", lw=2.6, color=colour, label=area)
    ax.yaxis.set_major_formatter(gbp_k)
    ax.set_ylim(0, None)
    ax.set_title("Median sale price: London has stalled since 2022")
    ax.legend(frameon=False)
    return _save(fig, out / "price-trend.png")


def monthly_volume(results: Path, out: Path) -> Path:
    df = pd.read_csv(results / "monthly_activity.csv", parse_dates=["sale_month"])
    df = df[df["area"] == "England and Wales"]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.bar(df["sale_month"], df["transactions"], width=25, color=REST)
    for when, label in (
        ("2021-06-01", "Stamp duty\nrelief cut"),
        ("2025-03-01", "Before stamp\nduty rise"),
    ):
        row = df[df["sale_month"] == when]
        if not row.empty:
            ax.annotate(
                label,
                (row["sale_month"].iloc[0], row["transactions"].iloc[0]),
                xytext=(8, -4),
                textcoords="offset points",
                fontsize=9,
                color=MUTED,
                va="top",
            )
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v / 1000:.0f}k"))
    ax.set_title("Monthly sales in England and Wales follow tax deadlines")
    ax.grid(axis="x", visible=False)
    return _save(fig, out / "monthly-sales.png")


def borough_change(results: Path, out: Path) -> Path:
    df = pd.read_csv(results / "london_boroughs.csv").sort_values("change_5y")
    colours = [LONDON if v < 0 else ACCENT for v in df["change_5y"]]
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.barh(df["borough"], df["change_5y"], color=colours)
    ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    year = int(df["latest_year"].iloc[0])
    ax.set_title(f"London boroughs: change in median price, {year - 5} to {year}")
    ax.grid(axis="y", visible=False)
    ax.axvline(0, color=INK, lw=0.8)
    return _save(fig, out / "borough-change.png")


def flats_vs_growth(results: Path, out: Path) -> Path:
    df = pd.read_csv(results / "london_boroughs.csv")
    fig, ax = plt.subplots(figsize=(8, 5.4))
    ax.scatter(
        df["flat_share"], df["change_5y"], s=df["transactions"] / 25, color=ACCENT, alpha=0.75
    )
    for _, r in df.iterrows():
        if r["change_5y"] < -0.06 or r["change_5y"] > 0.16:
            ax.annotate(
                r["borough"],
                (r["flat_share"], r["change_5y"]),
                xytext=(5, -12 if r["borough"] == "Hillingdon" else 3),
                textcoords="offset points",
                fontsize=8.5,
                color=MUTED,
            )
    ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xlabel("Share of sales that are flats")
    ax.set_ylabel("Five-year change in median price")
    ax.set_title("The more flats a borough sells, the weaker its prices")
    return _save(fig, out / "flats-vs-growth.png")


def make_all(results: Path, out: Path) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    return [f(results, out) for f in (price_trend, monthly_volume, borough_change, flats_vs_growth)]
