# Parity PL/SQL to PL/pgSQL Migration Reference

Parity provides deterministic parsing and conversion for Oracle PL/SQL functions and procedures, backed by explicit static analysis that rejects unsupported constructs rather than generating broken SQL.

---

## 1. Supported PL/SQL Constructs

| Oracle PL/SQL Construct | PostgreSQL PL/pgSQL Equivalent | Behavior / Transformation |
|---|---|---|
| `CREATE [OR REPLACE] FUNCTION name (...) RETURN type` | `CREATE OR REPLACE FUNCTION name (...) RETURNS type LANGUAGE plpgsql AS $$ ... $$;` | Wraps function body in standard dollar-quoted PL/pgSQL function syntax. |
| `CREATE [OR REPLACE] PROCEDURE name (...)` | `CREATE OR REPLACE PROCEDURE name (...) LANGUAGE plpgsql AS $$ ... $$;` | Wraps procedure in standard dollar-quoted PL/pgSQL procedure syntax. |
| `IN`, `OUT`, `IN OUT` parameters | `name type`, `OUT name type`, `INOUT name type` | Mode normalized to PostgreSQL parameter standards. |
| Local variable declarations (`IS ... BEGIN`) | `DECLARE ... BEGIN` | Placed inside the PL/pgSQL `DECLARE` section. |
| `VARCHAR2(n)`, `NVARCHAR2(n)` | `VARCHAR(n)` | Mapped to ANSI VARCHAR. |
| `NUMBER(p, s)` / `NUMBER` | `NUMERIC(p, s)` / `NUMERIC` | Mapped to arbitrary precision NUMERIC. |
| `DATE` | `TIMESTAMP WITHOUT TIME ZONE` | Preserves hours, minutes, and seconds from Oracle `DATE`. |
| `CLOB` / `BLOB` | `TEXT` / `BYTEA` | Large object type translation. |
| `col%TYPE` | `col%TYPE` | Anchored type reference preserved. |
| `DBMS_OUTPUT.PUT_LINE(msg)` | `RAISE NOTICE '%', msg;` | Converted to native Postgres notice logging. |
| `RAISE_APPLICATION_ERROR(code, msg)` | `RAISE EXCEPTION '%', msg;` | Converted to native PL/pgSQL exception. |
| `SYSDATE` | `CURRENT_TIMESTAMP` | System clock reference. |
| `NVL(a, b)` | `COALESCE(a, b)` | Null coalescing expression. |
| `TRUNC(d, 'MM')` | `DATE_TRUNC('month', d)` | Reversed argument date truncation. |
| `IF ... THEN ... ELSIF ... ELSE ... END IF;` | `IF ... THEN ... ELSIF ... ELSE ... END IF;` | Control flow constructs mapped directly. |
| `EXCEPTION WHEN ... THEN ...` | `EXCEPTION WHEN ... THEN ...` | Standard block exception handlers mapped directly. |

---

## 2. Explicitly Unsupported Constructs

Rather than making lossy assumptions, Parity scans code for the following constructs and **explicitly flags them with line numbers and migration remedies**:

| Construct | Severity | Why Unsupported Automatically | Recommended Remedy |
|---|---|---|---|
| **`PRAGMA AUTONOMOUS_TRANSACTION`** | BLOCKER | PostgreSQL transactions cannot be suspended or committed independently inside a function/procedure body. | Refactor using `dblink_connect` / `dblink_exec`, or isolate into an external client transaction. |
| **`BULK COLLECT` / `FORALL`** | BLOCKER | PL/pgSQL does not support array bulk-fetching directly into collections. | Refactor to set-based `INSERT ... SELECT`, `UPDATE`, or `UNNEST(array)`. |
| **`PIPE ROW` (Pipelined Functions)** | BLOCKER | Pipelined table functions require different semantics in PostgreSQL. | Declare function with `RETURNS TABLE(...)` and replace `PIPE ROW` with `RETURN NEXT`. |
| **`CREATE PACKAGE`** | BLOCKER | PostgreSQL has no package namespace abstraction. | Decompose package members into individual functions located inside a dedicated PostgreSQL schema. |
| **`TYPE ... IS TABLE OF / RECORD`** | BLOCKER | Custom procedural collections within function headers are not supported. | Use PostgreSQL composite types (`CREATE TYPE ... AS (...)`) or native array types (`type[]`). |
| **`GOTO <label>`** | BLOCKER | PL/pgSQL does not support unconditional branching with `GOTO`. | Restructure logic into standard `WHILE`, `LOOP`, or `EXIT WHEN` blocks. |
| **`EXECUTE IMMEDIATE ... USING`** | WARNING | Parameter binding tokens differ between Oracle and PostgreSQL dynamic SQL. | Rewrite using PostgreSQL `EXECUTE format(...) USING param1, param2`. |
| **`UTL_FILE`, `UTL_HTTP`, `DBMS_*`** | BLOCKER | Proprietary Oracle OS and subsystem interfaces. | Use PostgreSQL extensions (`pg_cron`, `http`) or move logic to application layer. |
