"""Data models for SQL lineage, object metadata, and complexity tiers."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set


@dataclass
class SQLObject:
    name: str
    sql: str
    object_type: str  # TABLE, VIEW, QUERY, FUNCTION
    file_path: Optional[Path] = None
    dependencies: Set[str] = field(default_factory=set)
    complexity_score: int = 1
    complexity_tier: str = "Simple"  # Simple, Moderate, Complex, Extreme
    ast_depth: int = 1
    join_count: int = 0
    subquery_count: int = 0


@dataclass
class LineagePlan:
    ordered_objects: List[SQLObject]
    has_cycles: bool = False
    cycle_nodes: List[str] = field(default_factory=list)
    average_complexity: float = 1.0
