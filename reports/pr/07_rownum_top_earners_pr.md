# feat(migration): Migrate Oracle `07_rownum_top_earners` to PostgreSQL

❌ **Verification Status**: `BLOCKED (VERIFICATION FAILED)`  
🌿 **Target Branch**: `parity/migrate-07_rownum_top_earners`  
📊 **Repair Attempts**: `3`  
💰 **LLM Cost**: `$0.00000`  
⏱️ **Verification Latency**: `0.0ms`  
📂 **Source File**: `07_rownum_top_earners.sql`

---

> **MERGE POLICY**: ⛔ **DO NOT MERGE**. Verification failed or unsupported constructs detected.

---

## 🔍 Semantic Verification Audit Trail

| Verification Layer | Check Type | Status |
|---|---|---|
| **Layer 1** | Target PostgreSQL Query Plan Compilation (`EXPLAIN`) | ⚠️ CHECK REPORT |
| **Layer 2** | Schema Column Count, Types & Projection Order | ⚠️ CHECK REPORT |
| **Layer 3** | Exact Row Count Cardinality Parity | ⚠️ CHECK REPORT |
| **Layer 4** | Column Aggregates (Nulls, Sums, Medians $\le 10^-9$) | ⚠️ CHECK REPORT |
| **Layer 5** | Row-Level Cryptographic SHA-256 Multiset Hashing | ⚠️ CHECK REPORT |


### 🧠 Applied Knowledge Base Context
- `ORA_DIFF_006`


---

## 📄 SQL Comparison

### Source (Oracle SQL)
```sql
-- 07: ROWNUM filtering for top earners
SELECT * FROM (
    SELECT employee_id, last_name, salary
    FROM employees
    ORDER BY salary DESC
)
WHERE ROWNUM <= 3;
```

### Transpiled Target (PostgreSQL SQL)
```sql
/* 07: ROWNUM filtering for top earners */
SELECT
  *
FROM (
  SELECT
    employee_id,
    last_name,
    salary
  FROM employees
  ORDER BY
    salary DESC
)
WHERE
  ROWNUM <= 3
```

---

## 📎 Audit Artifacts
- **Evidence Audit Report**: [View Full HTML Evidence Report](reports/output/07_rownum_top_earners_evidence.html)
- **Deterministic-First Guarantee**: Checked via Parity 5-Layer Stack.

*Generated automatically by Parity Migration Workflow.*
