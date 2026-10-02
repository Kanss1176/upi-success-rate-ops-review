-- Do the persistent outliers matter? Their share of chargebacks vs their share of volume.
WITH pers AS (
  SELECT code FROM read_csv('data/processed/chargeback_persistence.csv', header = true)
  WHERE months_outlier >= 3
),
b AS (
  SELECT *, (code IN (SELECT code FROM pers)) AS persistent
  FROM read_csv('data/processed/chargeback_banks.csv', header = true)
)
SELECT persistent,
       COUNT(DISTINCT code) AS banks,
       ROUND(100.0 * SUM(txns) / SUM(SUM(txns)) OVER (), 2) AS pct_of_txns,
       ROUND(100.0 * SUM(cb_received) / SUM(SUM(cb_received)) OVER (), 2) AS pct_of_chargebacks,
       ROUND(SUM(cb_received) * 1e6 / SUM(txns), 2) AS per_million
FROM b
GROUP BY persistent
ORDER BY persistent DESC;
