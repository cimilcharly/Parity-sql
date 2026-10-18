-- 07: ROWNUM filtering for top earners
SELECT * FROM (
    SELECT employee_id, last_name, salary
    FROM employees
    ORDER BY salary DESC
)
WHERE ROWNUM <= 3;
