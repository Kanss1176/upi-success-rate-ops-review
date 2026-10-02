-- Month-on-month trend in chargeback rate and acceptance rate (LAG window)
SELECT month, txns, cb_received, per_million, accept_rate,
       ROUND(per_million - LAG(per_million) OVER (ORDER BY month), 2) AS per_million_change,
       ROUND(accept_rate - LAG(accept_rate) OVER (ORDER BY month), 4) AS accept_rate_change
FROM read_csv('data/processed/chargeback_monthly.csv', header = true)
ORDER BY month;
