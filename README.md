# UPI Success Rate Operations Review

Bank-wise data-quality controls and technical-decline monitoring on public NPCI UPI remitter statistics.

## What it does
- Loads the NPCI Top 50 remitter file (downloaded manually) and runs seven controls: period label, row count, rank integrity, duplicate names, sort order, Approved + BD + TD within rounding of 100, missing values.
- Logs exceptions (banks showing 100% approved with zero declines) and excludes them from rankings.
- Flags banks by technical-decline (TD) rate: OUTLIER at 1% or more, WATCH at 3x the median.
- Separates customer-side declines (BD) from technical declines (TD), using NPCI's glossary definitions.

## Findings (one month, Aug 2026 selector)
- The file title reads Jul'26 although it was downloaded under the Aug 2026 selector. This is logged as a control exception (C1), not corrected.
- Five banks are OUTLIERs on TD: Baroda U.P. Bank, Central Bank of India, Punjab & Sind Bank, Rajasthan Marudhara Gramin Bank and NSDL Payments Bank.
- Central Bank of India has the largest technical-decline volume of the banks in scope.
- The lowest approval rates are mostly customer-side declines (BD), not technical faults.

## Data
Public NPCI statistics (Statistics, then Ecosystem Statistics, Top 50 Member Performance), downloaded manually. Raw files are not included. `demo/synthetic_remitter_demo.csv` is synthetic and for demonstration only.

## Run
    pip install pandas openpyxl numpy
    python src/load_remitter.py
    python src/flag_outliers.py

## Disclaimer
Public NPCI statistics, downloaded manually. Accuracy depends on the source. Not financial advice. Independent analysis, not affiliated with NPCI or PhonePe.

## Limitations
One month only. Top 50 banks, so totals do not tie to national volumes. Reversal-success rates sit on small counts and are not used for ranking. The download omits the UDIR columns shown on the web page. The loader and flag scripts read the real NPCI file, which is not in this repo; the demo file shows the expected columns.