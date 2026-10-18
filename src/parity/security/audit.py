"""Audit Logging Subsystem for Parity.

Provides append-only structured audit logging for all LLM calls, tool executions,
and security events to satisfy enterprise security compliance.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional


@dataclass
class AuditRecord:
    timestamp: str
    event_type: str  # LLM_CALL, VERIFICATION_RUN, SECURITY_VIOLATION, REPAIR_STEP
    object_name: str
    provider: Optional[str] = None
    model: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    duration_ms: float = 0.0
    prompt_hash: Optional[str] = None
    status: str = "SUCCESS"  # SUCCESS, FAILED, BLOCKED
    metadata: Optional[Dict[str, Any]] = None


class AuditLogger:
    """Thread-safe append-only audit logger writing to JSONL."""

    def __init__(self, log_path: Optional[Path] = None):
        if log_path is None:
            base_dir = Path(os.getenv("PARITY_AUDIT_DIR", ".cache/audit"))
            base_dir.mkdir(parents=True, exist_ok=True)
            self.log_path = base_dir / "parity_audit.jsonl"
        else:
            self.log_path = log_path
            self.log_path.parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()

    def log_llm_call(
        self,
        object_name: str,
        provider: str,
        model: str,
        prompt: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
        duration_ms: float,
        status: str = "SUCCESS",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditRecord:
        """Records an LLM request/response cycle with prompt hashing."""
        p_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        record = AuditRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="LLM_CALL",
            object_name=object_name,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost_usd,
            duration_ms=duration_ms,
            prompt_hash=p_hash,
            status=status,
            metadata=metadata or {},
        )
        self._write_record(record)
        return record

    def log_verification(
        self,
        object_name: str,
        passed: bool,
        duration_ms: float,
        failed_layer: Optional[int] = None,
        error_msg: Optional[str] = None,
    ) -> AuditRecord:
        """Records a 5-layer verification run."""
        record = AuditRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="VERIFICATION_RUN",
            object_name=object_name,
            duration_ms=duration_ms,
            status="PASSED" if passed else "FAILED",
            metadata={
                "overall_passed": passed,
                "failed_layer": failed_layer,
                "error": error_msg,
            },
        )
        self._write_record(record)
        return record

    def log_security_violation(
        self,
        object_name: str,
        sql: str,
        violation_reason: str,
    ) -> AuditRecord:
        """Records a blocked non-read-only query or PII incident."""
        record = AuditRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="SECURITY_VIOLATION",
            object_name=object_name,
            status="BLOCKED",
            metadata={
                "violation_reason": violation_reason,
                "sql_length": len(sql),
            },
        )
        self._write_record(record)
        return record

    def get_recent_records(self, limit: int = 50) -> List[AuditRecord]:
        """Reads recent audit records from disk."""
        if not self.log_path.exists():
            return []

        records = []
        with self._lock:
            lines = self.log_path.read_text(encoding="utf-8").strip().splitlines()

        for line in lines[-limit:]:
            if line.strip():
                try:
                    data = json.loads(line)
                    records.append(AuditRecord(**data))
                except Exception:
                    continue
        return records

    def _write_record(self, record: AuditRecord) -> None:
        data = asdict(record)
        line = json.dumps(data) + "\n"
        with self._lock:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line)


# Global singleton audit logger
audit_logger = AuditLogger()
