"""Data models for end-to-end migration workflows and PR generation."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class MigrationItem:
    """Individual SQL/PLSQL object migration record in the workflow."""
    object_name: str
    source_file: Path
    source_sql: str
    target_sql: str
    is_plsql: bool
    status: str  # VERIFIED_PASS, BLOCKED_FAILED
    git_branch: str
    evidence_report_path: Optional[Path] = None
    pr_artifact_path: Optional[Path] = None
    attempts: int = 1
    cost_usd: float = 0.0
    duration_ms: float = 0.0
    failure_reason: Optional[str] = None
    applied_kb_entries: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == "VERIFIED_PASS"


@dataclass
class WorkflowSummary:
    """Aggregate summary of batch migration execution."""
    total_objects: int
    verified_count: int
    blocked_count: int
    pass_rate_pct: float
    total_cost_usd: float
    total_duration_ms: float
    items: List[MigrationItem] = field(default_factory=list)
    summary_dashboard_path: Optional[Path] = None
