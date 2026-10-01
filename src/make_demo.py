"""Create a small SYNTHETIC demo file with the same columns. Not NPCI data."""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
n = 20
vol = np.sort(rng.uniform(60, 3000, n))[::-1].round(2)
td = rng.choice([0.05, 0.1, 0.2, 0.4, 1.5], n, p=[.3, .3, .2, .1, .1])
bd = rng.uniform(5, 20, n).round(2)
df = pd.DataFrame({
    "rank": range(1, n + 1),
    "bank": [f"Synthetic Bank {i:02d}" for i in range(1, n + 1)],
    "volume_mn": vol,
    "approved_pct": (100 - bd - td).round(2),
    "bd_pct": bd,
    "td_pct": td,
})
df["reversal_count_mn"] = (df.volume_mn * rng.uniform(0.001, 0.004, n)).round(2)
df["reversal_success_pct"] = rng.uniform(60, 100, n).round(2)
df.to_csv("demo/synthetic_remitter_demo.csv", index=False)
print("Saved demo/synthetic_remitter_demo.csv (synthetic, for demonstration only)")