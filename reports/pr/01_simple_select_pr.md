# feat(migration): Migrate Oracle `01_simple_select` to PostgreSQL

❌ **Verification Status**: `BLOCKED (VERIFICATION FAILED)`  
🌿 **Target Branch**: `parity/migrate-01_simple_select`  
📊 **Repair Attempts**: `3`  
💰 **LLM Cost**: `$0.00000`  
⏱️ **Verification Latency**: `0.1ms`  
📂 **Source File**: `01_simple_select.sql`

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



---

## 📄 SQL Comparison

### Source (Oracle SQL)
```sql
-- 01: Simple selection with projection and predicate
SELECT employee_id, first_name, last_name, salary
FROM employees
WHERE salary >= 10000
ORDER BY salary DESC, employee_id ASC;
```

### Transpiled Target (PostgreSQL SQL)
```sql
/* 01: Simple selection with projection and predicate */
SELECT
  employee_id,
  first_name,
  last_name,
  salary
FROM employees
WHERE
  salary >= 10000
ORDER BY
  salary DESC,
  employee_id ASC
```

---

## 📎 Audit Artifacts
- **Evidence Audit Report**: [View Full HTML Evidence Report](reports/output/01_simple_select_evidence.html)
- **Deterministic-First Guarantee**: Checked via Parity 5-Layer Stack.

*Generated automatically by Parity Migration Workflow.*
