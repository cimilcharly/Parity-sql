-- 03: DECODE function categorization
SELECT employee_id, last_name, job_id,
       DECODE(job_id, 'AD_PRES', 'Executive', 'AD_VP', 'Executive', 'IT_PROG', 'Technical', 'General') AS role_tier
FROM employees
ORDER BY employee_id;
