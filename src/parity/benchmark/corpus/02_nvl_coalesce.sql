-- 02: NVL null handling on commission_pct
SELECT employee_id, last_name, salary, NVL(commission_pct, 0) AS comm_rate
FROM employees
ORDER BY employee_id;
