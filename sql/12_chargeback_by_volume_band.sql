-- Dispute rate and acceptance rate by bank size band (conditional aggregation)
WITH b AS (
  SELECT *,
         CASE WHEN txns >= 100000000 THEN '1_large (100M+)'
              WHEN txns >= 5000000   THEN '2_mid (5M-100M)'
              ELSE '3_small (<5M, not ranked)' END AS band
  FROM read_csv('data/processed/chargeback_banks.csv', header = true)
)
SELECT band,
       COUNT(DISTINCT code) AS banks,
       SUM(txns) AS txns,
       SUM(cb_received) AS cb_received,
       ROUND(SUM(cb_received) * 1e6 / SUM(txns), 2) AS per_million,
       ROUND(SUM(cb_accepted) * 1.0 / NULLIF(SUM(cb_received), 0), 4) AS accept_rate,
       SUM(CASE WHEN outlier THEN 1 ELSE 0 END) AS outlier_rows
FROM b
GROUP BY band
ORDER BY band;
