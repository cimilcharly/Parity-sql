# feat(migration): Migrate Oracle `12_nested_subquery_salary` to PostgreSQL

❌ **Verification Status**: `BLOCKED (VERIFICATION FAILED)`  
🌿 **Target Branch**: `parity/migrate-12_nested_subquery_salary`  
📊 **Repair Attempts**: `3`  
💰 **LLM Cost**: `$0.00000`  
⏱️ **Verification Latency**: `0.0ms`  
📂 **Source File**: `12_nested_subquery_salary.sql`

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
-- 12: Correlated nested subquery: Employees earning above their department's average
SELECT e.employee_id, e.last_name, e.salary, e.department_id
FROM employees e
WHERE e.salary > (
    SELECT AVG(sub.salary)
    FROM employees sub
    WHERE sub.department_id = e.department_id
)
ORDER BY e.department_id, e.salary DESC;
```

### Transpiled Target (PostgreSQL SQL)
```sql
/* 12: Correlated nested subquery: Employees earning above their department's average */
SELECT
  e.employee_id,
  e.last_name,
  e.salary,
  e.department_id
FROM employees AS e
WHERE
  e.salary > (
    SELECT
      AVG(sub.salary)
    FROM employees AS sub
    WHERE
      sub.department_id = e.department_id
  )
ORDER BY
  e.department_id,
  e.salary DESC
```

---

## 📎 Audit Artifacts
- **Evidence Audit Report**: [View Full HTML Evidence Report](reports/output/12_nested_subquery_salary_evidence.html)
- **Deterministic-First Guarantee**: Checked via Parity 5-Layer Stack.

*Generated automatically by Parity Migration Workflow.*
