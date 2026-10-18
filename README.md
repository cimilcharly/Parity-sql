# Parity: Oracle to PostgreSQL SQL Transpilation & Semantic Verification

> **Deterministic-first Oracle to PostgreSQL SQL migration with 5-layer semantic verification.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-brightgreen.svg)](https://www.python.org/)
[![Verification Layers: 5](https://img.shields.io/badge/Verification%20Layers-1--5-purple.svg)](#the-5-layer-verification-stack)
[![Status: Foundation Complete](https://img.shields.io/badge/Phase%201-Foundation%20Ready-emerald.svg)](parity.md)

---

## The Problem Parity Solves

Traditional SQL converters (including generic LLMs and standard transpilers) only check **syntax**. If a transpiled query runs without throwing a database error, they declare success.

In reality, **Oracle SQL and PostgreSQL diverge silently in runtime semantics**:

1. **Empty String vs NULL (`ORA_DIFF_001`)**: In Oracle, `''` is identical to `NULL`. In PostgreSQL, `''` is a string of length zero (`'' IS NULL` is `FALSE`). Transpiled `WHERE` predicates silently omit or include rows.
2. **String Concatenation (`ORA_DIFF_002`)**: In Oracle, `'a' || NULL` yields `'a'`. In PostgreSQL (ANSI standard), `'a' || NULL` yields `NULL`.
3. **Legacy Outer Joins (`ORA_DIFF_007`)**: Standard transpilers drop `(+)` outer join markers, silently transforming outer joins into inner joins and losing records.
4. **DATE Type Precision (`ORA_DIFF_003`)**: Oracle `DATE` stores hours, minutes, and seconds. Postgres `DATE` truncates time unless mapped to `TIMESTAMP`.
5. **TRUNC and Date Functions (`ORA_DIFF_010`)**: Reversed arguments and dialect-specific formatting codes.

**Parity's Rule**: *The verifier decides, not the model. The transpiler or LLM proposes, but the 5 verification layers accept or reject.*

---

## Architecture

```mermaid
flowchart TD
    A[Source Oracle SQL] --> B[Parity Transpiler Engine]
    B -->|AST Rules: (+) Joins, Dual, Sysdate, Trunc| C[PostgreSQL SQL]
    C --> D[Verification Stack]
    
    subgraph D [5-Layer Verification Stack]
        L1[Layer 1: Target Compilation EXPLAIN]
        L2[Layer 2: Schema & Column Layout]
        L3[Layer 3: Row Count Parity]
        L4[Layer 4: Column Aggregates & Decimals 1e-9]
        L5[Layer 5: Row-Level Cryptographic Hashing]
        L1 --> L2 --> L3 --> L4 --> L5
    end
    
    D -->|Passed| E[Verified Migration Artifact]
    D -->|Mismatch Detected| F[Diagnostic Matcher & KB]
    F --> G[HTML Evidence Report & Audit Trail]
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

## Quickstart

### 1. Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Git

### 2. Installation
```powershell
# Clone and enter workspace
git clone <repo-url> Parity
cd Parity

# Install dependencies in editable mode
pip install -e .
```

### 3. Check System Readiness
```powershell
parity doctor
```

### 4. Start Dual-Database Sandbox (Oracle Free + Postgres 16)
```powershell
# Start Oracle 23 Free and PostgreSQL 16 containers with HR schema pre-loaded
docker compose up -d
```

### 5. Transpile Oracle SQL
```powershell
# Transpile single query or file
parity transpile src/parity/benchmark/corpus/08_outer_join_plus.sql
```

### 6. Run Autonomous Repair Loop (Phase 2)
```powershell
# Repair failing conversions using LLM + KB diagnostics with budget enforcement
parity repair src/parity/benchmark/corpus/02_nvl_coalesce.sql --provider mock
```

### 7. Analyze SQL Lineage & Object Complexity (Phase 2)
```powershell
# Extract dependencies, score complexity, and sort objects topologically
parity lineage src/parity/benchmark/corpus
```

### 8. Run 4-Way Ablation Study (Phase 2)
```powershell
# Compare baseline sqlglot vs AST rules vs +LLM vs +LLM+KB
parity ablation
```

### 9. Run Verification & Generate HTML Evidence Report
```powershell
parity verify src/parity/benchmark/corpus/01_simple_select.sql
```

---

## Security & Privacy Safeguards

- **Strict Read-Only Guard**: Destructive DDL and DML statements (`DROP`, `TRUNCATE`, `ALTER`, `DELETE`, `UPDATE`, `INSERT`, `GRANT`) are blocked before database execution.
- **Zero Raw Data to Models**: Raw row values are never transmitted to LLMs or external services. Only aggregate metrics, column names, and cryptographic bucket hashes are used.
- **Hard Cost Caps & Runaway Loop Protection**: Hard caps on attempts (max 3), per-object spend ($0.05 limit), and response caching to prevent runaway costs.
- **PII Redaction**: Literals and credentials are automatically stripped and masked.

---

## Project Structure

```
Parity/
├── src/parity/
│   ├── benchmark/         # Corpus queries, baseline runner, and ablation study
│   │   ├── corpus/        # 12+ Oracle dialect workload test cases
│   │   ├── runner.py      # Automated benchmark execution & pass rate logger
│   │   └── ablation.py    # 4-way ablation matrix runner
│   ├── kb/                # Knowledge Base
│   │   ├── dialect_differences.yaml  # 15+ cataloged Oracle vs Postgres differences
│   │   └── loader.py      # Search engine and error diagnostic matcher
│   ├── lineage/           # SQL dependency analysis & complexity scoring
│   │   ├── analyzer.py    # DDL/query dependency parser
│   │   ├── complexity.py  # Query complexity scoring (Simple -> Extreme)
│   │   └── topological.py # Kahn's algorithm topological execution ordering
│   ├── llm/               # Multi-provider LLM abstraction & cost tracker
│   │   ├── cost_tracker.py# Hard token limits, cost caps & runaway loop guards
│   │   ├── cache.py       # Persistent response caching
│   │   ├── prompts.py     # Privacy-first prompt templates (zero raw rows)
│   │   └── providers.py   # Mock, Ollama, and Hosted API connectors
│   ├── repair/            # Autonomous repair loop
│   │   └── engine.py      # Analyze -> Diagnose -> Propose -> Verify loop
│   ├── reporting/         # Modern HTML evidence audit report generator
│   ├── security/          # Read-only guards and PII redaction
│   ├── transpiler/        # AST transforms (Outer joins, SYSDATE, TRUNC, Dual, Concat)
│   ├── verifier/          # Layers 1-5 verification implementations
│   ├── cli.py             # Typer/Rich command line interface
│   ├── config.py          # Environment settings
│   └── db.py              # Dual Oracle & PostgreSQL execution connectors
├── docker/
│   ├── oracle/init/       # Oracle HR schema DDL and seed data
│   └── postgres/init/     # PostgreSQL HR schema DDL and seed data
├── tests/                 # Unit tests (Transpiler, Verifier, Security, KB, Lineage, Repair, LLM)
├── bench/results/         # Baseline and ablation study JSON logs
├── docker-compose.yml     # Local Oracle Free + Postgres services
├── DATA_SOURCES.md        # Licensing and data provenance
├── SEMANTIC_DIFFERENCES.md# Detailed dialect divergence catalog
├── parity.md              # Complete build roadmap
└── pyproject.toml         # PEP 621 package metadata
```

---

## License

This project is licensed under the [MIT License](LICENSE).
