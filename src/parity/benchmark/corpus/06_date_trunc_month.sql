-- 06: TRUNC on dates to group by month
SELECT TRUNC(hire_date, 'MM') AS hire_month,
       COUNT(*) AS num_hired,
       AVG(salary) AS avg_starting_salary
FROM employees
GROUP BY TRUNC(hire_date, 'MM')
ORDER BY hire_month;
