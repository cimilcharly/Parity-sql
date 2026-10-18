# 10 Ways Oracle SQL Silently Changes Meaning on PostgreSQL

*By the Parity Engineering Team • Published October 2026*

When migrating enterprise workloads from Oracle Database to PostgreSQL, syntax errors are your best friend. If a query crashes with `syntax error at or near...`, your automated CI pipeline catches it immediately, a human engineer inspects it, and nobody gets fired.

The real killers are **silent semantic divergences**—queries that compile cleanly on PostgreSQL, execute in milliseconds without a single warning, and return results that look plausible at first glance, but are mathematically and logically divergent from Oracle.

In this deep dive, we catalog the ten most treacherous semantic pitfalls encountered in real-world enterprise Oracle-to-PostgreSQL migrations, analyze why naive transpilers miss them, and explain how to verify against them mathematically.

---

## 1. The Empty String `''` vs `NULL` Trap

In Oracle Database, an empty string literal `''` is coerced to `NULL` at the SQL engine level. In PostgreSQL (and the ANSI SQL standard), `''` is a distinct string of zero length (`CHAR_LENGTH('') = 0`), which is completely different from `NULL`.

### Oracle Behavior:
```sql
-- Evaluates to TRUE in Oracle:
SELECT employee_id FROM employees WHERE commission_pct IS NULL;
-- In Oracle, this ALSO matches rows where commission_pct was set to '':
SELECT employee_id FROM employees WHERE commission_pct = ''; -- Returns NO rows (NULL = '' is UNKNOWN)
```

### PostgreSQL Divergence:
```sql
-- In PostgreSQL:
SELECT '' IS NULL;     -- Returns FALSE!
SELECT '' = '';        -- Returns TRUE!
SELECT LENGTH('');     -- Returns 0!
```

### The Production Impact:
Filtering for `WHERE comment IS NOT NULL` in Oracle drops both `NULL` values and empty strings. In PostgreSQL, rows containing `''` survive the filter, silently leaking blank records into downstream reports, metric aggregations, and data pipelines.

**Parity Remedy:**
Rewrite string nullness checks to `WHERE col IS NOT NULL AND col <> ''` or use a custom PostgreSQL domain/trigger if Oracle empty-string semantics must be preserved globally.

---

## 2. Oracle `DATE` Contains Time Components

In Oracle, the `DATE` data type is actually a timestamp: it stores century, year, month, day, hour, minute, and second. In PostgreSQL, `DATE` stores *only* year, month, and day.

### Oracle Behavior:
```sql
-- Oracle: hire_date contains '2024-03-15 14:32:00'
SELECT hire_date FROM employees WHERE hire_date = TO_DATE('2024-03-15', 'YYYY-MM-DD');
-- Returns FALSE because 14:32:00 != 00:00:00!
```

### PostgreSQL Divergence:
If a migration schema translates Oracle `DATE` to PostgreSQL `DATE` instead of `TIMESTAMP WITHOUT TIME ZONE`, the time portion is permanently and irreversibly truncated.
```sql
-- In PostgreSQL with DATE type:
SELECT hire_date = '2024-03-15'::DATE; -- Evaluates to TRUE, dropping time granularity!
```

**Parity Remedy:**
Always map Oracle `DATE` columns to PostgreSQL `TIMESTAMP(0) WITHOUT TIME ZONE` unless a business domain explicitly guarantees that the column never contains fractional day values.

---

## 3. `ROWNUM` Evaluation Order vs `LIMIT` / `OFFSET`

In Oracle, `ROWNUM` is assigned to rows as they are fetched from the candidate result set *before* the `ORDER BY` clause is evaluated.

### Oracle Behavior:
```sql
-- In Oracle, this selects 5 ARBITRARY rows, and THEN sorts those 5 by salary:
SELECT employee_id, salary 
FROM employees 
WHERE ROWNUM <= 5 
ORDER BY salary DESC;
```
To get the actual top 5 earners in Oracle, you are forced to write a subquery:
```sql
SELECT * FROM (
    SELECT employee_id, salary FROM employees ORDER BY salary DESC
) WHERE ROWNUM <= 5;
```

### PostgreSQL Divergence:
In PostgreSQL, `LIMIT` is evaluated *after* `ORDER BY`:
```sql
SELECT employee_id, salary FROM employees ORDER BY salary DESC LIMIT 5;
```
If a developer blindly translates `WHERE ROWNUM <= 5` into `LIMIT 5` on an unsorted or partially sorted query without understanding subquery nesting, the returned subset changes entirely.

---

## 4. Oracle `(+)` Outer Joins with Complex Filter Predicates

Oracle's legacy `(+)` operator specifies a left or right outer join. However, the placement of `(+)` in the `WHERE` clause fundamentally changes whether a predicate acts as a **join filter** or a **post-join filter**.

### Oracle Syntax:
```sql
SELECT e.employee_id, d.department_name
FROM employees e, departments d
WHERE e.department_id = d.department_id(+)
  AND d.location_id(+) = 1700;
```

### The Divergence in ANSI SQL:
If the `(+)` is omitted on the second predicate:
```sql
-- BROKEN NAIVE REWRITE:
SELECT e.employee_id, d.department_name
FROM employees e
LEFT JOIN departments d ON e.department_id = d.department_id
WHERE d.location_id = 1700; -- BUG: Turns the LEFT JOIN back into an INNER JOIN!
```
The correct ANSI translation requires placing `d.location_id = 1700` in the `ON` clause, not the `WHERE` clause:
```sql
-- CORRECT PARITY TRANSLATION:
SELECT e.employee_id, d.department_name
FROM employees e
LEFT JOIN departments d 
  ON e.department_id = d.department_id 
 AND d.location_id = 1700;
```

---

## 5. Trailing Whitespace in Fixed-Width `CHAR(n)`

Oracle and PostgreSQL handle space-padded `CHAR(n)` comparisons with subtle differences when comparing fixed-width columns with variable-width literals.

### Divergence:
```sql
-- Given a column dept_code CHAR(5) storing 'IT   ':
-- Oracle:
SELECT * FROM departments WHERE dept_code = 'IT'; -- MATCHES (blank-padded comparison semantics)

-- PostgreSQL:
SELECT * FROM departments WHERE dept_code = 'IT'::text; -- FAILS unless cast to CHAR(5) or trimmed!
```

---

## 6. Integer Division vs Arbitrary-Precision `NUMBER`

In Oracle, numeric calculations default to arbitrary-precision `NUMBER`. In PostgreSQL, division between integer types performs integer truncation.

### Divergence:
```sql
-- Oracle:
SELECT 5 / 2 FROM DUAL; -- Returns 2.5

-- PostgreSQL:
SELECT 5 / 2;           -- Returns 2! (Integer division truncated)
SELECT 5.0 / 2;         -- Returns 2.5000000000000000
```
In financial or risk models calculating ratios or interest rates, integer division truncation silently converts million-dollar payouts into zero.

---

## 7. Set Operators: `MINUS` vs `EXCEPT` Duplicate Semantics

Oracle uses `MINUS` to compute set difference. PostgreSQL uses `EXCEPT`. While they appear synonymous, their interaction with duplicate rows in complex subqueries can diverge if `ALL` is mistakenly appended or omitted.

```sql
-- Oracle:
SELECT dept_id FROM table_a MINUS SELECT dept_id FROM table_b;
-- In Oracle, MINUS implicitly performs a DISTINCT on both sets.

-- PostgreSQL:
SELECT dept_id FROM table_a EXCEPT SELECT dept_id FROM table_b;
-- EXCEPT also does DISTINCT, but EXCEPT ALL preserves duplicates.
```

---

## 8. `SYSDATE` Real-Time Clock vs `CURRENT_TIMESTAMP` Transaction Clock

This is one of the most insidious timing divergences in long-running batch jobs.

### Divergence:
- **Oracle `SYSDATE`**: Evaluated at the physical moment each row or statement is processed. In a loop or slow query taking 10 minutes, `SYSDATE` changes as time advances.
- **PostgreSQL `CURRENT_TIMESTAMP`**: Frozen at the start of the current transaction! Every call to `CURRENT_TIMESTAMP` inside the same transaction returns the exact same timestamp.

If your Oracle application relied on `SYSDATE` to measure duration or record sub-second row arrival times within a batch, PostgreSQL will record identical timestamps for all rows. Use `clock_timestamp()` in PostgreSQL when real-time wall-clock readings are required.

---

## 9. Sequence Next-Value Semantics

In Oracle, sequence progression uses `seq_name.NEXTVAL`. In PostgreSQL, sequence progression uses `nextval('seq_name')`.

In Oracle, multiple occurrences of `seq_name.NEXTVAL` within the same SQL statement return the **same value** for a given row. In PostgreSQL, calling `nextval('seq_name')` multiple times in a `SELECT` list increments the sequence independently for each column!

---

## 10. `CONNECT BY PRIOR` vs `WITH RECURSIVE` Infinite Loops

Oracle's `CONNECT BY PRIOR` has built-in loop detection via the `NOCYCLE` keyword and provides pseudo-columns like `LEVEL`, `CONNECT_BY_ISCYCLE`, and `SYS_CONNECT_BY_PATH`.

When transpiling to PostgreSQL's ANSI `WITH RECURSIVE`, you must explicitly construct cycle detection arrays (`ARRAY[employee_id]`) and termination guards (`WHERE NOT (employee_id = ANY(path))`), otherwise circular organizational charts or Bill-of-Materials structures will hang the PostgreSQL query engine in an infinite loop.

---

## Conclusion: Why You Need Verification, Not Just Translation

No static transpiler alone—and certainly no generic LLM—can guarantee that every single edge case above has been handled correctly for your company's proprietary schema.

That is why **Parity** was engineered with a **5-layer verification stack**:
1. Target Syntax & Compilation
2. Schema & Type Match
3. Exact Row Count Equality
4. Column Statistics & Null Density (catches empty string vs NULL)
5. Cryptographic Row Hashing (catches ordering and value swapping)

Before migrating your database to production, run Parity to prove mathematical equivalence.
