-- 12: Correlated nested subquery: Employees earning above their department's average
SELECT e.employee_id, e.last_name, e.salary, e.department_id
FROM employees e
WHERE e.salary > (
    SELECT AVG(sub.salary)
    FROM employees sub
    WHERE sub.department_id = e.department_id
)
ORDER BY e.department_id, e.salary DESC;
