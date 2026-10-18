# Parity Enterprise Pilot Migration Proposal

**Prepared For:** Enterprise Data Engineering & Database Architecture Teams  
**Engagement Type:** Fixed-Fee Zero-Risk Pilot Migration  
**Target Dialects:** Oracle SQL & PL/SQL &rarr; PostgreSQL (or AWS Aurora / AlloyDB)  
**Deliverable:** 200–500 Fully Transpiled & Verified Database Objects with Mathematical Parity Proof

---

## 1. Executive Summary

Migrating mission-critical enterprise database workloads from Oracle to PostgreSQL typically stalls during integration and validation testing. Traditional tools transpile SQL syntax but leave data teams with months of manual data reconciliation.

**Parity** solves this bottleneck through **deterministic-first transpilation paired with a 5-layer mathematical verification stack**. 

This pilot converts and validates **200 to 500 of your real-world Oracle SQL queries, views, and PL/SQL functions** under a fixed-timeline, zero-risk framework. Every delivered object includes an audit-ready HTML evidence report and an atomic Git Pull Request.

---

## 2. Pilot Scope & Workload Profile

| Parameter | Pilot Specification |
|---|---|
| **Workload Size** | 200 to 500 database objects (Views, complex SQL queries, analytical queries, PL/SQL functions) |
| **Source Database** | Oracle Database (11g, 12c, 19c, 21c, or 23ai) |
| **Target Database** | PostgreSQL (v14, v15, v16, v17), AWS Aurora PostgreSQL, GCP AlloyDB, or Azure PostgreSQL |
| **Complexity Distribution** | Minimum 40% Moderate/Complex objects (analytic functions, hierarchical CTEs, multi-table joins) |
| **Timeline** | 2 to 3 weeks from receipt of schema & benchmark corpus |

---

## 3. Measurable Success Metrics (Agreed SLA)

| Metric | Target SLA | Verification Method |
|---|---|---|
| **Automated Verified Pass Rate** | &ge; 95.0% | Passes all 5 verification layers (Compile, Schema, Row Count, Statistical Aggregates, and Row Hashing) |
| **Mathematical Tolerance** | &epsilon; < 10<sup>-9</sup> | Floating point and numeric columns match Oracle within 1e-9; exact integer & date equality |
| **Human Review Rate** | &le; 5.0% | Only explicit unsupported procedural constructs (e.g. autonomous transactions) flagged for manual refactoring |
| **Zero Raw Data Leakage** | 100% Guaranteed | No raw customer data or PII ever transmitted to external APIs or language models |

---

## 4. Deliverables

At the conclusion of the pilot, your engineering team receives:

1. **Production-Ready PostgreSQL DDL & SQL Repository**: Clean, idiomatic PostgreSQL code organized by schema and dependency order.
2. **Per-Object Evidence Audit Reports (HTML)**: Interactive audit documents showing:
   - Source Oracle SQL vs Target PostgreSQL SQL
   - Results of all 5 verification layers
   - Exact row count and column aggregate comparisons
   - Applied AST transform rules and audit log timestamps
3. **Executive Summary Dashboard**: High-level telemetry covering pass rates, complexity distribution, and compute costs.
4. **Automated CI/CD Workflow**: Pinned GitHub Actions / GitLab CI pipeline to run continuous regression verification as your database evolves.
5. **Architectural Remediation Guide**: Specific refactoring blueprints for any flagged PL/SQL procedures.

---

## 5. Security & Data Governance Guarantees

- **Read-Only Access**: Parity operates strictly under read-only database credentials with transaction rollback.
- **Air-Gapped & Local Deployment**: Parity runs entirely inside your VPC, on-premise infrastructure, or air-gapped Docker containers.
- **PII & Credential Redaction**: All SQL literals, passwords, and identifiers are scrubbed and anonymized before any internal diagnostic processing.
- **Tamper-Evident Audit Logging**: Every prompt, token metric, and verification check is logged to an immutable JSONL audit file with SHA-256 hashes.

---

## 6. Pilot Timeline & Weekly Milestones

```
Week 1: Ingestion & Baseline
├── Day 1-2: Setup secure VPC access & schema metadata extraction
├── Day 3-4: Dependency lineage graph & topological ordering
└── Day 5: Baseline transpilation run & initial pass rate calculation

Week 2: Autonomous Repair & Verification
├── Day 6-8: 5-layer verification execution on staging databases
├── Day 9-10: Autonomous repair loop for dialect divergence
└── Day 11: Flagging and remediation documentation for unsupported PL/SQL

Week 3: Final Delivery & Engineering Handover
├── Day 12-13: Generation of per-object HTML evidence reports & Git PRs
├── Day 14: Executive summary presentation & technical walkthrough
└── Day 15: CI/CD test harness integration handover
```

---

## 7. Commercial Terms & Pricing

- **Fixed Pilot Fee**: Fixed-price engagement (or complimentary for qualified enterprise design partners with >2,000 Oracle database objects).
- **Next Steps**: Contact the Parity Engineering team at `contact@parity-sql.dev` to schedule a 30-minute technical discovery call and sample object evaluation.
