"""Benchmark Corpus Generator for 500+ Enterprise Oracle SQL and PL/SQL Objects."""

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class BenchmarkObject:
    """Represents a benchmark test case."""
    id: str
    name: str
    category: str
    complexity_score: int
    complexity_tier: str
    is_plsql: bool
    source_sql: str
    expected_outcome: str  # "PASS", "HUMAN_REVIEW", "FAIL"
    expected_blocker: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "complexity_score": self.complexity_score,
            "complexity_tier": self.complexity_tier,
            "is_plsql": self.is_plsql,
            "source_sql": self.source_sql,
            "expected_outcome": self.expected_outcome,
            "expected_blocker": self.expected_blocker,
            "tags": self.tags,
        }


class BenchmarkCorpusGenerator:
    """Generates 500+ diverse enterprise Oracle SQL & PL/SQL objects across 10 categories."""

    CATEGORIES = [
        "1. Base Queries & Filters",
        "2. Joins & Oracle (+) Outer Joins",
        "3. Window & Analytic Functions",
        "4. Aggregations & Grouping",
        "5. Date & Time Arithmetic",
        "6. String & Null Coalescing",
        "7. Hierarchical & Recursive Queries",
        "8. CTEs, Subqueries & Set Operators",
        "9. PL/SQL Functions & Procedures",
        "10. Enterprise Edge Cases & Blockers",
    ]

    def generate_all_500(self) -> List[BenchmarkObject]:
        """Generate all 500 objects across the 10 distinct categories (50 each)."""
        objects: List[BenchmarkObject] = []
        objects.extend(self._generate_cat1_base_queries())        # 50
        objects.extend(self._generate_cat2_joins())               # 50
        objects.extend(self._generate_cat3_window_analytics())    # 50
        objects.extend(self._generate_cat4_aggregates())          # 50
        objects.extend(self._generate_cat5_date_arithmetic())     # 50
        objects.extend(self._generate_cat6_string_nulls())        # 50
        objects.extend(self._generate_cat7_hierarchical())        # 50
        objects.extend(self._generate_cat8_subqueries_sets())     # 50
        objects.extend(self._generate_cat9_plsql())               # 50
        objects.extend(self._generate_cat10_edge_cases())         # 50
        return objects

    def _generate_cat1_base_queries(self) -> List[BenchmarkObject]:
        """Category 1: 50 Base Queries & Projections."""
        items = []
        departments = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110]
        jobs = ["IT_PROG", "SA_REP", "ST_CLERK", "HR_REP", "AC_ACCOUNT", "MK_MAN", "FI_MGR", "PU_CLERK"]
        
        for i in range(1, 51):
            dep = departments[(i - 1) % len(departments)]
            job = jobs[(i - 1) % len(jobs)]
            min_sal = 2000 + (i * 150)
            max_sal = min_sal + 5000
            
            sql = f"""SELECT 
    employee_id,
    first_name,
    last_name,
    email,
    salary,
    department_id
FROM employees
WHERE department_id = {dep}
  AND job_id = '{job}'
  AND salary BETWEEN {min_sal} AND {max_sal}
ORDER BY salary DESC"""
            
            items.append(BenchmarkObject(
                id=f"CAT1_{i:03d}",
                name=f"base_query_dept_{dep}_job_{job.lower()}_{i:02d}",
                category="1. Base Queries & Filters",
                complexity_score=2 if i % 2 == 0 else 3,
                complexity_tier="Simple",
                is_plsql=False,
                source_sql=sql.strip(),
                expected_outcome="PASS",
                tags=["select", "filter", "between", "order_by"],
            ))
        return items

    def _generate_cat2_joins(self) -> List[BenchmarkObject]:
        """Category 2: 50 Joins and Oracle (+) Outer Joins."""
        items = []
        for i in range(1, 51):
            if i <= 25:
                # Oracle (+) outer join
                sql = f"""SELECT 
    e.employee_id,
    e.first_name,
    e.last_name,
    e.salary,
    d.department_name,
    l.city
FROM employees e,
     departments d,
     locations l
WHERE e.department_id = d.department_id(+)
  AND d.location_id = l.location_id(+)
  AND e.salary > {3000 + (i * 100)}"""
                tier = "Moderate"
                score = 5
                tags = ["outer_join", "oracle_plus_syntax", "multi_table"]
            else:
                # Multi-table inner/outer ANSI mix
                sql = f"""SELECT 
    e.employee_id,
    e.first_name || ' ' || e.last_name AS full_name,
    d.department_name,
    j.job_title,
    jh.start_date,
    jh.end_date
FROM employees e
JOIN departments d ON e.department_id = d.department_id
JOIN jobs j ON e.job_id = j.job_id
LEFT JOIN job_history jh ON e.employee_id = jh.employee_id
WHERE e.department_id IN (10, 20, 30, 40, 50, 60, 70, 80)
ORDER BY e.employee_id"""
                tier = "Moderate"
                score = 6
                tags = ["join", "job_history", "departments"]

            items.append(BenchmarkObject(
                id=f"CAT2_{i:03d}",
                name=f"join_object_pattern_{i:02d}",
                category="2. Joins & Oracle (+) Outer Joins",
                complexity_score=score,
                complexity_tier=tier,
                is_plsql=False,
                source_sql=sql.strip(),
                expected_outcome="PASS",
                tags=tags,
            ))
        return items

    def _generate_cat3_window_analytics(self) -> List[BenchmarkObject]:
        """Category 3: 50 Window and Analytic Functions."""
        items = []
        for i in range(1, 51):
            modulo = i % 5
            if modulo == 0:
                fn = "ROW_NUMBER() OVER (PARTITION BY department_id ORDER BY salary DESC) AS rank_in_dept"
            elif modulo == 1:
                fn = "DENSE_RANK() OVER (PARTITION BY job_id ORDER BY salary DESC) AS salary_dense_rank"
            elif modulo == 2:
                fn = "AVG(salary) OVER (PARTITION BY department_id) AS dept_avg_sal, salary - AVG(salary) OVER (PARTITION BY department_id) AS diff_from_avg"
            elif modulo == 3:
                fn = "LAG(salary, 1, 0) OVER (PARTITION BY department_id ORDER BY hire_date) AS prev_employee_salary"
            else:
                fn = "SUM(salary) OVER (PARTITION BY department_id ORDER BY hire_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_dept_total"

            sql = f"""SELECT 
    employee_id,
    first_name,
    last_name,
    department_id,
    job_id,
    salary,
    hire_date,
    {fn}
FROM employees
WHERE salary > {2500 + (i * 50)}"""

            items.append(BenchmarkObject(
                id=f"CAT3_{i:03d}",
                name=f"analytic_window_pattern_{i:02d}",
                category="3. Window & Analytic Functions",
                complexity_score=7 if i % 2 == 0 else 6,
                complexity_tier="Complex",
                is_plsql=False,
                source_sql=sql.strip(),
                expected_outcome="PASS",
                tags=["window_function", "partition_by", "analytic"],
            ))
        return items

    def _generate_cat4_aggregates(self) -> List[BenchmarkObject]:
        """Category 4: 50 Aggregations and Grouping Queries."""
        items = []
        for i in range(1, 51):
            having_threshold = 3000 + (i * 120)
            sql = f"""SELECT 
    department_id,
    job_id,
    COUNT(employee_id) AS total_headcount,
    COUNT(DISTINCT manager_id) AS distinct_managers,
    ROUND(AVG(salary), 2) AS average_salary,
    MIN(salary) AS minimum_salary,
    MAX(salary) AS maximum_salary,
    SUM(salary) AS total_payroll
FROM employees
WHERE department_id IS NOT NULL
GROUP BY department_id, job_id
HAVING AVG(salary) >= {having_threshold}
ORDER BY department_id, total_payroll DESC"""

            items.append(BenchmarkObject(
                id=f"CAT4_{i:03d}",
                name=f"aggregate_dept_job_summary_{i:02d}",
                category="4. Aggregations & Grouping",
                complexity_score=5,
                complexity_tier="Moderate",
                is_plsql=False,
                source_sql=sql.strip(),
                expected_outcome="PASS",
                tags=["group_by", "having", "count_distinct", "aggregates"],
            ))
        return items

    def _generate_cat5_date_arithmetic(self) -> List[BenchmarkObject]:
        """Category 5: 50 Date & Time Arithmetic Queries."""
        items = []
        for i in range(1, 51):
            offset_days = (i * 7)
            trunc_unit = "'MM'" if i % 2 == 0 else "'YYYY'"
            sql = f"""SELECT 
    employee_id,
    first_name,
    last_name,
    hire_date,
    TRUNC(hire_date, {trunc_unit}) AS hire_period_start,
    SYSDATE AS current_system_time,
    SYSDATE - hire_date AS tenure_days,
    SYSDATE + {offset_days} AS future_checkpoint_date
FROM employees
WHERE hire_date <= SYSDATE - {offset_days}
ORDER BY hire_date ASC"""

            items.append(BenchmarkObject(
                id=f"CAT5_{i:03d}",
                name=f"date_math_tenure_calc_{i:02d}",
                category="5. Date & Time Arithmetic",
                complexity_score=4,
                complexity_tier="Moderate",
                is_plsql=False,
                source_sql=sql.strip(),
                expected_outcome="PASS",
                tags=["sysdate", "trunc_date", "date_arithmetic"],
            ))
        return items

    def _generate_cat6_string_nulls(self) -> List[BenchmarkObject]:
        """Category 6: 50 String and Null Coalescing Queries."""
        items = []
        for i in range(1, 51):
            default_comm = (i % 5) * 0.05
            sql = f"""SELECT 
    employee_id,
    first_name || ' ' || last_name AS full_name,
    NVL(commission_pct, {default_comm}) AS normalized_commission,
    DECODE(department_id, 
        10, 'Executive Suite', 
        20, 'Marketing Division', 
        50, 'Shipping & Logistics', 
        60, 'Engineering Tech', 
        80, 'Global Sales', 
        'General Operations') AS department_category,
    NVL2(commission_pct, salary * (1 + commission_pct), salary) AS total_effective_comp,
    RPAD(SUBSTR(first_name, 1, 1) || '. ' || last_name, 30, ' ') AS formatted_name
FROM employees
WHERE salary > {2000 + (i * 80)}"""

            items.append(BenchmarkObject(
                id=f"CAT6_{i:03d}",
                name=f"string_null_semantics_{i:02d}",
                category="6. String & Null Coalescing",
                complexity_score=5,
                complexity_tier="Moderate",
                is_plsql=False,
                source_sql=sql.strip(),
                expected_outcome="PASS",
                tags=["nvl", "nvl2", "decode", "string_concat", "rpad"],
            ))
        return items

    def _generate_cat7_hierarchical(self) -> List[BenchmarkObject]:
        """Category 7: 50 Hierarchical & Recursive Queries."""
        items = []
        for i in range(1, 51):
            root_mgr = 100 + (i % 3) * 2
            sql = f"""SELECT 
    employee_id,
    first_name,
    last_name,
    manager_id,
    LEVEL AS hierarchy_depth,
    SYS_CONNECT_BY_PATH(last_name, ' / ') AS management_chain
FROM employees
START WITH manager_id = {root_mgr} OR manager_id IS NULL
CONNECT BY PRIOR employee_id = manager_id
ORDER SIBLINGS BY last_name"""

            items.append(BenchmarkObject(
                id=f"CAT7_{i:03d}",
                name=f"hierarchical_org_chart_{i:02d}",
                category="7. Hierarchical & Recursive Queries",
                complexity_score=8,
                complexity_tier="Complex",
                is_plsql=False,
                source_sql=sql.strip(),
                expected_outcome="PASS",
                tags=["connect_by", "start_with", "sys_connect_by_path", "hierarchy"],
            ))
        return items

    def _generate_cat8_subqueries_sets(self) -> List[BenchmarkObject]:
        """Category 8: 50 CTEs, Subqueries and Set Operators."""
        items = []
        for i in range(1, 51):
            if i % 2 == 0:
                # CTE with Correlated Subquery
                sql = f"""WITH dept_benchmarks AS (
    SELECT department_id, AVG(salary) AS dept_avg_sal
    FROM employees
    GROUP BY department_id
)
SELECT 
    e.employee_id,
    e.first_name,
    e.last_name,
    e.salary,
    b.dept_avg_sal,
    (e.salary - b.dept_avg_sal) AS delta_from_benchmark
FROM employees e
JOIN dept_benchmarks b ON e.department_id = b.department_id
WHERE e.salary > b.dept_avg_sal + {i * 50}"""
            else:
                # Set Operator (MINUS / EXCEPT pattern)
                sql = f"""SELECT employee_id, first_name, last_name, department_id
FROM employees
WHERE department_id IN (10, 20, 30, 50, 80)
MINUS
SELECT employee_id, first_name, last_name, department_id
FROM employees
WHERE salary < {3000 + (i * 100)}"""

            items.append(BenchmarkObject(
                id=f"CAT8_{i:03d}",
                name=f"subquery_set_operator_{i:02d}",
                category="8. CTEs, Subqueries & Set Operators",
                complexity_score=7,
                complexity_tier="Complex",
                is_plsql=False,
                source_sql=sql.strip(),
                expected_outcome="PASS",
                tags=["cte", "subquery", "minus", "set_operator"],
            ))
        return items

    def _generate_cat9_plsql(self) -> List[BenchmarkObject]:
        """Category 9: 50 PL/SQL Functions & Stored Procedures."""
        items = []
        for i in range(1, 51):
            func_id = f"calc_payout_tax_tier_{i:02d}"
            sql = f"""CREATE OR REPLACE FUNCTION {func_id}(
    p_emp_id IN NUMBER,
    p_rate IN NUMBER
) RETURN NUMBER IS
    v_salary NUMBER(10, 2);
    v_tax NUMBER(10, 2);
BEGIN
    SELECT salary INTO v_salary FROM employees WHERE employee_id = p_emp_id;
    IF v_salary IS NULL THEN
        RETURN 0;
    ELSIF v_salary > {5000 + (i * 100)} THEN
        v_tax := v_salary * p_rate * 1.15;
    ELSE
        v_tax := v_salary * p_rate;
    END IF;
    RETURN ROUND(v_tax, 2);
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN -1;
END;"""

            items.append(BenchmarkObject(
                id=f"CAT9_{i:03d}",
                name=func_id,
                category="9. PL/SQL Functions & Procedures",
                complexity_score=6,
                complexity_tier="Moderate",
                is_plsql=True,
                source_sql=sql.strip(),
                expected_outcome="PASS",
                tags=["plsql", "function", "create_or_replace", "exception_block"],
            ))
        return items

    def _generate_cat10_edge_cases(self) -> List[BenchmarkObject]:
        """Category 10: 50 Enterprise Edge Cases & Deliberate Blocker Probes."""
        items = []
        for i in range(1, 51):
            case_type = i % 5
            if case_type == 0:
                # Autonomous transaction (PL/SQL Blocker)
                sql = f"""CREATE OR REPLACE PROCEDURE audit_trans_logger_{i:02d}(p_msg IN VARCHAR2) IS
    PRAGMA AUTONOMOUS_TRANSACTION;
BEGIN
    INSERT INTO audit_log (event_time, message) VALUES (SYSDATE, p_msg);
    COMMIT;
END;"""
                expected = "HUMAN_REVIEW"
                blocker = "PRAGMA AUTONOMOUS_TRANSACTION"
                tier = "Extreme"
                score = 10
            elif case_type == 1:
                # BULK COLLECT (PL/SQL Blocker)
                sql = f"""CREATE OR REPLACE PROCEDURE bulk_dept_fetcher_{i:02d}(p_dept IN NUMBER) IS
    TYPE emp_list_t IS TABLE OF employees%ROWTYPE;
    v_emps emp_list_t;
BEGIN
    SELECT * BULK COLLECT INTO v_emps FROM employees WHERE department_id = p_dept;
END;"""
                expected = "HUMAN_REVIEW"
                blocker = "BULK COLLECT"
                tier = "Extreme"
                score = 10
            elif case_type == 2:
                # PIPE ROW pipelined function (PL/SQL Blocker)
                sql = f"""CREATE OR REPLACE FUNCTION stream_salaries_{i:02d} RETURN emp_num_table PIPELINED IS
BEGIN
    FOR r IN (SELECT salary FROM employees) LOOP
        PIPE ROW(r.salary);
    END LOOP;
    RETURN;
END;"""
                expected = "HUMAN_REVIEW"
                blocker = "PIPE ROW (Pipelined Function)"
                tier = "Extreme"
                score = 9
            elif case_type == 3:
                # Empty string edge case (SQL Pass with semantic rewrite)
                sql = f"""SELECT employee_id, first_name, commission_pct
FROM employees
WHERE commission_pct IS NULL OR commission_pct = '' OR first_name != ''"""
                expected = "PASS"
                blocker = None
                tier = "Moderate"
                score = 6
            else:
                # DUAL scalar expression with ROWNUM
                sql = f"""SELECT employee_id, salary, ROWNUM AS rank_num
FROM (
    SELECT employee_id, salary FROM employees ORDER BY salary DESC
)
WHERE ROWNUM <= {i}"""
                expected = "PASS"
                blocker = None
                tier = "Moderate"
                score = 5

            items.append(BenchmarkObject(
                id=f"CAT10_{i:03d}",
                name=f"edge_case_probe_{i:02d}",
                category="10. Enterprise Edge Cases & Blockers",
                complexity_score=score,
                complexity_tier=tier,
                is_plsql=case_type in (0, 1, 2),
                source_sql=sql.strip(),
                expected_outcome=expected,
                expected_blocker=blocker,
                tags=["edge_case", "blocker_probe", "static_analysis"],
            ))
        return items


corpus_generator = BenchmarkCorpusGenerator()
