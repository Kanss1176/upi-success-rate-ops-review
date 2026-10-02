"""Fault-injection tests: each control must catch the fault planted for it,
and a clean table must raise nothing."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import chargeback as cb  # noqa: E402


def clean(n=6, month="2026-07"):
    rows = []
    for i in range(n):
        txns = 50_000_000 - i * 1_000_000
        recv = 400 + i * 10
        acc = recv // 4
        rows.append(dict(srno=i + 1, code=f"B{i:02d}", bank=f"Bank {i}", txns=txns,
                         cb_ratio_pct=recv / txns * 100, cb_received=recv,
                         cb_accepted=acc, represented=recv - acc))
    df = pd.DataFrame(rows)
    df["month"] = month
    df["bank_norm"] = df["bank"].map(cb.norm_name)
    return df


def controls(df, header_ok=True, prev=None):
    exc, excl = cb.run_controls(df, header_ok, prev)
    return set(exc["control"]), excl


def test_clean_table_raises_nothing():
    found, excl = controls(clean())
    assert found == set() and excl == set()


def test_duplicate_code_caught_and_excluded():
    df = clean()
    df.loc[3, "code"] = df.loc[2, "code"]
    found, excl = controls(df)
    assert "CB2" in found and {2, 3} <= excl


def test_same_name_two_codes_logged_not_excluded():
    df = clean()
    df.loc[3, "bank_norm"] = df.loc[2, "bank_norm"]
    found, excl = controls(df)
    assert "CB3" in found and excl == set()


def test_negative_or_missing_count_caught():
    df = clean()
    df.loc[1, "cb_received"] = -5
    df.loc[4, "txns"] = None
    found, excl = controls(df)
    assert "CB4" in found and {1, 4} <= excl


def test_split_mismatch_caught():
    df = clean()
    df.loc[2, "represented"] += 7
    found, excl = controls(df)
    assert "CB5" in found and 2 in excl


def test_ratio_mismatch_caught():
    df = clean()
    df.loc[0, "cb_ratio_pct"] = 0.5
    found, excl = controls(df)
    assert "CB6" in found and 0 in excl


def test_chargebacks_above_transactions_caught():
    df = clean()
    df.loc[5, "txns"] = 3
    df.loc[5, "cb_received"] = 10
    df.loc[5, "cb_accepted"] = 4
    df.loc[5, "represented"] = 6
    df.loc[5, "cb_ratio_pct"] = 10 / 3 * 100
    found, _ = controls(df)
    assert "CB7" in found


def test_bad_header_caught():
    found, _ = controls(clean(), header_ok=False)
    assert "CB1" in found


def test_row_count_swing_and_vanished_bank_caught():
    prev = clean(10, "2026-06")
    cur = clean(6, "2026-07")
    exc, _ = cb.run_controls(cur, True, prev)
    assert {"CB8", "CB9"} <= set(exc["control"])


def test_header_styles_both_accepted():
    a = ["SrNo", "Code", "Beneficiary Bank", "Total Txns during the month", "CB Ratio",
         "Chargebacks Received during the month", "Chargebacks Accepted during the month",
         "Re-presentment Raised during the month"]
    b = ["SrNo", "Code", "Beneficiary Bank", "total_txns_during_the_month", "cb_ratio",
         "chargebacks_received_during_the_month", "chargebacks_accepted_during_the_month",
         "representment_raised_during_the_month"]
    assert [cb.norm_header(x) for x in a] == cb.EXPECTED == [cb.norm_header(x) for x in b]


def test_small_banks_listed_but_not_ranked():
    df = clean()
    df.loc[5, "txns"] = 1000
    df.loc[5, "cb_received"], df.loc[5, "cb_accepted"], df.loc[5, "represented"] = 10, 2, 8
    df.loc[5, "cb_ratio_pct"] = 1.0
    m = cb.month_metrics(df, set())
    assert not m.loc[5, "ranked"] and not m.loc[5, "outlier"]


def test_persistent_outlier_streak():
    frames = []
    for mo, hot in (("2026-04", True), ("2026-05", True), ("2026-06", False), ("2026-07", True)):
        df = clean(30, mo)
        if hot:
            df.loc[0, "cb_received"] = 40_000
            df.loc[0, "cb_accepted"] = 10_000
            df.loc[0, "represented"] = 30_000
        frames.append(cb.month_metrics(df, set()))
    p = cb.persistence(pd.concat(frames)).set_index("code")
    assert p.loc["B00", "months_outlier"] == 3 and p.loc["B00", "longest_streak"] == 2
