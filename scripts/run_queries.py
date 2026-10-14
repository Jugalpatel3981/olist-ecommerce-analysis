"""Run every SQL file in sql/ against the DuckDB database and save results as CSV.

Usage:
    python scripts/run_queries.py            # run all queries
    python scripts/run_queries.py 07 13      # run only queries whose file starts with 07 / 13
"""
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"
OUT_DIR = SQL_DIR / "results"
DB_PATH = ROOT / "data" / "olist.duckdb"


def main(prefixes: list[str]) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    con = duckdb.connect(str(DB_PATH), read_only=True)
    for path in sorted(SQL_DIR.glob("*.sql")):
        if prefixes and not any(path.name.startswith(p) for p in prefixes):
            continue
        df = con.execute(path.read_text()).df()
        df.to_csv(OUT_DIR / f"{path.stem}.csv", index=False)
        print(f"\n=== {path.name} ({len(df)} rows) ===")
        print(df.head(25).to_string(index=False))
    con.close()


if __name__ == "__main__":
    main(sys.argv[1:])
