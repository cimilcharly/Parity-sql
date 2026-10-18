-- 11: Edge case testing NULL / empty string difference
SELECT employee_id, first_name, last_name, commission_pct
FROM employees
WHERE commission_pct IS NOT NULL
ORDER BY employee_id;
