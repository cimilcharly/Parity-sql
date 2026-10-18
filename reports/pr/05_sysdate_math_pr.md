# feat(migration): Migrate Oracle `05_sysdate_math` to PostgreSQL

❌ **Verification Status**: `BLOCKED (VERIFICATION FAILED)`  
🌿 **Target Branch**: `parity/migrate-05_sysdate_math`  
📊 **Repair Attempts**: `3`  
💰 **LLM Cost**: `$0.00000`  
⏱️ **Verification Latency**: `0.1ms`  
📂 **Source File**: `05_sysdate_math.sql`

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
- `ORA_DIFF_009`


---

## 📄 SQL Comparison

### Source (Oracle SQL)
```sql
-- 05: SYSDATE reference and date tenure calculation
SELECT employee_id, last_name, hire_date,
       ROUND((SYSDATE - hire_date) / 365.25, 2) AS tenure_years
FROM employees
WHERE hire_date < TO_DATE('2006-01-01', 'YYYY-MM-DD')
ORDER BY employee_id;
```

### Transpiled Target (PostgreSQL SQL)
```sql
/* 05: SYSDATE reference and date tenure calculation */
SELECT
  employee_id,
  last_name,
  hire_date,
  ROUND(
    CAST(CAST((
      CURRENT_TIMESTAMP - hire_date
    ) AS DOUBLE PRECISION) / 365.25 AS DECIMAL),
    2
  ) AS tenure_years
FROM employees
WHERE
  hire_date < TO_DATE('2006-01-01', 'YYYY-MM-DD')
ORDER BY
  employee_id
```

---

## 📎 Audit Artifacts
- **Evidence Audit Report**: [View Full HTML Evidence Report](reports/output/05_sysdate_math_evidence.html)
- **Deterministic-First Guarantee**: Checked via Parity 5-Layer Stack.

*Generated automatically by Parity Migration Workflow.*
