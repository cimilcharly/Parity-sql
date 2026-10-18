# Upstream sqlglot Findings and Edge-Case Reports (Week 22)

During the development of Parity and execution of the 500-object enterprise benchmark suite, our 5-layer verification stack uncovered several nuanced Oracle &rarr; PostgreSQL dialect edge cases in general AST transpilation engines (including `sqlglot`).

This document records the exact syntax reproductions, expected behaviors, and recommended upstream fixes for submission to the `sqlglot` repository.

---

## Finding 1: Oracle `(+)` Outer Join with Subsequent Filter Predicates

### Issue Summary:
When transpiling legacy Oracle `(+)` outer joins where one table has an additional filtering predicate in the `WHERE` clause, naive outer join conversion places the additional predicate in the target `WHERE` clause instead of inside the ANSI `LEFT JOIN ... ON` clause.

### Minimal Reproduction:
```sql
-- Oracle Source SQL:
SELECT e.employee_id, d.department_name
FROM employees e, departments d
WHERE e.department_id = d.department_id(+)
  AND d.location_id(+) = 1700;
```

### Naive / Buggy Output:
```sql
SELECT e.employee_id, d.department_name
FROM employees AS e
LEFT JOIN departments AS d ON e.department_id = d.department_id
WHERE d.location_id = 1700;
```
**Why this fails Layer 3 & Layer 4:**
In PostgreSQL, evaluating `WHERE d.location_id = 1700` filters out all rows where `d.department_id` was `NULL` (from employees with no department). This inadvertently turns the `LEFT JOIN` back into an `INNER JOIN`.

### Correct Generated SQL:
```sql
SELECT e.employee_id, d.department_name
FROM employees AS e
LEFT JOIN departments AS d 
  ON e.department_id = d.department_id 
 AND d.location_id = 1700;
```

---

## Finding 2: `TRUNC(date, 'MM')` vs `DATE_TRUNC('month', date)` Argument Inversion

### Issue Summary:
In Oracle, `TRUNC(date, unit)` takes the date value as the *first* argument and the truncation unit as the *second* argument (`TRUNC(hire_date, 'MM')`).
In PostgreSQL, `DATE_TRUNC(unit, date)` takes the truncation unit as the *first* argument and the timestamp as the *second* argument (`DATE_TRUNC('month', hire_date)`).

Additionally, Oracle allows `'MM'` or `'MONTH'`, whereas PostgreSQL expects `'month'`.

### Correct Rule Implemented in Parity:
Parity's AST transformer intercepts `sqlglot.expressions.Anonymous` where `this.name.upper() == "TRUNC"` and transforms the node into an `Anonymous(this="DATE_TRUNC", expressions=[reversed_and_normalized_unit, date_expr])`.

---

## Finding 3: `NVL2(expr, not_null_val, null_val)` Conditional Evaluation

### Issue Summary:
Oracle's `NVL2` function evaluates ternary nullness. When converting to PostgreSQL, mapping `NVL2` to nested `COALESCE` can result in incorrect evaluation if `not_null_val` itself evaluates to `NULL`.

### Correct Generated SQL:
```sql
-- Oracle:
SELECT NVL2(commission_pct, salary * (1 + commission_pct), salary) FROM employees;

-- PostgreSQL Target:
SELECT CASE 
         WHEN commission_pct IS NOT NULL THEN salary * (1 + commission_pct) 
         ELSE salary 
       END 
FROM employees;
```

---

## Finding 4: Empty String `''` Concatenation and Null Propagation

### Issue Summary:
In Oracle:
```sql
SELECT 'Hello' || '' || 'World' FROM DUAL; -- Evaluates to 'HelloWorld'
```
In standard ANSI SQL and PostgreSQL without custom collation:
```sql
SELECT 'Hello' || '' || 'World'; -- Evaluates to 'HelloWorld'
```
However:
```sql
SELECT 'Hello' || NULL || 'World'; -- Evaluates to NULL in PostgreSQL, but 'HelloWorld' in Oracle!
```
Because Oracle treats `''` as `NULL`, expressions that concatenate nullable columns (`first_name || ' ' || middle_name || ' ' || last_name`) evaluate to `NULL` in PostgreSQL if any single component is `NULL`.

### Parity Automated Fix:
Parity rewrites string concatenations using PostgreSQL's null-safe `CONCAT_WS()` or `CONCAT()` functions:
```sql
SELECT CONCAT_WS(' ', first_name, NULLIF(middle_name, ''), last_name) FROM employees;
```
