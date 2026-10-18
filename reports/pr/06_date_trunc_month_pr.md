# feat(migration): Migrate Oracle `06_date_trunc_month` to PostgreSQL

❌ **Verification Status**: `BLOCKED (VERIFICATION FAILED)`  
🌿 **Target Branch**: `parity/migrate-06_date_trunc_month`  
📊 **Repair Attempts**: `3`  
💰 **LLM Cost**: `$0.00000`  
⏱️ **Verification Latency**: `0.1ms`  
📂 **Source File**: `06_date_trunc_month.sql`

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
- `ORA_DIFF_010`


---

## 📄 SQL Comparison

### Source (Oracle SQL)
```sql
-- 06: TRUNC on dates to group by month
SELECT TRUNC(hire_date, 'MM') AS hire_month,
       COUNT(*) AS num_hired,
       AVG(salary) AS avg_starting_salary
FROM employees
GROUP BY TRUNC(hire_date, 'MM')
ORDER BY hire_month;
```

### Transpiled Target (PostgreSQL SQL)
```sql
/* 06: TRUNC on dates to group by month */
SELECT
  DATE_TRUNC('month', hire_date) AS hire_month,
  COUNT(*) AS num_hired,
  AVG(salary) AS avg_starting_salary
FROM employees
GROUP BY
  DATE_TRUNC('month', hire_date)
ORDER BY
  hire_month
```

---

## 📎 Audit Artifacts
- **Evidence Audit Report**: [View Full HTML Evidence Report](reports/output/06_date_trunc_month_evidence.html)
- **Deterministic-First Guarantee**: Checked via Parity 5-Layer Stack.

*Generated automatically by Parity Migration Workflow.*
