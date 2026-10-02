-- Control exceptions per month (conditional aggregation); nothing is silently corrected
SELECT control,
       SUM(CASE WHEN month = '2026-04' THEN 1 ELSE 0 END) AS apr,
       SUM(CASE WHEN month = '2026-05' THEN 1 ELSE 0 END) AS may,
       SUM(CASE WHEN month = '2026-06' THEN 1 ELSE 0 END) AS jun,
       SUM(CASE WHEN month = '2026-07' THEN 1 ELSE 0 END) AS jul,
       COUNT(*) AS total
FROM read_csv('data/processed/chargeback_exceptions.csv', header = true)
GROUP BY control
ORDER BY control;
