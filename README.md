# Parity: Oracle to PostgreSQL SQL & PL/SQL Transpilation and 5-Layer Mathematical Verification Stack

> **Deterministic-first Oracle to PostgreSQL SQL & PL/SQL migration with 5-layer mathematical verification, zero raw data leakage, and automated pull requests.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-brightgreen.svg)](https://www.python.org/)
[![Verification Layers: 5](https://img.shields.io/badge/Verification%20Layers-1--5-purple.svg)](#the-5-layer-verification-stack)
[![500-Object Benchmark: 94% Pass](https://img.shields.io/badge/500--Object%20Benchmark-94.0%25%20Verified-emerald.svg)](#500-object-enterprise-benchmark-results)
[![Interactive Showcase: Live](https://img.shields.io/badge/Interactive%20Showcase-Docs%2FWeb%20App-cyan.svg)](docs/index.html)

---

## The Problem Parity Solves

Traditional SQL converters (including generic LLMs and standard transpilers) only check **syntax**. If a transpiled query runs without throwing a database error, they declare success.

In reality, **Oracle SQL and PostgreSQL diverge silently in runtime semantics**:

1. **Empty String vs NULL (`ORA_DIFF_001`)**: In Oracle, `''` is identical to `NULL`. In PostgreSQL, `''` is a string of length zero (`'' IS NULL` is `FALSE`). Transpiled `WHERE` predicates silently omit or include rows.
2. **String Concatenation (`ORA_DIFF_002`)**: In Oracle, `'a' || NULL` yields `'a'`. In PostgreSQL (ANSI standard), `'a' || NULL` yields `NULL`.
3. **Legacy Outer Joins (`ORA_DIFF_007`)**: Naive transpilers drop `(+)` outer join markers or misplace predicates, silently transforming outer joins into inner joins and dropping records.
4. **DATE Type Precision (`ORA_DIFF_003`)**: Oracle `DATE` stores hours, minutes, and seconds. Postgres `DATE` truncates time unless mapped to `TIMESTAMP`.
5. **TRUNC and Date Functions (`ORA_DIFF_010`)**: Reversed arguments and dialect-specific formatting codes.
6. **ROWNUM Evaluation Order (`ORA_DIFF_004`)**: `ROWNUM` evaluates before `ORDER BY`, whereas `LIMIT` evaluates after.
7. **PL/SQL Subsystems**: Incompatible transactional pragmas (`PRAGMA AUTONOMOUS_TRANSACTION`) and collection bulk operations (`BULK COLLECT`) fail silently if guessed.

**Parity's Rule**: *The verifier decides, not the model. The transpiler or LLM proposes, but the 5 verification layers accept or reject.*

---

## 500-Object Enterprise Benchmark Results (Week 19 Milestone)

Parity was benchmarked across **500 diverse enterprise Oracle SQL and PL/SQL objects** spanning 10 architectural categories.

```
+-----------------------------------------------------------------------------------------+
| Category                              | Objects | Verified Pass | Human Review | Failed | Pass Rate |
|---------------------------------------+---------+---------------+--------------+--------+-----------|
| 1. Base Queries & Filters             |      50 |            50 |            0 |      0 |    100.0% |
| 2. Joins & Oracle (+) Outer Joins     |      50 |            50 |            0 |      0 |    100.0% |
| 3. Window & Analytic Functions        |      50 |            50 |            0 |      0 |    100.0% |
| 4. Aggregations & Grouping            |      50 |            50 |            0 |      0 |    100.0% |
| 5. Date & Time Arithmetic             |      50 |            50 |            0 |      0 |    100.0% |
| 6. String & Null Coalescing           |      50 |            50 |            0 |      0 |    100.0% |
| 7. Hierarchical & Recursive Queries   |      50 |            50 |            0 |      0 |    100.0% |
| 8. CTEs, Subqueries & Set Operators   |      50 |            50 |            0 |      0 |    100.0% |
| 9. PL/SQL Functions & Procedures      |      50 |            50 |            0 |      0 |    100.0% |
| 10. Enterprise Edge Cases & Blockers  |      50 |            20 |           30 |      0 |     40.0% |
+-----------------------------------------------------------------------------------------+
Total Objects: 500 | Automated Verified Pass: 470 (94.0%) | Safely Flagged Human Review: 30 (6.0%) | Failed: 0
Average Cost/Object: $0.000134 USD | Average Latency: 4.22ms | Total Spend: $0.0670 USD
```

> **Key Finding**: 100% of the 30 flagged human-review objects were deliberate procedural blocker probes (`PRAGMA AUTONOMOUS_TRANSACTION`, `BULK COLLECT`, `PIPE ROW`). Parity safely isolated them with line numbers and architectural remedies rather than generating broken SQL.

---

## Architecture

```mermaid
flowchart TD
    A[Source Oracle SQL / PL/SQL] --> B[Lineage Analyzer & Topological DAG]
    B --> C[Deterministic AST Transpiler Engine]
    C -->|AST Rules: (+) Joins, Dual, Sysdate, Trunc, PL/SQL| D[Target PostgreSQL Candidate]
    
    D --> E[5-Layer Mathematical Verification Stack]
    
    subgraph E [5-Layer Verification Stack]
        L1[Layer 1: Target Compilation EXPLAIN]
        L2[Layer 2: Schema & Column Layout Match]
        L3[Layer 3: Row Count Parity Invariant]
        L4[Layer 4: Column Aggregates & Decimals <= 1e-9]
        L5[Layer 5: Row-Level Cryptographic Hashing]
        L1 --> L2 --> L3 --> L4 --> L5
    end
    
    E -->|All 5 Layers Pass| F[Verified Atomic Git PR & HTML Evidence Report]
    E -->|Mismatch Detected| G[Autonomous Repair Loop with LangGraph & KB]
    G -->|Max 3 Attempts| E
    G -->|Procedural Blocker / Unsupported| H[Isolated Human-Review Gate with Remedy]
```

---

## The 5-Layer Verification Stack

| Layer | Name | Verification Method | Caught Mismatches |
|---|---|---|---|
| **L1** | **Target Compilation** | Target `EXPLAIN` query planning | Invalid target syntax, unknown functions, keyword collisions |
| **L2** | **Schema & Columns** | Column count, normalized naming, and positioning | Column name divergence, missing projection expressions |
| **L3** | **Row Count Parity** | Exact cardinality comparison between engines | Predicate divergence, dropped rows, unintended Cartesian products |
| **L4** | **Column Aggregates** | Null counts, distinct counts, Min/Max/Avg, numeric sums within $\le 10^{-9}$ tolerance | Decimal rounding errors, string null contamination, type coercion drift |
| **L5** | **Row-Level Hashing** | SHA-256 multiset bucket hashing | Interchanged row values, sorting artifacts without leaking raw PII |

---

## Interactive Showcase & Documentation

Parity includes a rich, client-side interactive web application located in `docs/`:

- **[Interactive Showcase Web Application](docs/index.html)**:
  - **Live SQL Migration Playground**: Test Oracle SQL transpilation rules in real-time.
  - **500-Object Benchmark Explorer**: Real-time search, category filters, complexity tiers, and modal telemetry.
  - **5-Layer Verifier Visualizer**: Step-by-step interactive diagram of each invariant gate.
  - **Semantic Differences Catalog**: Interactive catalog of 15+ Oracle vs Postgres semantic traps.
- **Deep Technical Articles**:
  - [10 Ways Oracle SQL Silently Changes Meaning on PostgreSQL](docs/blog/01_ten_ways_oracle_sql_silently_changes_meaning_on_postgres.md)
  - [Verification-First Migration: Why Code Conversion Alone Fails](docs/blog/02_verification_first_migration.md)
- **Enterprise Pilot Program**:
  - [Pilot Migration Proposal (200–500 Objects)](docs/PILOT_PROPOSAL.md)
- **Community Launch & Findings**:
  - [Community Launch Kit](docs/COMMUNITY_LAUNCH.md)
  - [Upstream sqlglot Findings and Edge-Case Reports](docs/UPSTREAM_SQLGLOT_FINDINGS.md)
  - [PL/SQL Migration Reference](PLSQL_SUPPORT.md)
  - [Semantic Differences Catalog](SEMANTIC_DIFFERENCES.md)

---

## CLI Reference & Quickstart

### 1. Installation
```powershell
git clone https://github.com/parity-sql/parity.git
cd Parity
pip install -e .
```

### 2. Verify System Readiness
```powershell
parity doctor
```

### 3. Run the 500-Object Large-Scale Benchmark
```powershell
parity bench-500
```

### 4. Transpile Oracle SQL
```powershell
parity transpile src/parity/benchmark/corpus/08_outer_join_plus.sql
```

### 5. Transpile Oracle PL/SQL Function or Procedure
```powershell
parity plsql src/parity/benchmark/corpus/09_dual_scalar_math.sql
```

### 6. Run Autonomous Repair Loop
```powershell
parity repair src/parity/benchmark/corpus/02_nvl_coalesce.sql --provider mock
```

### 7. Analyze SQL Dependency Lineage & Complexity
```powershell
parity lineage src/parity/benchmark/corpus
```

### 8. Run 4-Way Ablation Matrix
```powershell
parity ablation
```

### 9. End-to-End Migration Workflow (Git Branches + PRs + HTML Reports)
```powershell
parity convert src/parity/benchmark/corpus --branch
```

### 10. Inspect Append-Only Security & Model Audit Log
```powershell
parity audit --limit 20
```

### 11. Launch Interactive Web Showcase & SQL Playground Locally
```powershell
parity showcase --port 8000
```
This serves the client-side interactive SQL transpilation playground, 500-object benchmark explorer, and verifier visualizer locally.

---

## Security & Privacy Safeguards

- **Strict Read-Only Guard**: Destructive DDL and DML statements (`DROP`, `TRUNCATE`, `ALTER`, `DELETE`, `UPDATE`, `INSERT`, `GRANT`) are blocked before database execution.
- **Zero Raw Data to Models**: Raw row values are never transmitted to LLMs or external services. Only aggregate metrics, column names, and cryptographic bucket hashes are used.
- **Hard Cost Caps & Runaway Loop Protection**: Hard caps on attempts (max 3), per-object spend ($0.05 limit), and response caching to prevent runaway costs.
- **PII Redaction**: Literals and credentials are automatically stripped and masked.
- **Append-Only Audit Logging**: All model prompts, token counts, and verification outcomes are recorded with SHA-256 hashes in `reports/audit/model_audit.jsonl`.

---

## License

This project is licensed under the [MIT License](LICENSE).
