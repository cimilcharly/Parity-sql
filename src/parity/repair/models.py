"""Data models for autonomous SQL repair attempts and outcomes."""

from dataclasses import dataclass, field
from typing import List, Optional
from parity.verifier.models import VerificationReport


@dataclass
class RepairAttempt:
    attempt_number: int
    proposed_sql: str
    verification_report: VerificationReport
    duration_ms: float
    cost_usd: float
    error_feedback: Optional[str] = None


@dataclass
class RepairResult:
    object_name: str
    original_oracle_sql: str
    initial_postgres_sql: str
    final_postgres_sql: str
    verified: bool
    attempts: List[RepairAttempt] = field(default_factory=list)
    applied_kb_entries: List[str] = field(default_factory=list)
    total_cost_usd: float = 0.0
    total_duration_ms: float = 0.0
    failure_reason: Optional[str] = None

    @property
    def total_attempts(self) -> int:
        return len(self.attempts)

    @property
    def last_verification(self) -> Optional[VerificationReport]:
        return self.attempts[-1].verification_report if self.attempts else None
