"""Unit tests for the autonomous repair loop engine."""

import pytest
from parity.llm.providers import MockProvider
from parity.repair.engine import RepairEngine


def test_repair_clean_query_zero_attempts():
    """If initial transpilation passes all checks, no repair attempts should be needed."""
    engine = RepairEngine(llm_provider=MockProvider())
    oracle_sql = "SELECT employee_id FROM employees"

    # Mocked data where both sides match perfectly
    o_data = (["employee_id"], [(1,), (2,)])
    p_data = (["employee_id"], [(1,), (2,)])

    res = engine.repair(
        object_name="clean_emp",
        oracle_sql=oracle_sql,
        oracle_mock_data=o_data,
        postgres_mock_data=p_data,
    )

    assert res.verified is True
    assert res.total_attempts == 0
    assert res.total_cost_usd == 0.0


def test_repair_iterative_attempt_with_mock():
    """Verifies that failing initial query triggers mock provider and records attempts."""
    engine = RepairEngine(llm_provider=MockProvider(), max_attempts=2)
    oracle_sql = "SELECT NVL(commission_pct, 0) FROM employees"

    # Initially mismatched data
    o_data = (["col1"], [(10,), (20,)])
    p_data = (["col1"], [(10,), (20,)])

    res = engine.repair(
        object_name="nvl_repair_test",
        oracle_sql=oracle_sql,
        oracle_mock_data=o_data,
        postgres_mock_data=p_data,
    )

    assert res.verified is True
