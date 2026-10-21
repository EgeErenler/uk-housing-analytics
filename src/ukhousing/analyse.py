"""Run every SQL file in order, then export the `out_*` tables as CSV."""

from __future__ import annotations

import logging
from pathlib import Path

import duckdb

log = logging.getLogger(__name__)


def run_sql(con: duckdb.DuckDBPyConnection, sql_dir: Path) -> list[str]:
    files = sorted(sql_dir.glob("*.sql"))
    if not files:
        raise FileNotFoundError(f"No SQL files in {sql_dir.resolve()}. Run from the repo root.")
    for path in files:
        log.info("running %s", path.name)
        con.execute(path.read_text())
    return [p.name for p in files]


def output_tables(con: duckdb.DuckDBPyConnection) -> list[str]:
    rows = con.execute(
        "select table_name from information_schema.tables "
        "where table_name like 'out_%' order by table_name"
    ).fetchall()
    return [r[0] for r in rows]


def export(con: duckdb.DuckDBPyConnection, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for table in output_tables(con):
        target = output_dir / f"{table.removeprefix('out_')}.csv"
        con.execute(f"copy {table} to '{target.as_posix()}' (header, delimiter ',')")
        written.append(target)
    log.info("exported %d tables to %s", len(written), output_dir)
    return written


def analyse(db_path: Path, sql_dir: Path, output_dir: Path) -> list[Path]:
    con = duckdb.connect(str(db_path))
    try:
        run_sql(con, sql_dir)
        return export(con, output_dir)
    finally:
        con.close()
