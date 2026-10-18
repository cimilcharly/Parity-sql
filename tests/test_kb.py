"""Unit tests for dialect differences Knowledge Base."""

import pytest
from parity.kb.loader import kb


def test_kb_loads_entries():
    entries = kb.get_all()
    assert len(entries) >= 15


def test_kb_lookup_by_id():
    entry = kb.get_by_id("ORA_DIFF_001")
    assert entry is not None
    assert "Empty String" in entry.title
    assert entry.severity == "HIGH"


def test_kb_search():
    results = kb.search("decode")
    assert len(results) >= 1
    assert any(r.id == "ORA_DIFF_005" for r in results)


def test_kb_diagnostic_matching():
    err_msg = "function nvl(numeric, integer) does not exist"
    matches = kb.match_diagnostic(err_msg, "SELECT NVL(comm, 0) FROM emp")
    assert len(matches) >= 1
    assert matches[0].id == "ORA_DIFF_004"
