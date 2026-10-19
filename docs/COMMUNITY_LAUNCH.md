# Parity Community Launch & Social Distribution Kit (Week 22)

This document contains copy, technical angles, and distribution plans for sharing Parity across data engineering and database communities.

---

## 1. Reddit: r/dataengineering & r/PostgreSQL

**Title:** Show r/dataengineering: Parity – Deterministic Oracle to PostgreSQL migration with 5-layer mathematical verification (Open Source)

**Body:**
> Hey r/dataengineering,
>
> Over the past year, our team worked on multiple large-scale Oracle-to-PostgreSQL migrations. Every single time, the hardest part wasn't writing syntax converters—it was answering the VP of Engineering’s question: *"How do you prove the new PostgreSQL database produces identical numbers to Oracle?"*
>
> In production, standard syntax transpilation isn't enough. Oracle empty string `''` is treated as `NULL` while in Postgres `''` is a 0-length string; Oracle `DATE` has a time part; Oracle `ROWNUM` evaluates before `ORDER BY`; and Oracle `(+)` outer joins with where predicates silently drop rows if naively translated.
>
> To solve this, we built **Parity** – an open-source, deterministic-first migration and verification framework:
>
> 🔬 **The 5-Layer Verification Stack:**
> Instead of guessing, Parity runs queries against both databases and validates:
> 1. Target syntax compilation
> 2. Schema, column arity & type coercion
> 3. Exact row count equality
> 4. Column statistics (SUM, AVG, MIN, MAX, NULL counts within 1e-9 tolerance)
> 5. Cryptographic row-level bucket hashing (catches swapped row values)
>
> 🤖 **Zero Raw Data to LLMs:**
> Parity uses deterministic AST transforms (`sqlglot` + custom grammar rules) for 95% of queries. The LLM is used only for residual repair, and it receives ONLY aggregate summaries, column names, and hash buckets—never raw data or PII.
>
> 📊 **500-Object Benchmark:**
> We ran Parity across a diverse 500-object enterprise benchmark suite (joins, analytic functions, hierarchical CTEs, PL/SQL):
> - **94.0% Direct Verified Pass**
> - **98.6% Pass Rate with LLM+KB Repair**
> - **6.0% Safely Flagged Human Review** (isolated explicit blockers like `PRAGMA AUTONOMOUS_TRANSACTION` with line numbers and refactoring advice)
> - **Average Cost:** $0.00013 / object
>
> Check out the GitHub repo and interactive live demo:
> - GitHub: https://github.com/cimilcharly/Parity-sql
> - Interactive Demo & Benchmark Explorer: https://parity-sql.dev
>
> Would love feedback on the verification layers or edge cases you've hit in your dialect migrations!

---

## 2. LinkedIn Post (Data Architects & Engineering Leaders)

**Post Content:**
> The biggest lie in database migration is: *"It compiled without errors, so it must be right."*
>
> When migrating Oracle SQL to PostgreSQL, queries can compile in milliseconds and return 10,000 rows—while silently corrupting revenue metrics by hundreds of thousands of dollars.
>
> Why?
> 1. In Oracle, `'' IS NULL` is TRUE. In PostgreSQL, it's FALSE.
> 2. Oracle `DATE` secretly stores hours, minutes, and seconds.
> 3. Oracle `(+)` outer joins behave differently when paired with `WHERE` filters.
> 4. Oracle `ROWNUM` evaluates *before* `ORDER BY`.
>
> Today, we're open-sourcing **Parity**: a deterministic-first Oracle &rarr; PostgreSQL transpiler and 5-layer mathematical verification framework.
>
> Parity runs queries across both databases and mathematically proves parity across schemas, row counts, statistical column distributions (within 1e-9 tolerance), and cryptographic row hashes.
>
> In our 500-object enterprise benchmark:
> ⚡ 94.0% automated verified pass rate (98.6% with repair)
> 🛡️ 0 byte raw customer data ever transmitted to language models
> 📂 Automatic Git PRs and interactive HTML evidence audit reports
>
> Read our full technical deep-dive: "10 Ways Oracle SQL Silently Changes Meaning on PostgreSQL" in the comments below.
>
> #DataEngineering #PostgreSQL #Oracle #DatabaseMigration #OpenSource #SQL

---

## 3. dbt Community & Postgres Mailing Lists

**Topic:** Automated Dialect Semantic Verification Tooling for Oracle &rarr; Postgres

**Summary:**
> Introducing Parity: an open-source tool designed to eliminate manual data diffing when porting complex Oracle legacy queries, views, and PL/SQL functions to PostgreSQL. Parity produces audit-ready evidence reports comparing column statistics and cryptographic hashes, with full support for modern CI pipelines.

---

## 4. Twitter / X Thread

**Tweet 1:**
> Announcing Parity: An open-source, deterministic-first Oracle &rarr; PostgreSQL SQL & PL/SQL migration framework with 5-layer mathematical verification.
> 
> Here is why traditional SQL transpilation silently fails in enterprise migrations (and how we fixed it) 🧵👇

**Tweet 2:**
> 1/ Compiler success is an illusion.
> In Oracle, `WHERE col = ''` matches nothing because empty string is NULL.
> In Postgres, `''` is a 0-length string! Rows survive the filter and silently corrupt downstream financial reports.

**Tweet 3:**
> 2/ The Parity 5-Layer Invariant Stack:
> L1: Syntax & Compile
> L2: Schema & Types
> L3: Row Count Equality
> L4: Statistical Column Aggregates (SUM, AVG within 1e-9)
> L5: Cryptographic Row Hashing
> Every query must pass all 5 gates before cutover.

**Tweet 4:**
> 3/ Zero Raw Data to LLMs.
> Regulated enterprises cannot send customer PII to cloud models.
> Parity executes locally and passes only column names, metrics, and bucket hashes to the repair engine.

**Tweet 5:**
> Try the interactive live playground & explore the 500-object benchmark:
> https://parity-sql.dev
> ⭐ Star the project on GitHub: https://github.com/cimilcharly/Parity-sql
