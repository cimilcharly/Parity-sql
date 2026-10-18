"""Golden-file regression tests verifying deterministic Oracle to PostgreSQL conversions."""

import pytest
from parity.plsql import PLSQLConverter
from parity.transpiler import Transpiler


@pytest.fixture
def transpiler():
    return Transpiler()


@pytest.fixture
def plsql_converter():
    return PLSQLConverter()


GOLDEN_SQL_CASES = [
    # 1. Simple select with column normalization
    (
        "SELECT employee_id, first_name FROM employees WHERE department_id = 10",
        "SELECT employee_id, first_name FROM employees WHERE department_id = 10",
    ),
    # 2. NVL -> COALESCE
    (
        "SELECT employee_id, NVL(commission_pct, 0) AS comm FROM employees",
        "SELECT employee_id, COALESCE(commission_pct, 0) AS comm FROM employees",
    ),
    # 3. Stripping FROM DUAL
    (
        "SELECT 100 * 2 FROM DUAL",
        "SELECT 100 * 2",
    ),
    # 4. SYSDATE -> CURRENT_TIMESTAMP
    (
        "SELECT SYSDATE FROM DUAL",
        "SELECT CURRENT_TIMESTAMP",
    ),
    # 5. TRUNC(date, 'MM') -> DATE_TRUNC('month', date)
    (
        "SELECT TRUNC(hire_date, 'MM') FROM employees",
        "SELECT DATE_TRUNC('month', hire_date) FROM employees",
    ),
    # 6. Legacy (+) Outer Join
    (
        "SELECT e.employee_id, d.department_name FROM employees e, departments d WHERE e.department_id = d.department_id(+)",
        "SELECT e.employee_id, d.department_name FROM employees AS e LEFT JOIN departments AS d ON e.department_id = d.department_id",
    ),
]


@pytest.mark.parametrize("oracle_sql, expected_pg_sql", GOLDEN_SQL_CASES)
def test_golden_sql_conversions(transpiler, oracle_sql, expected_pg_sql):
    result = transpiler.transpile(oracle_sql)
    target_sql = result.target_sql
    # Normalize whitespaces and quotes for robust comparison
    norm_result = " ".join(target_sql.replace('"', "").split()).upper()
    norm_expected = " ".join(expected_pg_sql.replace('"', "").split()).upper()
    assert norm_result == norm_expected


def test_golden_plsql_function_conversion(plsql_converter):
    oracle_fn = """
    CREATE OR REPLACE FUNCTION calc_bonus(p_salary NUMBER, p_rating NUMBER)
    RETURN NUMBER IS
        v_mult NUMBER := 1.0;
    BEGIN
        IF p_rating > 3 THEN
            v_mult := 1.5;
        END IF;
        RETURN p_salary * v_mult;
    END;
    """

    res = plsql_converter.convert(oracle_fn)
    assert res.success is True
    assert "RETURNS NUMERIC" in res.target_code
    assert "LANGUAGE plpgsql" in res.target_code
    assert "v_mult NUMERIC := 1.0;" in res.target_code
    assert "IF p_rating > 3 THEN" in res.target_code
    assert "RETURN p_salary * v_mult;" in res.target_code
