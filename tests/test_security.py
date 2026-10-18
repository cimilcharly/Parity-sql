"""Unit tests for Parity security safeguards and PII redaction."""

import pytest
from parity.security.redactor import Redactor, SecurityViolationError


def test_redactor_blocks_destructive_ddl():
    dangerous_queries = [
        "DROP TABLE employees",
        "TRUNCATE TABLE employees",
        "ALTER TABLE employees DROP COLUMN salary",
        "DELETE FROM employees WHERE 1=1",
        "UPDATE employees SET salary = 99999",
        "INSERT INTO employees VALUES (1, 'Hacker')",
        "GRANT ALL PRIVILEGES ON employees TO public",
    ]

    for q in dangerous_queries:
        with pytest.raises(SecurityViolationError):
            Redactor.assert_read_only(q)


def test_redactor_allows_safe_queries():
    safe_queries = [
        "SELECT * FROM employees",
        "SELECT department_id, COUNT(*) FROM employees GROUP BY department_id",
        "WITH cte AS (SELECT * FROM jobs) SELECT * FROM cte",
    ]

    for q in safe_queries:
        # Should not raise exception
        Redactor.assert_read_only(q)


def test_redactor_redacts_sql_literals():
    sql = "SELECT * FROM employees WHERE email = 'secret@corp.com' AND salary > 50000"
    redacted = Redactor.redact_sql_literals(sql)
    assert "secret@corp.com" not in redacted
    assert "<REDACTED_LITERAL>" in redacted


def test_redactor_sanitizes_mismatched_row():
    columns = ["id", "email", "salary"]
    oracle_row = (101, "neena@example.com", 17000.0)
    postgres_row = (101, None, 17000.0)

    sanitized = Redactor.sanitize_mismatch_data(columns, oracle_row, postgres_row)
    assert sanitized["mismatch_columns"] == ["email"]
    # Ensure no raw PII email string is exposed in details
    assert "neena@example.com" not in str(sanitized)
    assert sanitized["details"]["email"]["oracle_is_null"] is False
    assert sanitized["details"]["email"]["postgres_is_null"] is True
