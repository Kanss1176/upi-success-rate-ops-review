"""Load and validate the NPCI Top 50 remitter file (manual download)."""
import re
from pathlib import Path

import pandas as pd

RAW = Path("data/raw/remitter_2026-08.xlsx")
OUT = Path("data/processed/remitter_2026-08_clean.csv")
EXPECTED_PERIOD = "2026-08"
TOL = 0.05  # rounding tolerance, percentage points
MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}

COLS = {
    "Sr. No.": "rank",
    "UPI Remitter Banks": "bank",
    "Total Volume (In Mn)": "volume_mn",
    "Approved %": "approved_pct",
    "BD %": "bd_pct",
    "TD%": "td_pct",
    "Total Debit Reversal Count (In Mn)": "reversal_count_mn",
    "Debit Reversal Success %": "reversal_success_pct",
}


def pct(s):
    return pd.to_numeric(s.astype(str).str.replace("%", "").str.strip(),
                         errors="coerce")


title = str(pd.read_excel(RAW, header=None, nrows=1).iloc[0, 0])
m = re.search(r"\((\w{3})'(\d{2})\)", title)
file_period = f"20{m.group(2)}-{MONTHS[m.group(1)]:02d}" if m else "unknown"

df = pd.read_excel(RAW, header=1)
df.columns = [str(c).strip() for c in df.columns]
missing = [c for c in COLS if c not in df.columns]
if missing:
    raise SystemExit(f"Unexpected columns. Missing {missing}. Found {list(df.columns)}")
df = df.rename(columns=COLS)[list(COLS.values())]
df = df[pd.to_numeric(df["rank"], errors="coerce").notna()].copy()
df["rank"] = df["rank"].astype(int)
df["bank"] = df["bank"].astype(str).str.strip()
for c in ["approved_pct", "bd_pct", "td_pct", "reversal_success_pct"]:
    df[c] = pct(df[c])
for c in ["volume_mn", "reversal_count_mn"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

df["pct_total"] = (df.approved_pct + df.bd_pct + df.td_pct).round(2)
df["sum_ok"] = (df.pct_total - 100).abs() <= TOL

print(f"Title: {title}")
print("CONTROL RESULTS")
print(f" C1 period label matches {EXPECTED_PERIOD}: "
      f"{'PASS' if file_period == EXPECTED_PERIOD else 'FAIL'} (file says {file_period})")
print(f" C2 row count is 50: {'PASS' if len(df) == 50 else 'FAIL'} ({len(df)})")
print(f" C3 ranks 1..50 unique: "
      f"{'PASS' if sorted(df['rank']) == list(range(1, 51)) else 'FAIL'}")
print(f" C4 no duplicate bank names: "
      f"{'PASS' if not df.bank.duplicated().any() else 'FAIL'}")
print(f" C5 volume sorted high to low: "
      f"{'PASS' if df.volume_mn.is_monotonic_decreasing else 'FAIL'}")
print(f" C6 approved+BD+TD within +/-{TOL} of 100: "
      f"{int(df.sum_ok.sum())}/{len(df)} pass")
print(f" C7 missing values in core columns: "
      f"{int(df[['volume_mn','approved_pct','bd_pct','td_pct']].isna().sum().sum())}")

bad = df[~df.sum_ok]
if len(bad):
    print("\nC6 failures:")
    print(bad[["rank", "bank", "approved_pct", "bd_pct", "td_pct", "pct_total"]]
          .to_string(index=False))
odd = df[(df.approved_pct == 100) & (df.bd_pct == 0) & (df.td_pct == 0)]
if len(odd):
    print("\nException log (100% approved, zero declines):")
    print(odd[["rank", "bank", "volume_mn"]].to_string(index=False))

OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)
print(f"\nSaved {len(df)} rows to {OUT}")