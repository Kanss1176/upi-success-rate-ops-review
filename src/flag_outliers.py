"""Flag banks with unusually high technical declines (TD) for review."""
from pathlib import Path

import pandas as pd

IN = Path("data/processed/remitter_2026-08_clean.csv")
OUT = Path("data/processed/remitter_2026-08_flags.csv")
MIN_VOLUME_MN = 50       # keep mid-size banks in scope
TD_MULTIPLE = 3          # watch if TD is 3x the median
OUTLIER_TD_PCT = 1.0     # outlier if TD is at least 1% regardless of the median

df = pd.read_csv(IN)
df["td_txn_mn"] = (df.volume_mn * df.td_pct / 100).round(2)
df["exception"] = (df.approved_pct == 100) & (df.bd_pct == 0) & (df.td_pct == 0)

scope = df[(~df.exception) & (df.volume_mn >= MIN_VOLUME_MN)].copy()
bench = scope.td_pct.median()
scope["td_vs_median"] = (scope.td_pct / bench).round(1)
scope["td_flag"] = scope.td_pct >= TD_MULTIPLE * bench
scope["td_tier"] = scope.td_pct.apply(
    lambda x: "OUTLIER" if x >= OUTLIER_TD_PCT
    else ("WATCH" if x >= TD_MULTIPLE * bench else ""))

print(f"Banks in scope (volume >= {MIN_VOLUME_MN} Mn, exceptions removed): {len(scope)}")
print(f"Median TD %: {bench:.2f}   flag threshold: {TD_MULTIPLE * bench:.2f}%")
print(f"Total technical declines in scope: {scope.td_txn_mn.sum():.1f} Mn txns\n")

print("FLAGGED FOR REVIEW")
print(scope[scope.td_flag].sort_values("td_pct", ascending=False)
              [["rank", "bank", "volume_mn", "td_pct", "td_txn_mn", "td_tier"]]
      .to_string(index=False))

print("\nTOP 5 BY TECHNICAL-DECLINE VOLUME")
print(scope.sort_values("td_txn_mn", ascending=False).head(5)
      [["rank", "bank", "volume_mn", "td_pct", "td_txn_mn"]].to_string(index=False))

print("\nLOWEST APPROVAL, MAINLY CUSTOMER-SIDE (BD)")
print(scope.sort_values("approved_pct").head(5)
      [["bank", "approved_pct", "bd_pct", "td_pct"]].to_string(index=False))

df.merge(scope[["bank", "td_vs_median", "td_flag"]], on="bank", how="left") \
  .to_csv(OUT, index=False)
print(f"\nSaved to {OUT}")