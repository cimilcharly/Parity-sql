"""Unit tests for Parity verification layers with deliberately planted bugs."""

import pytest
from parity.verifier.layer2_schema import verify_layer2_schema
from parity.verifier.layer3_rowcount import verify_layer3_rowcount
from parity.verifier.layer4_aggregates import verify_layer4_aggregates
from parity.verifier.layer5_hashing import verify_layer5_hashing
from parity.verifier.models import LayerStatus
from parity.verifier.runner import VerificationRunner


def test_layer2_schema_matches():
    res = verify_layer2_schema(["id", "name", "salary"], ["id", "name", "salary"])
    assert res.passed is True
    assert res.status == LayerStatus.PASSED


def test_layer2_schema_planted_column_mismatch():
    # Deliberately planted missing column
    res = verify_layer2_schema(["id", "name", "salary"], ["id", "name"])
    assert res.passed is False
    assert res.status == LayerStatus.FAILED
    assert "Column count mismatch" in res.message


def test_layer2_schema_planted_name_mismatch():
    # Deliberately planted column name divergence
    res = verify_layer2_schema(["id", "name"], ["id", "full_name"])
    assert res.passed is False
    assert "naming/ordering mismatch" in res.message


def test_layer3_rowcount_matches():
    res = verify_layer3_rowcount(107, 107)
    assert res.passed is True


def test_layer3_rowcount_planted_mismatch():
    # Deliberately planted missing row in target
    res = verify_layer3_rowcount(107, 106)
    assert res.passed is False
    assert res.metrics["delta"] == -1
    assert "Row count mismatch" in res.message


def test_layer4_aggregates_matches():
    columns = ["id", "salary"]
    oracle_rows = [(1, 1000.0), (2, 2000.0), (3, None)]
    postgres_rows = [(1, 1000.0), (2, 2000.0), (3, None)]

    res = verify_layer4_aggregates(columns, oracle_rows, postgres_rows)
    assert res.passed is True


def test_layer4_aggregates_planted_decimal_drift():
    columns = ["id", "salary"]
    oracle_rows = [(1, 1000.000000001)]
    postgres_rows = [(1, 1000.000000009)]

    # With tight tolerance 1e-9, drift of 8e-9 is caught
    res = verify_layer4_aggregates(columns, oracle_rows, postgres_rows, tolerance=1e-9)
    assert res.passed is False
    assert "Aggregate mismatch" in res.message


def test_layer4_aggregates_planted_null_count():
    columns = ["id", "bonus"]
    # Oracle treats empty as NULL, Postgres might have non-null
    oracle_rows = [(1, None), (2, 50.0)]
    postgres_rows = [(1, 0.0), (2, 50.0)]

    res = verify_layer4_aggregates(columns, oracle_rows, postgres_rows)
    assert res.passed is False
    assert any(m["metric"] == "null_count" for m in res.diff_details["mismatches"])


def test_layer5_hashing_matches():
    rows_a = [(1, "Alpha"), (2, "Beta")]
    rows_b = [(2, "Beta"), (1, "Alpha")]  # Order-independent multiset match
    res = verify_layer5_hashing(rows_a, rows_b)
    assert res.passed is True


def test_layer5_hashing_planted_divergence():
    # Same row count, same column sum, but different distribution (row divergence)
    # Sum is 15 in both, count is 2 in both, but rows are (5, 10) vs (7, 8)
    oracle_rows = [(1, 5), (2, 10)]
    postgres_rows = [(1, 7), (2, 8)]

    res = verify_layer5_hashing(oracle_rows, postgres_rows)
    assert res.passed is False
    assert res.metrics["total_mismatched_rows"] == 4


def test_verification_runner_end_to_end_mock():
    runner = VerificationRunner()
    o_data = (["id", "salary"], [(1, 5000.0), (2, 6000.0)])
    p_data = (["id", "salary"], [(1, 5000.0), (2, 6000.0)])

    report = runner.verify_query(
        query_name="test_clean",
        oracle_sql="SELECT id, salary FROM employees",
        postgres_sql="SELECT id, salary FROM employees",
        oracle_mock_data=o_data,
        postgres_mock_data=p_data,
    )
    assert report.overall_passed is True
    assert len(report.layers) == 5
