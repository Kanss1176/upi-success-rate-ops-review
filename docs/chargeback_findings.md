# Chargeback Monitor: Findings (Apr to Jul 2026)

**Data:** NPCI UPI Ecosystem Statistics, Chargeback tab, four monthly files (Apr, May, Jun, Jul 2026),
downloaded manually. Public aggregates by beneficiary-side entry (about 310 to 330 entries per month).
Raw files are not in this repository. This is an independent analysis, not affiliated with NPCI or PhonePe.

## What is NPCI data, what is assumption, what is derived
| Layer | Items |
|---|---|
| NPCI published | Total transactions, chargebacks received, chargebacks accepted, re-presentments raised, published chargeback ratio |
| Assumptions (this project's choices) | Minimum volume to rank an entry: 5 million transactions a month. Outlier cut-off: robust z-score above 3.5 (median and MAD of chargebacks per million transactions among ranked entries). "Persistent" means outlier in at least 3 of 4 months |
| Derived | Chargebacks per million transactions, acceptance rate, excess chargebacks (received minus what the peer-median rate implies for that volume), months flagged, longest streak |
| Conclusions | Listed below, each with its number and its caveat |

## Controls (all run on every month; nothing is silently corrected)
CB1 header layout, CB2 duplicate code, CB3 same name under two codes, CB4 missing or negative count,
CB5 accepted + re-presented = received, CB6 published ratio = received / transactions,
CB7 chargebacks above transactions, CB8 row-count swing above 15%, CB9 material entry missing versus prior month.
Row-level failures (CB2, CB4 to CB7) are excluded from rankings. Twelve tests, including a planted fault for every control, show each one catches what it is meant to catch.

**What the four months raised:** 9 logged exceptions (Deutsche Bank is caught by two controls).
- May: Deutsche Bank appears twice under code DEU (CB2, excluded); one row (AXIS BANK _ ABT, 2 transactions) shows more chargebacks than transactions (CB7, excluded).
- Jul: Ujjivan Small Finance Bank appears under two codes, UIJ and USN (CB3, logged, kept).
- May: ESAF Small Finance Bank (code EAF) is absent; Jun: code KMJ (Kotak Mahindra) is absent (CB9). Cause unknown: a rename or a code change is possible, and this has not been verified.
- Both header styles in the source files (Title Case and snake_case) are read correctly, and the per-row tie-outs (CB5, CB6) held on every other row of every month.

## Findings
1. **Volume grew about 6% and the chargeback rate stayed flat.** Transactions went from 22.6 billion (Apr) to 24.0 billion (Jul). Chargebacks per million transactions: 9.30, 8.05, 8.43, 8.33. April is the high month; the last three months sit in a narrow band.
2. **Acceptance of chargebacks edged down.** Share of received chargebacks accepted: 27.1%, 28.2%, 26.3%, 25.5%. Four points is too few to call a trend; it is worth watching, not acting on.
3. **A small group of entries is persistently bad.** 14 entries were outliers in at least three of the four months, six of them in all four (YES BANK MGS M, NSDL PAYMENTS BANK LIMITED _ NPD, SURYODAY SMALL FINANCE BANK, AXIS BANK _ ABR, JANA SMALL FINANCE BANK, RBL BANK). Together they handle **2.2% of transactions but hold 18.4% of chargebacks**: about 71 chargebacks per million transactions against 7.1 for everyone else.
4. **Large entries are not the problem.** The 26 entries above 100 million transactions run at 6.5 chargebacks per million; the 67 mid-size entries (5 to 100 million) run at 27.2. The five largest entries hold about 59% of volume but only about 38 to 41% of chargebacks.
5. **Persistence separates chronic from one-off.** A single-month view would flag 9 to 18 entries a month; only 14 stayed flagged in three or more months.

## What I would do with this
Escalate the six four-month outliers first, with the data pack: months flagged, rate against the peer median, excess chargebacks. Treat the three-month group as a watch list. Re-run each month and track whether the streaks continue.

## What this cannot tell you
- The chargeback table lists beneficiary-side entries. Some entries look like sub-units of a bank (for example "AXIS BANK SETU", "YES BANK MGS M"). What each one represents has not been verified, so no claim is made about the cause of a high rate.
- Chargebacks are disputes, not failed payments. This is a different measure from the technical-decline and business-decline rates, which come from the separate Top 50 Member Performance table.
- Aggregated monthly counts only: no transaction-level, merchant-level or value data, and no refund data.
- Four months is enough to separate persistent from one-off, but not to assess seasonality.
- The 5 million, 3.5 and "three of four months" thresholds are choices, not NPCI standards. Changing them changes which entries appear.
