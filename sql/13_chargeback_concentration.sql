-- Share of monthly volume and chargebacks held by the five largest entries (RANK window)
WITH r AS (
  SELECT month, txns, cb_received,
         RANK() OVER (PARTITION BY month ORDER BY txns DESC) AS volume_rank
  FROM read_csv('data/processed/chargeback_banks.csv', header = true)
)
SELECT month,
       ROUND(100.0 * SUM(CASE WHEN volume_rank <= 5 THEN txns END) / SUM(txns), 1) AS top5_pct_of_txns,
       ROUND(100.0 * SUM(CASE WHEN volume_rank <= 5 THEN cb_received END) / SUM(cb_received), 1) AS top5_pct_of_chargebacks
FROM r
GROUP BY month
ORDER BY month;
