# UPI Success Rate Operations Review

Bank-wise data-quality controls and monitoring on public NPCI UPI statistics. Two modules:
a remitter success-rate monitor (technical vs business declines) and a chargeback monitor.


## Module 1: Remitter success-rate monitor (single-month snapshot)
- Loads the NPCI Top 50 remitter file (downloaded manually) and runs seven controls: period label, row count, rank integrity, duplicate names, sort order, Approved + BD + TD within rounding of 100, missing values.
- Logs exceptions (banks showing 100% approved with zero declines) and excludes them from rankings.
- Flags banks by technical-decline (TD) rate: OUTLIER at 1% or more, WATCH at 3x the median. These cut-offs are my assumptions, not NPCI standards.
- Separates customer-side declines (BD) from technical declines (TD), using NPCI's glossary definitions.

**Findings (Aug 2026 selector):**
- The file title reads Jul'26 although it was downloaded under the Aug 2026 selector. This is logged as a control exception (C1), not corrected.
- Five banks are OUTLIERs on TD: Baroda U.P. Bank, Central Bank of India, Punjab & Sind Bank, Rajasthan Marudhara Gramin Bank and NSDL Payments Bank.
- Central Bank of India has the largest technical-decline volume of the banks in scope.
- The lowest approval rates are mostly customer-side declines (BD), not technical faults.

## Module 2: Chargeback monitor (Apr to Jul 2026)
Four monthly NPCI chargeback tables (Statistics, Ecosystem Statistics, Chargeback tab), downloaded manually.
Chargebacks are disputes, not failed payments, so this is a separate measure from the TD/BD view above.

- **Controls (CB1 to CB9):** header layout, duplicate codes, one name under two codes, missing or negative counts, accepted + re-presented = received, published ratio = received / transactions, chargebacks above transactions, row-count swing, and material entries missing versus the prior month. 12 tests cover them.
- **Result:** transactions grew about 6% (22.6 to 24.0 billion) while chargebacks per million fell from 9.3 to 8.3 (April to July). 14 entries were outliers in at least 3 of 4 months; together they carry 2.2% of transactions and 18.4% of chargebacks (about 71 per million against 7.1 for the rest).
- **Thresholds are my assumptions:** minimum 5 million transactions to rank, robust z-score above 3.5, "persistent" = 3 of 4 months.
- Full write-up: [`docs/chargeback_findings.md`](docs/chargeback_findings.md)

## Data
Public NPCI statistics (Statistics, then Ecosystem Statistics), downloaded manually. Raw files are not included. `demo/synthetic_remitter_demo.csv` and `demo/chargeback/` are synthetic and for demonstration only.

## Run
    pip install pandas openpyxl numpy duckdb pytest
    python src/load_remitter.py
    python src/flag_outliers.py
    python src/chargeback.py
    python src/run_sql.py
    python -m pytest -q tests
    python src/chargeback.py --demo   (synthetic files, no NPCI data needed)

## Disclaimer
Public NPCI statistics, downloaded manually. Accuracy depends on the source. Not financial advice. Independent analysis, not affiliated with NPCI or PhonePe.

## Limitations
- Module 1 covers one month only (Aug 2026 selector); Module 2 covers four months (Apr to Jul 2026).
- Top 50 banks only, so totals do not tie to national volumes.
- Reversal-success rates sit on small counts and are not used for ranking.
- The remitter download omits the UDIR columns shown on the web page.
- The loader and flag scripts read the real NPCI file, which is not in this repo; the demo file shows the expected columns.
- The chargeback table lists beneficiary-side entries, and what each entry represents has not been verified.