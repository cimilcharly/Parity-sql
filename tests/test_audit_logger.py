"""Unit tests for Parity security audit logging."""

import os
from pathlib import Path
import tempfile
import pytest
from parity.security.audit import AuditLogger


@pytest.fixture
def temp_audit_logger(tmp_path):
    log_file = tmp_path / "test_audit.jsonl"
    return AuditLogger(log_path=log_file)


def test_audit_log_llm_call(temp_audit_logger):
    rec = temp_audit_logger.log_llm_call(
        object_name="test_query_01",
        provider="MockProvider",
        model="mock-v1",
        prompt="SELECT * FROM dual",
        prompt_tokens=10,
        completion_tokens=15,
        cost_usd=0.0001,
        duration_ms=45.2,
    )

    assert rec.event_type == "LLM_CALL"
    assert rec.object_name == "test_query_01"
    assert rec.prompt_hash is not None
    assert len(rec.prompt_hash) == 64  # SHA-256

    recent = temp_audit_logger.get_recent_records(10)
    assert len(recent) == 1
    assert recent[0].prompt_hash == rec.prompt_hash
    assert recent[0].cost_usd == 0.0001


def test_audit_log_verification(temp_audit_logger):
    rec = temp_audit_logger.log_verification(
        object_name="query_02",
        passed=True,
        duration_ms=120.5,
    )
    assert rec.event_type == "VERIFICATION_RUN"
    assert rec.status == "PASSED"

    recent = temp_audit_logger.get_recent_records(10)
    assert len(recent) == 1
    assert recent[0].metadata["overall_passed"] is True


def test_audit_log_security_violation(temp_audit_logger):
    rec = temp_audit_logger.log_security_violation(
        object_name="planted_drop_table",
        sql="DROP TABLE employees;",
        violation_reason="DROP TABLE pattern detected",
    )
    assert rec.event_type == "SECURITY_VIOLATION"
    assert rec.status == "BLOCKED"
    assert rec.metadata["violation_reason"] == "DROP TABLE pattern detected"

    recent = temp_audit_logger.get_recent_records(10)
    assert len(recent) == 1
    assert recent[0].status == "BLOCKED"
