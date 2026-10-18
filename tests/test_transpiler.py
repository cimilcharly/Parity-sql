"""Unit tests for Oracle -> PostgreSQL transpilation and custom AST rewrite rules."""

import pytest
from parity.transpiler import Transpiler


@pytest.fixture
def transpiler():
    return Transpiler(use_parity_rules=True)


def test_transpile_simple_select(transpiler):
    oracle_sql = "SELECT employee_id, first_name FROM employees WHERE salary > 5000"
    res = transpiler.transpile(oracle_sql)
    assert res.success is True
    assert "SELECT" in res.target_sql.upper()
    assert "salary > 5000" in res.target_sql


def test_transpile_nvl_coalesce(transpiler):
    oracle_sql = "SELECT NVL(commission_pct, 0) FROM employees"
    res = transpiler.transpile(oracle_sql)
    assert res.success is True
    assert "COALESCE" in res.target_sql.upper()


def test_transpile_decode(transpiler):
    oracle_sql = "SELECT DECODE(dept_id, 10, 'A', 20, 'B', 'C') FROM departments"
    res = transpiler.transpile(oracle_sql)
    assert res.success is True
    assert "CASE" in res.target_sql.upper()


def test_transpile_sysdate(transpiler):
    oracle_sql = "SELECT SYSDATE FROM dual"
    res = transpiler.transpile(oracle_sql)
    assert res.success is True
    assert "CURRENT_TIMESTAMP" in res.target_sql.upper()
    # Redundant DUAL is stripped
    assert "DUAL" not in res.target_sql.upper()


def test_transpile_strip_from_dual(transpiler):
    oracle_sql = "SELECT 1 + 1 FROM DUAL"
    res = transpiler.transpile(oracle_sql)
    assert res.success is True
    assert "DUAL" not in res.target_sql.upper()


def test_transpile_trunc_date(transpiler):
    oracle_sql = "SELECT TRUNC(hire_date, 'MM') FROM employees"
    res = transpiler.transpile(oracle_sql)
    assert res.success is True
    assert "date_trunc" in res.target_sql.lower()
    assert "month" in res.target_sql.lower()


def test_transpile_outer_join_plus(transpiler):
    oracle_sql = "SELECT d.department_name, e.last_name FROM departments d, employees e WHERE d.department_id = e.department_id(+)"
    res = transpiler.transpile(oracle_sql)
    assert res.success is True
    assert "LEFT JOIN" in res.target_sql.upper()
    assert "ON d.department_id = e.department_id" in res.target_sql
    assert "ORA_RULE_005" in res.applied_rules
