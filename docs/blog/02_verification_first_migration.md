# Verification-First Migration: Why Code Conversion Alone Fails

*By the Parity Engineering Team • Published October 2026*

Every enterprise database migration starts with optimism. A vendor or consulting team arrives with an AST transpiler or fine-tuned LLM, converts 10,000 Oracle SQL queries into PostgreSQL syntax in an afternoon, and shows an impressive chart of green checkmarks.

Then comes integration testing.

Six months later, the project is stalled, the budget is depleted, and the data engineering team is working nights writing manual comparison scripts in Python or Excel to find out why the executive revenue dashboard differs by $42,000 between Oracle and Postgres.

The root cause is fundamental: **In enterprise database migrations, code translation is only 20% of the difficulty. The other 80% is verification.**

---

## The Illusion of Compiler Success

In software engineering, if code compiles and tests pass, it usually works. In relational databases, this intuition is dangerously wrong.

A query in PostgreSQL can:
1. Parse cleanly (Layer 1 pass)
2. Return columns with matching names (Layer 2 pass)
3. Return exactly 10,000 rows (Layer 3 pass)
4. **And still be completely mathematically wrong.**

Consider an innocent translation of an Oracle outer join with an additional filter predicate:
```sql
-- Oracle Source:
SELECT e.employee_id, d.department_name
FROM employees e, departments d
WHERE e.department_id = d.department_id(+)
  AND d.location_id = 1700;
```
If a naive migration script converts this to:
```sql
-- Naive PostgreSQL Conversion:
SELECT e.employee_id, d.department_name
FROM employees e
LEFT JOIN departments d ON e.department_id = d.department_id
WHERE d.location_id = 1700;
```
This PostgreSQL query compiles instantly. It runs in 4 milliseconds. If all departments in your small development database happen to be in location 1700, it even returns the exact same number of rows.

In production, however, employees with `NULL` departments or departments in other locations are silently dropped because the `WHERE` clause filters out the outer join's null rows. The row count drops from 107 to 24.

---

## Why Generative AI Without Verification Makes Things Worse

Over the past two years, teams have attempted to replace rule-based transpilers with large language models. The results are deceptively dangerous.

LLMs are creative language predictors. When asked to convert complex Oracle SQL with `CONNECT BY`, analytic functions, and `NVL2`, an LLM will generate beautifully formatted, convincing PostgreSQL SQL that *looks* idiomatic. But LLMs:
- **Invent columns** that seem plausible given the context.
- **Silently invert outer join orders** when trying to simplify code.
- **Drop subtle edge-case guards** (like `NOCYCLE` or collation overrides).

Crucially, you cannot ask an LLM: *"Did you preserve mathematical equivalence across 5 million rows?"* The model does not know. Only the execution engines of the databases themselves can answer that question.

---

## The Parity Philosophy: Deterministic First, Mathematical Verification Always

Parity was built on three architectural principles:

### 1. Deterministic First, Model for Residue
95% of dialect differences should be handled by predictable, deterministic AST transforms (`sqlglot` + custom grammar rules). The LLM is invoked only for the tricky procedural residue, and its output is treated as untrusted user input until validated.

### 2. The Verifier Decides, Not the Model
The model proposes a translation candidate. It does not get to declare victory. The candidate is sent to the 5-layer verification stack. If any layer fails, the verifier provides structural diagnostics back to the repair loop.

### 3. Zero Raw Data to External Services
You cannot send patient medical records, banking transaction amounts, or customer PII to cloud LLMs or external servers. Parity executes queries against isolated local or private databases and transmits **only aggregate metrics, column names, and cryptographic bucket hashes**.

---

## The 5-Layer Mathematical Verification Stack

How does Parity prove that two SQL statements in different database dialects produce identical results?

```
┌────────────────────────────────────────────────────────┐
│ Layer 1: Syntax & Compile Invariant                    │
├────────────────────────────────────────────────────────┤
│ Layer 2: Schema, Arity & Type Coercion Invariant       │
├────────────────────────────────────────────────────────┤
│ Layer 3: Cardinality & Row Count Equality              │
├────────────────────────────────────────────────────────┤
│ Layer 4: Statistical Column Aggregates & Null Density  │
├────────────────────────────────────────────────────────┤
│ Layer 5: Cryptographic Row-Level Bucketed Hashing      │
└────────────────────────────────────────────────────────┘
```

### Layer 1: Dialect Compilation
Validates that target SQL compiles cleanly on PostgreSQL, rejecting deprecated keywords, invalid operators, or unmigrated procedural pragmas.

### Layer 2: Schema & Type Match
Validates that output columns match in count (arity), normalized naming, and compatible datatypes.

### Layer 3: Row Count Equality
Validates that `COUNT(*)` matches exactly between Oracle and PostgreSQL. Catches Cartesian row explosions and dropped outer rows.

### Layer 4: Statistical Column Aggregates
Computes `SUM`, `AVG`, `MIN`, `MAX`, and `COUNT(col)` for all numeric and date columns, plus `NULL_COUNT` for all nullable columns:
$$\left| \mu_{\text{Oracle}} - \mu_{\text{Postgres}} \right| < 10^{-9}$$
This layer catches silent float rounding, integer division truncation, and empty string `''` vs `NULL` divergences.

### Layer 5: Cryptographic Row Hashing
Computes MD5 or SHA-256 checksums across concatenated row values within deterministic partitions. Even if column averages match, swapped values across rows (e.g. employee A getting employee B's salary) diverge immediately at Layer 5.

---

## The Result: Automated, Auditable Confidence

When Parity runs across a migration corpus:
- **Clean queries** pass through with zero human intervention and sub-15ms verification times.
- **Tricky queries** are automatically repaired in 1 to 2 attempts using dialect knowledge base entries.
- **Unsupported procedural constructs** (like `PRAGMA AUTONOMOUS_TRANSACTION`) are safely isolated with precise line numbers and architectural remedies, generating an atomic Git branch and Pull Request for human sign-off.

Stop guessing whether your migrated SQL matches Oracle. Make mathematical proof the foundation of your migration strategy.
