"""Unit tests for SQL object dependency lineage, complexity scoring, and topological sort."""

import pytest
from parity.lineage.analyzer import parse_sql_object
from parity.lineage.complexity import score_query_complexity
from parity.lineage.models import SQLObject
from parity.lineage.topological import order_dependencies
import sqlglot


def test_complexity_scoring_simple():
    parsed = sqlglot.parse_one("SELECT id, name FROM users WHERE id = 1")
    meta = score_query_complexity(parsed)
    assert meta["score"] <= 2
    assert meta["tier"] == "Simple"


def test_complexity_scoring_complex():
    complex_sql = """
    SELECT d.dept_name, e.salary,
           AVG(e.salary) OVER (PARTITION BY d.dept_name) AS avg_sal
    FROM departments d
    JOIN employees e ON d.id = e.dept_id
    JOIN locations l ON d.loc_id = l.id
    WHERE e.id IN (SELECT emp_id FROM bonuses WHERE amount > 1000)
    """
    parsed = sqlglot.parse_one(complex_sql)
    meta = score_query_complexity(parsed)
    assert meta["score"] >= 4
    assert meta["tier"] in ["Moderate", "Complex", "Extreme"]
    assert meta["join_count"] >= 2


def test_parse_sql_object_extracts_dependencies():
    sql = "CREATE VIEW dept_summary AS SELECT department_name FROM departments JOIN locations ON departments.loc_id = locations.id"
    obj = parse_sql_object(sql)
    assert obj.name == "dept_summary"
    assert "departments" in obj.dependencies
    assert "locations" in obj.dependencies


def test_topological_order_dependencies():
    # Base tables (0 dependencies)
    obj_dept = SQLObject(name="departments", sql="SELECT 1", object_type="TABLE", dependencies=set())
    obj_emp = SQLObject(name="employees", sql="SELECT 1", object_type="TABLE", dependencies=set())

    # View 1 depends on departments & employees
    obj_view1 = SQLObject(name="emp_dept_view", sql="SELECT 1", object_type="VIEW", dependencies={"departments", "employees"})

    # View 2 depends on View 1
    obj_view2 = SQLObject(name="executive_summary", sql="SELECT 1", object_type="VIEW", dependencies={"emp_dept_view"})

    # Pass in reversed order
    plan = order_dependencies([obj_view2, obj_view1, obj_dept, obj_emp])

    ordered_names = [o.name for o in plan.ordered_objects]
    assert plan.has_cycles is False

    # Base tables must appear before views that depend on them
    assert ordered_names.index("departments") < ordered_names.index("emp_dept_view")
    assert ordered_names.index("employees") < ordered_names.index("emp_dept_view")
    assert ordered_names.index("emp_dept_view") < ordered_names.index("executive_summary")


def test_topological_cycle_detection():
    # A depends on B, B depends on A
    obj_a = SQLObject(name="table_a", sql="SELECT 1", object_type="VIEW", dependencies={"table_b"})
    obj_b = SQLObject(name="table_b", sql="SELECT 1", object_type="VIEW", dependencies={"table_a"})

    plan = order_dependencies([obj_a, obj_b])
    assert plan.has_cycles is True
    assert "table_a" in plan.cycle_nodes
    assert "table_b" in plan.cycle_nodes
