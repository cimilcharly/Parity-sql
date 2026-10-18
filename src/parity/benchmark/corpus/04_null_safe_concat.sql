-- 04: String concatenation with potential NULL values
SELECT employee_id, first_name || ' ' || last_name AS full_name,
       first_name || ' (' || phone_number || ')' AS contact_card
FROM employees
ORDER BY employee_id;
