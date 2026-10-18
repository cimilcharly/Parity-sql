-- 05: SYSDATE reference and date tenure calculation
SELECT employee_id, last_name, hire_date,
       ROUND((SYSDATE - hire_date) / 365.25, 2) AS tenure_years
FROM employees
WHERE hire_date < TO_DATE('2006-01-01', 'YYYY-MM-DD')
ORDER BY employee_id;
