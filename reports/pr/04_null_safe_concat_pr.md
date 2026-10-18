# feat(migration): Migrate Oracle `04_null_safe_concat` to PostgreSQL

❌ **Verification Status**: `BLOCKED (VERIFICATION FAILED)`  
🌿 **Target Branch**: `parity/migrate-04_null_safe_concat`  
📊 **Repair Attempts**: `3`  
💰 **LLM Cost**: `$0.00000`  
⏱️ **Verification Latency**: `0.0ms`  
📂 **Source File**: `04_null_safe_concat.sql`

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
-- 04: String concatenation with potential NULL values
SELECT employee_id, first_name || ' ' || last_name AS full_name,
       first_name || ' (' || phone_number || ')' AS contact_card
FROM employees
ORDER BY employee_id;
```

### Transpiled Target (PostgreSQL SQL)
```sql
/* 04: String concatenation with potential NULL values */
SELECT
  employee_id,
  first_name || ' ' || last_name AS full_name,
  first_name || ' (' || phone_number || ')' AS contact_card
FROM employees
ORDER BY
  employee_id
```

---

## 📎 Audit Artifacts
- **Evidence Audit Report**: [View Full HTML Evidence Report](reports/output/04_null_safe_concat_evidence.html)
- **Deterministic-First Guarantee**: Checked via Parity 5-Layer Stack.

*Generated automatically by Parity Migration Workflow.*
