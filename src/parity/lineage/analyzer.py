"""Parses SQL objects and extracts dependency relationships."""

from pathlib import Path
import re
from typing import List, Optional, Set
import sqlglot
from sqlglot import exp

from parity.lineage.complexity import score_query_complexity
from parity.lineage.models import SQLObject


def parse_sql_object(sql: str, file_path: Optional[Path] = None, fallback_name: Optional[str] = None) -> SQLObject:
    """Extracts object name, type, dependencies, and complexity from a SQL query or DDL statement."""
    clean_sql = sql.strip()
    try:
        parsed = sqlglot.parse_one(clean_sql, read="oracle")
    except Exception:
        # Fallback to generic dialect if oracle parse fails
        parsed = sqlglot.parse_one(clean_sql)

    # 1. Determine Object Type & Name
    obj_name = fallback_name or (file_path.stem if file_path else "unnamed_object")
    obj_type = "QUERY"

    if isinstance(parsed, exp.Create):
        kind = parsed.args.get("kind", "").upper()
        if kind:
            obj_type = kind
        target = parsed.this
        if isinstance(target, exp.Table):
            obj_name = target.name.lower()
        elif hasattr(target, "name"):
            obj_name = target.name.lower()

    # 2. Extract Dependencies (Referenced tables, excluding internal CTE names)
    cte_names: Set[str] = {cte.alias.lower() for cte in parsed.find_all(exp.CTE) if cte.alias}
    referenced_tables: Set[str] = set()

    for table in parsed.find_all(exp.Table):
        t_name = table.name.lower()
        # Exclude DUAL dummy table and internal CTEs
        if t_name and t_name != "dual" and t_name not in cte_names and t_name != obj_name:
            referenced_tables.add(t_name)

    # 3. Complexity Scoring
    meta = score_query_complexity(parsed)

    return SQLObject(
        name=obj_name,
        sql=clean_sql,
        object_type=obj_type,
        file_path=file_path,
        dependencies=referenced_tables,
        complexity_score=meta["score"],
        complexity_tier=meta["tier"],
        ast_depth=meta["ast_depth"],
        join_count=meta["join_count"],
        subquery_count=meta["subquery_count"],
    )


def analyze_directory(directory_path: Path) -> List[SQLObject]:
    """Scans and analyzes all .sql files in a directory."""
    objects = []
    for sql_file in sorted(directory_path.glob("*.sql")):
        content = sql_file.read_text(encoding="utf-8")
        obj = parse_sql_object(content, file_path=sql_file)
        objects.append(obj)
    return objects
