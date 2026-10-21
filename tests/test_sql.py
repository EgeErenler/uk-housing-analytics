"""Test the SQL logic on small, hand-made data where the right answer is known."""

from __future__ import annotations

import duckdb
import pytest

from ukhousing.analyse import export, run_sql
from ukhousing.config import PPD_COLUMNS, SQL_DIR


def make_db(rows: list[tuple]) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    cols = ", ".join(f"{name} {dtype}" for name, dtype in PPD_COLUMNS.items())
    con.execute(f"create table ppd ({cols})")
    con.executemany(f"insert into ppd values ({', '.join(['?'] * len(PPD_COLUMNS))})", rows)
    return con


def sale(
    tid,
    price,
    when,
    postcode="E8 1AA",
    ptype="T",
    paon="10",
    district="HACKNEY",
    county="GREATER LONDON",
    category="A",
    status="A",
    new="N",
    duration="F",
):
    return (
        tid,
        price,
        f"{when} 00:00",
        postcode,
        ptype,
        new,
        duration,
        paon,
        None,
        "MARE STREET",
        None,
        "LONDON",
        district,
        county,
        category,
        status,
    )


def full_year(year: int, district="HACKNEY", county="GREATER LONDON", price=500_000, start=0):
    """One sale in every month, so the year counts as complete."""
    return [
        sale(
            f"{district}-{year}-{m}",
            price,
            f"{year}-{m:02d}-15",
            paon=str(start + m),
            district=district,
            county=county,
        )
        for m in range(1, 13)
    ]


@pytest.fixture
def con():
    rows = (
        full_year(2019)
        + full_year(2024, price=600_000)
        + full_year(2019, district="CAMDEN", price=800_000, start=100)
        + full_year(2024, district="CAMDEN", price=880_000, start=100)
        + full_year(2024, district="LEEDS", county="WEST YORKSHIRE", price=200_000, start=200)
        + [
            # The same home sold twice, exactly two years apart: 400k -> 484k is +10% a year.
            sale("r1", 400_000, "2021-03-01", postcode="E8 9ZZ", paon="7"),
            sale("r2", 484_000, "2023-03-01", postcode="E8 9ZZ", paon="7"),
            # Rows the cleaning rules must remove.
            sale("b1", 9_000_000, "2024-05-01", category="B"),
            sale("o1", 1_000_000, "2024-05-01", ptype="O"),
            sale("d1", 1_000_000, "2024-05-01", status="D"),
        ]
    )
    con = make_db(rows)
    run_sql(con, SQL_DIR)
    yield con
    con.close()


def scalar(con, sql):
    return con.execute(sql).fetchone()[0]


def test_cleaning_rules_remove_b_other_and_deleted(con):
    assert scalar(con, "select count(*) from sales where transaction_id in ('b1','o1','d1')") == 0
    assert scalar(con, "select count(*) from sales") == 12 * 5 + 2


def test_title_case_keeps_joining_words_lower(con):
    assert scalar(con, "select title_case('KENSINGTON AND CHELSEA')") == "Kensington and Chelsea"
    assert scalar(con, "select title_case('  CITY OF LONDON ')") == "City of London"


def test_incomplete_years_are_flagged(con):
    complete = {r[0] for r in con.execute("select sale_year from complete_years").fetchall()}
    assert complete == {2019, 2024}  # 2021 and 2023 only have one sale each


def test_repeat_sale_annual_return(con):
    row = con.execute(
        "select years_held, annual_return from repeat_sale_pairs where price = 484000"
    ).fetchone()
    assert row[0] == pytest.approx(2.0, abs=0.01)
    assert row[1] == pytest.approx(0.10, abs=0.001)


def test_borough_league_table(con):
    rows = con.execute(
        "select borough, median_price, change_5y, price_rank, growth_rank "
        "from out_london_boroughs order by price_rank"
    ).fetchall()
    assert [r[0] for r in rows] == ["Camden", "Hackney"]
    camden, hackney = rows
    assert camden[2] == pytest.approx(0.10)  # 800k -> 880k
    assert hackney[2] == pytest.approx(0.20)  # 500k -> 600k
    assert hackney[4] == 1 and camden[4] == 2  # Hackney grew faster


def test_yearly_summary_yoy_uses_previous_row(con):
    yoy = scalar(
        con,
        "select median_price_yoy from out_yearly_summary "
        "where area = 'Outside London' and sale_year = 2024",
    )
    assert yoy is None  # no earlier year outside London in this data


def test_export_writes_every_output(con, tmp_path):
    written = {p.name for p in export(con, tmp_path)}
    assert {"yearly_summary.csv", "london_boroughs.csv", "repeat_sales_summary.csv"} <= written
