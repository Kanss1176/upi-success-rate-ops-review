"""Chargeback monitor: load monthly NPCI UPI chargeback tables, run data-quality
controls, and compute dispute-rate metrics with persistence across months.

Input : data/raw/Ecosystem-Statistics-UPI-Chargeback-<YYY>-<Mon>.xlsx (downloaded by hand)
Output: data/processed/chargeback_{monthly,banks,exceptions,persistence}.csv

Nothing is silently corrected: failures are logged to the exceptions table and
row-level failures are excluded from rankings.
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path("data/raw")
OUT = Path("data/processed")
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}

MIN_VOLUME = 5_000_000      # assumption: banks below this monthly volume are listed, not ranked
Z_CUTOFF = 3.5              # assumption: robust z-score above this = outlier
ROW_SWING = 0.15            # assumption: row count moving >15% month on month is flagged
RATIO_TOL = 0.0006          # percentage points; NPCI publishes the ratio rounded to 3 decimals

EXPECTED = ["srno", "code", "beneficiarybank", "totaltxnsduringthemonth", "cbratio",
            "chargebacksreceivedduringthemonth", "chargebacksacceptedduringthemonth",
            "representmentraisedduringthemonth"]
COLS = ["srno", "code", "bank", "txns", "cb_ratio_pct", "cb_received", "cb_accepted", "represented"]


def norm_header(h):
    return re.sub(r"[^a-z0-9]", "", str(h).lower())


def norm_name(s):
    return re.sub(r"\s+", " ", str(s).upper()).strip()


def month_from_name(path):
    m = re.search(r"-(\d{4})-([A-Za-z]{3})", Path(path).name)
    if not m or m.group(2).lower() not in MONTHS:
        raise ValueError(f"cannot read month from file name: {path}")
    return f"{m.group(1)}-{MONTHS[m.group(2).lower()]:02d}"


def load_month(path):
    """Read one file. Returns (clean dataframe, header_ok)."""
    raw = pd.read_excel(path)
    header_ok = [norm_header(c) for c in raw.columns] == EXPECTED
    df = raw.iloc[:, :8].copy()
    df.columns = COLS
    df["month"] = month_from_name(path)
    df["code"] = df["code"].astype(str).str.strip().str.upper()
    df["bank_norm"] = df["bank"].map(norm_name)
    df["cb_ratio_pct"] = pd.to_numeric(df["cb_ratio_pct"].astype(str).str.rstrip("%"), errors="coerce")
    for c in ("txns", "cb_received", "cb_accepted", "represented"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df, header_ok


def run_controls(df, header_ok, prev=None):
    """Return (exceptions dataframe, set of row labels to exclude from rankings)."""
    month = df["month"].iloc[0]
    exc, exclude = [], set()

    def log(cid, rows, detail, drop=False):
        for i in rows:
            r = df.loc[i]
            exc.append(dict(month=month, control=cid, code=r["code"], bank=r["bank"], detail=detail))
            if drop:
                exclude.add(i)

    if not header_ok:
        exc.append(dict(month=month, control="CB1", code="", bank="", detail="header does not match expected 8 columns"))
    log("CB2", df.index[df.duplicated("code", keep=False)], "duplicate bank code in month", drop=True)
    log("CB3", df.index[df.duplicated("bank_norm", keep=False)], "same bank name under more than one code")
    bad = df[["txns", "cb_received", "cb_accepted", "represented"]].isna().any(axis=1) | (df["txns"] <= 0) \
        | (df[["cb_received", "cb_accepted", "represented"]] < 0).any(axis=1)
    log("CB4", df.index[bad], "missing, zero or negative count", drop=True)
    ok = ~bad
    split = ok & ((df["cb_accepted"] + df["represented"]) != df["cb_received"])
    log("CB5", df.index[split], "accepted + re-presented does not equal received", drop=True)
    calc = df["cb_received"] / df["txns"] * 100
    log("CB6", df.index[ok & ((calc - df["cb_ratio_pct"]).abs() > RATIO_TOL)], "published ratio differs from received/txns", drop=True)
    log("CB7", df.index[ok & (df["cb_received"] > df["txns"])], "chargebacks exceed transactions", drop=True)
    if prev is not None:
        swing = abs(len(df) - len(prev)) / len(prev)
        if swing > ROW_SWING:
            exc.append(dict(month=month, control="CB8", code="", bank="",
                            detail=f"row count {len(prev)} -> {len(df)} ({swing:.0%} change)"))
        gone = prev[(prev["txns"] >= MIN_VOLUME) & ~prev["code"].isin(df["code"])]
        for _, r in gone.iterrows():
            exc.append(dict(month=month, control="CB9", code=r["code"], bank=r["bank"],
                            detail="material bank in prior month is absent this month"))
    return pd.DataFrame(exc, columns=["month", "control", "code", "bank", "detail"]), exclude


def month_metrics(df, exclude):
    d = df.drop(index=list(exclude)).copy()
    d["per_million"] = d["cb_received"] / d["txns"] * 1e6
    d["accept_rate"] = np.where(d["cb_received"] > 0, d["cb_accepted"] / d["cb_received"], np.nan)
    d["ranked"] = d["txns"] >= MIN_VOLUME
    r = d[d["ranked"]]
    med = r["per_million"].median()
    mad = (r["per_million"] - med).abs().median()
    d["peer_median"] = med
    d["robust_z"] = np.where(d["ranked"] & (mad > 0), 0.6745 * (d["per_million"] - med) / mad, np.nan)
    d["outlier"] = d["robust_z"] > Z_CUTOFF
    d["excess_cb"] = np.where(d["ranked"], (d["cb_received"] - med * d["txns"] / 1e6).clip(lower=0), 0.0)
    return d


def persistence(banks):
    r = banks[banks["ranked"]].copy()
    months = sorted(banks["month"].unique())
    flag = r.pivot_table(index="code", columns="month", values="outlier", aggfunc="max").reindex(columns=months).fillna(False)

    def longest(row):
        best = cur = 0
        for v in row:
            cur = cur + 1 if v else 0
            best = max(best, cur)
        return best

    p = pd.DataFrame({"months_ranked": r.groupby("code")["month"].nunique(),
                      "months_outlier": flag.sum(axis=1).astype(int),
                      "longest_streak": flag.apply(longest, axis=1).astype(int)})
    names = r.sort_values("month").groupby("code")["bank_norm"].last()
    ex = r.groupby("code")["excess_cb"].sum()
    p["bank"] = names
    p["excess_chargebacks"] = ex.round(0)
    p["avg_per_million"] = r.groupby("code")["per_million"].mean().round(1)
    return p.sort_values(["months_outlier", "excess_chargebacks"], ascending=False).reset_index()


def main(raw=RAW, out=OUT):
    out.mkdir(parents=True, exist_ok=True)
    files = sorted(raw.glob("Ecosystem-Statistics-UPI-Chargeback-*.xlsx"), key=month_from_name)
    if not files:
        sys.exit(f"no chargeback files in {raw}")
    seen = [month_from_name(f) for f in files]
    if len(set(seen)) != len(seen):
        sys.exit(f"two files for the same month: {seen}")
    banks, excs, prev = [], [], None
    for f in files:
        df, hdr = load_month(f)
        e, ex = run_controls(df, hdr, prev)
        excs.append(e)
        banks.append(month_metrics(df, ex))
        prev = df
    banks = pd.concat(banks, ignore_index=True)
    exc = pd.concat(excs, ignore_index=True)
    ranked = banks[banks["ranked"]]
    monthly = banks.groupby("month").agg(banks=("code", "nunique"), txns=("txns", "sum"),
                                         cb_received=("cb_received", "sum"), cb_accepted=("cb_accepted", "sum")).reset_index()
    monthly["per_million"] = (monthly["cb_received"] / monthly["txns"] * 1e6).round(2)
    monthly["accept_rate"] = (monthly["cb_accepted"] / monthly["cb_received"]).round(4)
    monthly["outliers"] = ranked.groupby("month")["outlier"].sum().reindex(monthly["month"]).values
    pers = persistence(banks)
    banks.to_csv(out / "chargeback_banks.csv", index=False)
    exc.to_csv(out / "chargeback_exceptions.csv", index=False)
    monthly.to_csv(out / "chargeback_monthly.csv", index=False)
    pers.to_csv(out / "chargeback_persistence.csv", index=False)
    print(f"Loaded {len(files)} months: {', '.join(seen)}")
    print("\nMonthly summary:\n", monthly.to_string(index=False))
    print("\nControl exceptions by control:\n", exc.groupby("control").size().to_string() if len(exc) else "none")
    print("\nPersistent outliers (top 10):\n", pers.head(10).to_string(index=False))
    return banks, exc, monthly, pers


if __name__ == "__main__":
    if "--demo" in sys.argv:  # synthetic files in demo/chargeback, for running without NPCI data
        main(Path("demo/chargeback"), OUT)
    else:
        main()
