-- 10: Group by department with multiple numeric aggregates
SELECT department_id,
       COUNT(*) AS emp_count,
       MIN(salary) AS min_sal,
       MAX(salary) AS max_sal,
       ROUND(AVG(salary), 2) AS avg_sal,
       SUM(salary) AS total_sal
FROM employees
WHERE department_id IS NOT NULL
GROUP BY department_id
ORDER BY department_id;
