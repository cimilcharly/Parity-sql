# feat(migration): Migrate Oracle `10_dept_salary_aggregates` to PostgreSQL

❌ **Verification Status**: `BLOCKED (VERIFICATION FAILED)`  
🌿 **Target Branch**: `parity/migrate-10_dept_salary_aggregates`  
📊 **Repair Attempts**: `3`  
💰 **LLM Cost**: `$0.00000`  
⏱️ **Verification Latency**: `0.1ms`  
📂 **Source File**: `10_dept_salary_aggregates.sql`

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
-- 10: Group by department with multiple numeric aggregates
SELECT department_id,
       COUNT(*) AS emp_count,
       MIN(salary) AS min_sal,
       MAX(salary) AS max_sal,
       ROUND(AVG(salary), 2) AS avg_sal,
       SUM(salary) AS total_sal
FROM employees
WHERE department_id IS NOT NULL
GROUP BY department_id
ORDER BY department_id;
```

### Transpiled Target (PostgreSQL SQL)
```sql
/* 10: Group by department with multiple numeric aggregates */
SELECT
  department_id,
  COUNT(*) AS emp_count,
  MIN(salary) AS min_sal,
  MAX(salary) AS max_sal,
  ROUND(CAST(AVG(salary) AS DECIMAL), 2) AS avg_sal,
  SUM(salary) AS total_sal
FROM employees
WHERE
  NOT department_id IS NULL
GROUP BY
  department_id
ORDER BY
  department_id
```

---

## 📎 Audit Artifacts
- **Evidence Audit Report**: [View Full HTML Evidence Report](reports/output/10_dept_salary_aggregates_evidence.html)
- **Deterministic-First Guarantee**: Checked via Parity 5-Layer Stack.

*Generated automatically by Parity Migration Workflow.*
