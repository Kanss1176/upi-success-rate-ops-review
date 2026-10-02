"""Run every query in sql/ against data/processed/ and save results to docs/sql_results/."""
from pathlib import Path

import duckdb

OUT = Path("docs/sql_results")
OUT.mkdir(parents=True, exist_ok=True)
con = duckdb.connect()
for f in sorted(Path("sql").glob("*.sql")):
    try:
        df = con.execute(f.read_text(encoding="utf-8")).df()
    except Exception as e:  # a query whose input file is not built yet should not stop the rest
        print(f"\n=== {f.name}: skipped ({str(e).splitlines()[0]})")
        continue
    df.to_csv(OUT / f"{f.stem}.csv", index=False)
    print(f"\n=== {f.name} ({len(df)} rows) ===")
    print(df.to_string(index=False))
