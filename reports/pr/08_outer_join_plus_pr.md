# feat(migration): Migrate Oracle `08_outer_join_plus` to PostgreSQL

❌ **Verification Status**: `BLOCKED (VERIFICATION FAILED)`  
🌿 **Target Branch**: `parity/migrate-08_outer_join_plus`  
📊 **Repair Attempts**: `3`  
💰 **LLM Cost**: `$0.00000`  
⏱️ **Verification Latency**: `0.1ms`  
📂 **Source File**: `08_outer_join_plus.sql`

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
- `ORA_DIFF_007`


---

## 📄 SQL Comparison

### Source (Oracle SQL)
```sql
-- 08: Legacy Oracle (+) outer join syntax
SELECT d.department_name, e.last_name, e.salary
FROM departments d, employees e
WHERE d.department_id = e.department_id(+)
ORDER BY d.department_name, e.last_name;
```

### Transpiled Target (PostgreSQL SQL)
```sql
/* 08: Legacy Oracle  outer join syntax */
SELECT
  d.department_name,
  e.last_name,
  e.salary
FROM departments AS d
LEFT JOIN employees AS e
  ON d.department_id = e.department_id
ORDER BY
  d.department_name,
  e.last_name
```

---

## 📎 Audit Artifacts
- **Evidence Audit Report**: [View Full HTML Evidence Report](reports/output/08_outer_join_plus_evidence.html)
- **Deterministic-First Guarantee**: Checked via Parity 5-Layer Stack.

*Generated automatically by Parity Migration Workflow.*
