"""Unit tests for Oracle PL/SQL to PostgreSQL PL/pgSQL transpiler."""

import pytest
from parity.plsql import PLSQLConstructType, PLSQLConverter


@pytest.fixture
def converter():
    return PLSQLConverter()


def test_convert_simple_function(converter):
    oracle_code = """
    CREATE OR REPLACE FUNCTION get_annual_salary (
        p_emp_id IN NUMBER,
        p_bonus IN NUMBER
    ) RETURN NUMBER IS
        v_sal NUMBER(10, 2);
        v_total NUMBER(10, 2);
    BEGIN
        SELECT salary INTO v_sal FROM employees WHERE employee_id = p_emp_id;
        v_total := (v_sal * 12) + NVL(p_bonus, 0);
        DBMS_OUTPUT.PUT_LINE('Calculated total');
        RETURN v_total;
    END get_annual_salary;
    """

    res = converter.convert(oracle_code)
    assert res.success is True
    assert res.object_name == "get_annual_salary"
    assert res.object_type == PLSQLConstructType.FUNCTION
    assert "RETURNS NUMERIC" in res.target_code
    assert "LANGUAGE plpgsql" in res.target_code
    assert "v_sal NUMERIC(10, 2);" in res.target_code
    assert "COALESCE(p_bonus, 0)" in res.target_code
    assert "RAISE NOTICE '%', 'Calculated total';" in res.target_code
    assert "RETURN v_total;" in res.target_code


def test_convert_procedure_with_out_param(converter):
    oracle_code = """
    CREATE OR REPLACE PROCEDURE calculate_tax (
        p_emp_id IN NUMBER,
        p_tax_rate IN NUMBER,
        p_tax_amount OUT NUMBER
    ) AS
        v_salary NUMBER;
    BEGIN
        SELECT salary INTO v_salary FROM employees WHERE employee_id = p_emp_id;
        p_tax_amount := v_salary * p_tax_rate;
    END;
    """

    res = converter.convert(oracle_code)
    assert res.success is True
    assert res.object_name == "calculate_tax"
    assert res.object_type == PLSQLConstructType.PROCEDURE
    assert "OUT p_tax_amount NUMERIC" in res.target_code
    assert "LANGUAGE plpgsql" in res.target_code
    assert "DECLARE" in res.target_code
    assert "v_salary NUMERIC;" in res.target_code


def test_unsupported_pragma_autonomous_transaction(converter):
    oracle_code = """
    CREATE OR REPLACE PROCEDURE log_audit_event (
        p_msg IN VARCHAR2
    ) AS
        PRAGMA AUTONOMOUS_TRANSACTION;
    BEGIN
        INSERT INTO audit_log VALUES (p_msg, SYSDATE);
        COMMIT;
    END;
    """

    res = converter.convert(oracle_code)
    assert res.success is False
    assert res.has_unsupported is True
    assert any("AUTONOMOUS_TRANSACTION" in u.name for u in res.unsupported_constructs)
    # Check remedy is provided
    assert any("dblink" in u.remedy for u in res.unsupported_constructs)


def test_unsupported_bulk_collect_and_pipe_row(converter):
    bulk_code = """
    CREATE OR REPLACE PROCEDURE fetch_all AS
        TYPE t_emp IS TABLE OF employees%ROWTYPE;
        l_emps t_emp;
    BEGIN
        SELECT * BULK COLLECT INTO l_emps FROM employees;
    END;
    """
    res = converter.convert(bulk_code)
    assert res.success is False
    assert any("BULK COLLECT" in u.name for u in res.unsupported_constructs)

    pipe_code = """
    CREATE OR REPLACE FUNCTION get_rows RETURN my_tab_type AS
    BEGIN
        PIPE ROW(1);
        RETURN;
    END;
    """
    res_pipe = converter.convert(pipe_code)
    assert res_pipe.success is False
    assert any("PIPE ROW" in u.name for u in res_pipe.unsupported_constructs)
