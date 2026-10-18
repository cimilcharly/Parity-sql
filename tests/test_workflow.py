"""Unit tests for Parity end-to-end migration workflow and PR generator."""

from pathlib import Path
import pytest
from parity.workflow import (
    MigrationItem,
    WorkflowEngine,
    branch_name_for_object,
    generate_pr_markdown,
)


def test_branch_name_for_object():
    assert branch_name_for_object("01_simple_select") == "parity/migrate-01_simple_select"
    assert branch_name_for_object("HR.GET_SALARY") == "parity/migrate-hr_get_salary"


def test_generate_pr_markdown_verified_pass(tmp_path):
    item = MigrationItem(
        object_name="01_simple_select",
        source_file=tmp_path / "01_simple_select.sql",
        source_sql="SELECT employee_id FROM employees;",
        target_sql="SELECT employee_id FROM employees;",
        is_plsql=False,
        status="VERIFIED_PASS",
        git_branch="parity/migrate-01_simple_select",
        evidence_report_path=tmp_path / "01_simple_select_evidence.html",
        attempts=1,
        cost_usd=0.0,
        duration_ms=12.4,
        applied_kb_entries=["ORA_DIFF_011"],
    )

    pr_file = tmp_path / "01_simple_select_pr.md"
    md = generate_pr_markdown(item, output_path=pr_file)

    assert "APPROVED FOR MERGE" in md
    assert "01_simple_select" in md
    assert "parity/migrate-01_simple_select" in md
    assert "ORA_DIFF_011" in md
    assert pr_file.exists()


def test_generate_pr_markdown_blocked(tmp_path):
    item = MigrationItem(
        object_name="failing_object",
        source_file=tmp_path / "failing_object.sql",
        source_sql="SELECT * FROM unmapped_table;",
        target_sql="",
        is_plsql=False,
        status="BLOCKED_FAILED",
        git_branch="parity/migrate-failing_object",
        evidence_report_path=None,
        attempts=3,
        cost_usd=0.002,
        duration_ms=45.0,
        failure_reason="Table unmapped_table does not exist",
    )

    md = generate_pr_markdown(item)
    assert "DO NOT MERGE" in md
    assert "BLOCKED" in md


def test_workflow_engine_end_to_end(tmp_path):
    # Create test sql files
    sql_dir = tmp_path / "sql"
    sql_dir.mkdir()

    (sql_dir / "01_test.sql").write_text("SELECT 1 FROM dual;", encoding="utf-8")
    (sql_dir / "02_func.sql").write_text(
        "CREATE OR REPLACE FUNCTION add_tax (p_amt NUMBER) RETURN NUMBER IS BEGIN RETURN p_amt * 1.1; END;",
        encoding="utf-8",
    )

    out_dir = tmp_path / "reports" / "output"
    pr_dir = tmp_path / "reports" / "pr"
    target_sql_dir = tmp_path / "dist"

    engine = WorkflowEngine(
        output_dir=out_dir,
        pr_dir=pr_dir,
        target_sql_dir=target_sql_dir,
    )

    summary = engine.convert_directory(sql_dir, create_git_branches=False)

    assert summary.total_objects == 2
    assert summary.verified_count >= 1
    assert summary.summary_dashboard_path.exists()
    assert (out_dir / "01_test_evidence.html").exists()
    assert (pr_dir / "01_test_pr.md").exists()
    assert (pr_dir / "02_func_pr.md").exists()
