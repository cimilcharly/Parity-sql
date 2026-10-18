# Oracle to PostgreSQL Semantic Differences Knowledge Base

A key design pillar of **Parity** is that semantic migration failures are rarely caused by parse errors—they are caused by silent behavioral differences where transpiled SQL compiles and executes without errors but produces subtly different data, row counts, or nullability.

Below are the 20 primary semantic divergences cataloged by Parity:

---

### 1. `ORA_DIFF_001`: Empty String vs NULL
- **Oracle**: An empty string literal `''` is semantically equivalent to `NULL`. Expressions like `WHERE col = ''` or `col IS NULL` behave identically.
- **PostgreSQL**: `''` is a distinct `TEXT`/`VARCHAR` value of length 0. `'' IS NULL` evaluates to `FALSE`.
- **Trap**: Transpiling `WHERE col IS NOT NULL` will include rows with `''` in Postgres, but exclude them in Oracle.
- **Verification Catch**: Layer 3 (Row Counts) & Layer 4 (Null counts).

---

### 2. `ORA_DIFF_002`: String Concatenation (`||`) with NULL
- **Oracle**: Concatenating any string with `NULL` ignores the `NULL`: `'Hello' || NULL || ' World'` produces `'Hello World'`.
- **PostgreSQL**: Following ANSI standards, concatenating with `NULL` yields `NULL`: `'Hello' || NULL` produces `NULL`.
- **Mitigation**: Transpile `||` to Postgres `CONCAT(a, b)` or `COALESCE(a, '') || COALESCE(b, '')`.
- **Verification Catch**: Layer 4 (Aggregates & Null Counts) & Layer 5 (Row Hashing).

---

### 3. `ORA_DIFF_003`: `DATE` Type Precision
- **Oracle**: The `DATE` datatype includes both calendar date and time components (to the second): `YYYY-MM-DD HH24:MI:SS`.
- **PostgreSQL**: `DATE` stores only the date (`YYYY-MM-DD`). Time components are silently truncated unless mapped to `TIMESTAMP(0)` or `TIMESTAMP WITHOUT TIME ZONE`.
- **Verification Catch**: Layer 2 (Schema Types) & Layer 4 (Column Aggregates).

---

### 4. `ORA_DIFF_004`: `NVL` and `NVL2`
- **Oracle**: Proprietary null-coalescing functions: `NVL(expr1, expr2)` and `NVL2(expr1, if_not_null, if_null)`.
- **PostgreSQL**: Does not have `NVL`. Must transpile `NVL(a, b)` to `COALESCE(a, b)`, and `NVL2(a, b, c)` to `CASE WHEN a IS NOT NULL THEN b ELSE c END`.

---

### 5. `ORA_DIFF_005`: `DECODE` Conditional Logic
- **Oracle**: `DECODE(val, search1, result1, search2, result2, ..., default)` evaluates equality, treating `NULL = NULL` as TRUE.
- **PostgreSQL**: Standard `CASE val WHEN search1 THEN result1 ... ELSE default END`.
- **Note**: Special care is needed if `search` contains `NULL`, since standard `CASE` in Postgres uses `= NULL` which evaluates to unknown.

---

### 6. `ORA_DIFF_006`: `ROWNUM` Filtering & Pagination
- **Oracle**: `ROWNUM` is a pseudo-column assigned dynamically as rows pass the predicate filter: `WHERE ROWNUM <= 10 ORDER BY salary DESC` sorts *after* truncating to 10 rows!
- **PostgreSQL**: `LIMIT` and `OFFSET` or window function `ROW_NUMBER() OVER (ORDER BY salary DESC)`.

---

### 7. `ORA_DIFF_007`: Legacy `(+)` Outer Join Syntax
- **Oracle**: `WHERE t1.id = t2.id(+)` indicates a `LEFT OUTER JOIN` on `t1`.
- **PostgreSQL**: Does not support `(+)`. Must be rewritten into standard ANSI `LEFT OUTER JOIN ... ON ...`.

---

### 8. `ORA_DIFF_008`: Sequence Syntax
- **Oracle**: `seq_name.NEXTVAL` and `seq_name.CURRVAL`.
- **PostgreSQL**: `nextval('seq_name')` and `currval('seq_name')`.

---

### 9. `ORA_DIFF_009`: `SYSDATE` and `SYSTIMESTAMP`
- **Oracle**: `SYSDATE` returns the current system datetime (as `DATE`).
- **PostgreSQL**: `CURRENT_TIMESTAMP` or `clock_timestamp()` or `NOW()`. For date-only: `CURRENT_DATE`.

---

### 10. `ORA_DIFF_010`: `TRUNC` on Dates
- **Oracle**: `TRUNC(sysdate, 'MM')` truncates date to the beginning of the month.
- **PostgreSQL**: `date_trunc('month', CURRENT_TIMESTAMP)`. Note argument order is reversed!

---

### 11. `ORA_DIFF_011`: Identifier Casing & Quoting
- **Oracle**: Unquoted identifiers are automatically folded to UPPERCASE.
- **PostgreSQL**: Unquoted identifiers are automatically folded to lowercase.
- **Trap**: Double-quoted identifiers in Oracle `"EMP"` match unquoted `emp` in Oracle, but in Postgres `"EMP"` requires uppercase and will NOT match `emp`.

---

### 12. `ORA_DIFF_012`: `ADD_MONTHS(date, n)`
- **Oracle**: Native function `ADD_MONTHS(hire_date, 6)`.
- **PostgreSQL**: `hire_date + (INTERVAL '1 month' * n)` or `(hire_date + make_interval(months => n))`.

---

### 13. `ORA_DIFF_013`: `INSTR` vs `POSITION` / `STRPOS`
- **Oracle**: `INSTR(string, substring [, position [, occurrence]])` (1-indexed).
- **PostgreSQL**: `POSITION(substring IN string)` or `STRPOS(string, substring)`. For nth occurrence, regex or custom helper is required.

---

### 14. `ORA_DIFF_014`: `SUBSTR` with Negative Index
- **Oracle**: `SUBSTR('abcdef', -2)` extracts 2 characters from the end: `'ef'`.
- **PostgreSQL**: Standard `substr(string, from, count)` requires positive start index. For negative offsets, `RIGHT(string, 2)` or `substring(string from length(string) - 1)` must be used.

---

### 15. `ORA_DIFF_015`: Dual Dummy Table
- **Oracle**: `SELECT 1 + 1 FROM DUAL;`
- **PostgreSQL**: `SELECT 1 + 1;` (`FROM DUAL` is unnecessary; Postgres accepts standard queries without a `FROM` clause).

---

### 16. `ORA_DIFF_016`: Implicit Type Coercion
- **Oracle**: Permissive auto-casting (e.g. `'123' + 5` evaluates to `128`, string dates auto-parsed).
- **PostgreSQL**: Strict type checking; throws type mismatch errors unless explicitly cast via `CAST(x AS INT)` or `x::integer`.

---

### 17. `ORA_DIFF_017`: `CONNECT BY` Hierarchical Queries
- **Oracle**: Native `START WITH ... CONNECT BY PRIOR ...` construct.
- **PostgreSQL**: Requires ANSI recursive Common Table Expressions (`WITH RECURSIVE ...`).

---

### 18. `ORA_DIFF_018`: `NUMBER` vs `NUMERIC` / `DOUBLE PRECISION`
- **Oracle**: `NUMBER` with no precision/scale supports up to 38 digits of precision with arbitrary scale.
- **PostgreSQL**: `NUMERIC` or `DOUBLE PRECISION`.

---

### 19. `ORA_DIFF_019`: Division by Zero & Floating Point
- **Oracle**: Throws `ORA-01476: divisor is equal to zero`.
- **PostgreSQL**: Throws `ERROR: division by zero`. In analytical contexts, `NULLIF(divisor, 0)` is the deterministic fix.

---

### 20. `ORA_DIFF_020`: String Padding and Comparison Semantics
- **Oracle**: `CHAR(n)` data types are blank-padded and use blank-padded comparison semantics.
- **PostgreSQL**: `CHAR(n)` also pads spaces, but behavior in concatenation and pattern matching can diverge from `VARCHAR`.
