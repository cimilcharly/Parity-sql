# feat(migration): Migrate Oracle `03_decode_job_category` to PostgreSQL

❌ **Verification Status**: `BLOCKED (VERIFICATION FAILED)`  
🌿 **Target Branch**: `parity/migrate-03_decode_job_category`  
📊 **Repair Attempts**: `3`  
💰 **LLM Cost**: `$0.00000`  
⏱️ **Verification Latency**: `0.0ms`  
📂 **Source File**: `03_decode_job_category.sql`

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
-- 03: DECODE function categorization
SELECT employee_id, last_name, job_id,
       DECODE(job_id, 'AD_PRES', 'Executive', 'AD_VP', 'Executive', 'IT_PROG', 'Technical', 'General') AS role_tier
FROM employees
ORDER BY employee_id;
```

### Transpiled Target (PostgreSQL SQL)
```sql
/* 03: DECODE function categorization */
SELECT
  employee_id,
  last_name,
  job_id,
  CASE
    WHEN job_id = 'AD_PRES'
    THEN 'Executive'
    WHEN job_id = 'AD_VP'
    THEN 'Executive'
    WHEN job_id = 'IT_PROG'
    THEN 'Technical'
    ELSE 'General'
  END AS role_tier
FROM employees
ORDER BY
  employee_id
```

---

## 📎 Audit Artifacts
- **Evidence Audit Report**: [View Full HTML Evidence Report](reports/output/03_decode_job_category_evidence.html)
- **Deterministic-First Guarantee**: Checked via Parity 5-Layer Stack.

*Generated automatically by Parity Migration Workflow.*
