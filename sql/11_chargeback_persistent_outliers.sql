-- Banks flagged as outliers in at least three months, with their excess chargebacks.
-- Excess = chargebacks above what the peer-median rate would imply for the bank's volume.
WITH p AS (
  SELECT *, ROUND(100.0 * excess_chargebacks / SUM(excess_chargebacks) OVER (), 1) AS pct_of_all_excess
  FROM read_csv('data/processed/chargeback_persistence.csv', header = true)
)
SELECT code, bank, months_ranked, months_outlier, longest_streak,
       avg_per_million, excess_chargebacks, pct_of_all_excess
FROM p
WHERE months_outlier >= 3
ORDER BY excess_chargebacks DESC;
