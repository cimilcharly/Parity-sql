"""Git operations for per-object branching and atomic migration commits."""

import logging
from pathlib import Path
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


def branch_name_for_object(object_name: str) -> str:
    """Computes standard migration branch name for an object."""
    clean_name = object_name.strip().replace(" ", "_").replace(".", "_").lower()
    return f"parity/migrate-{clean_name}"


class GitOpsManager:
    """Manages git branches and commits for isolated object migrations."""

    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path or Path.cwd()

    def run_git(self, *args: str) -> subprocess.CompletedProcess:
        """Executes a git command in the repository path."""
        cmd = ["git"] + list(args)
        return subprocess.run(
            cmd,
            cwd=str(self.repo_path),
            capture_output=True,
            text=True,
            check=False,
        )

    def is_git_repo(self) -> bool:
        """Checks if the working directory is a git repository."""
        res = self.run_git("rev-parse", "--is-inside-work-tree")
        return res.returncode == 0 and res.stdout.strip() == "true"

    def create_and_checkout_branch(self, branch_name: str) -> bool:
        """Creates and checks out a new branch, or checks out if it exists."""
        if not self.is_git_repo():
            return False

        # Check if branch exists
        res = self.run_git("checkout", "-B", branch_name)
        return res.returncode == 0

    def commit_file(self, file_path: Path, commit_message: str) -> bool:
        """Adds and commits a single migrated file."""
        if not self.is_git_repo():
            return False

        add_res = self.run_git("add", str(file_path))
        if add_res.returncode != 0:
            return False

        commit_res = self.run_git("commit", "-m", commit_message)
        return commit_res.returncode == 0
