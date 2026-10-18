# Data Sources and Licensing

Parity is designed with a strict "security-first, zero-leak" methodology. The datasets and schemas used for baseline validation and benchmarking adhere to the following licenses and source guidelines:

---

## 1. Oracle Human Resources (HR) Sample Schema
- **Description**: Standard relational enterprise schema modeling departments, employees, jobs, job history, locations, and countries.
- **Source**: Oracle Database Sample Schemas ([Oracle GitHub Repository](https://github.com/oracle-samples/db-sample-schemas)).
- **License**: Oracle Free Use Terms / Sample Code License.
- **Permitted Use**: Development, education, automated testing, and migration verification.
- **PII Status**: 100% synthetic fictitious employee data.

---

## 2. TPC-H & TPC-DS Dialect Benchmarks
- **Description**: Decision-support SQL queries and analytical workloads adapted to test complex Oracle constructs (hierarchical queries, analytic window functions, nested subqueries, date math).
- **Source**: Transaction Processing Performance Council (TPC).
- **License**: TPC benchmark query specifications (adapted under fair-use for academic & transpilation benchmark testing).
- **Attribution**: TPC-H and TPC-DS are registered trademarks of the Transaction Processing Performance Council. The queries used in Parity are derivative dialect test templates, not official audited TPC results.

---

## 3. Synthetic Edge-Case Generator (Faker)
- **Description**: Boundary conditions, extreme edge cases, NULL vs empty string ambiguities, leap days, unicode string padding, floating point rounding, and temporal boundaries.
- **Source**: Generated procedurally using `Faker` (Python).
- **License**: MIT License.
- **PII Status**: Completely synthetic.

---

## 4. Proprietary Data Policy
- **Strict Prohibition**: No real customer SQL, proprietary database dumps, or real corporate schemas are permitted in public benchmark corpora or repositories.
- **Redaction**: All LLM prompts and evidence reports pass through an automated PII/value redactor before leaving the local sandbox.
