"""Workflow and CI automation subpackage for Parity."""

from parity.workflow.engine import WorkflowEngine
from parity.workflow.git_ops import GitOpsManager, branch_name_for_object
from parity.workflow.models import MigrationItem, WorkflowSummary
from parity.workflow.pr_generator import generate_pr_markdown

__all__ = [
    "GitOpsManager",
    "MigrationItem",
    "WorkflowEngine",
    "WorkflowSummary",
    "branch_name_for_object",
    "generate_pr_markdown",
]
