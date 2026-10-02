"""Write SYNTHETIC chargeback files in the NPCI layout so the repo runs without
NPCI data. Every number here is invented (seeded). Not NPCI data."""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path("demo/chargeback")
HDR = ["SrNo", "Code", "Beneficiary Bank", "Total Txns during the month", "CB Ratio",
       "Chargebacks Received during the month", "Chargebacks Accepted during the month",
       "Re-presentment Raised during the month"]
MONTHS = [("2026-Apr", 0), ("2026-May", 1), ("2026-Jun", 2), ("2026-Jul", 3)]


def build(seed=42, n=80):
    rng = np.random.default_rng(seed)
    vol = np.sort(rng.lognormal(17, 1.6, n))[::-1]
    base = rng.lognormal(np.log(8e-6), 0.5, n)
    base[[5, 17, 31]] *= 12  # three synthetic persistently high banks
    for name, k in MONTHS:
        txns = (vol * rng.uniform(0.95, 1.05, n)).astype(np.int64) + 1
        recv = rng.poisson(txns * base * rng.uniform(0.8, 1.2, n)).astype(np.int64)
        acc = rng.binomial(recv, 0.27)
        df = pd.DataFrame({"SrNo": range(1, n + 1), "Code": [f"S{i:03d}" for i in range(n)],
                           "Beneficiary Bank": [f"DEMO BANK {i:03d}" for i in range(n)],
                           "Total Txns during the month": txns,
                           "CB Ratio": [f"{r / t * 100:.3f}%" for r, t in zip(recv, txns)],
                           "Chargebacks Received during the month": recv,
                           "Chargebacks Accepted during the month": acc,
                           "Re-presentment Raised during the month": recv - acc})
        df.columns = HDR
        if k == 1:  # planted faults so the controls have something to find
            df.loc[10, "Code"] = df.loc[9, "Code"]
            df.loc[20, "Re-presentment Raised during the month"] += 5
        OUT.mkdir(parents=True, exist_ok=True)
        df.to_excel(OUT / f"Ecosystem-Statistics-UPI-Chargeback-{name}.xlsx", index=False)
    print(f"wrote 4 synthetic files to {OUT}")


if __name__ == "__main__":
    build()
