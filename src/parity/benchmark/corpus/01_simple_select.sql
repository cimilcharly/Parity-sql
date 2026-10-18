-- 01: Simple selection with projection and predicate
SELECT employee_id, first_name, last_name, salary
FROM employees
WHERE salary >= 10000
ORDER BY salary DESC, employee_id ASC;
