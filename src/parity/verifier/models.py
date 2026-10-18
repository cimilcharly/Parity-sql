"""Data models and diagnostic schemas for Parity verification layers."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class LayerStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


@dataclass
class LayerResult:
    layer_number: int
    name: str
    status: LayerStatus
    message: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    diff_details: Optional[Dict[str, Any]] = None
    duration_ms: float = 0.0

    @property
    def passed(self) -> bool:
        return self.status == LayerStatus.PASSED


@dataclass
class VerificationReport:
    query_name: str
    overall_passed: bool
    source_sql: str
    target_sql: str
    layers: List[LayerResult] = field(default_factory=list)
    total_duration_ms: float = 0.0
    error: Optional[str] = None

    def get_layer(self, number: int) -> Optional[LayerResult]:
        for layer in self.layers:
            if layer.layer_number == number:
                return layer
        return None

    def failure_summary(self) -> Optional[str]:
        for layer in self.layers:
            if not layer.passed:
                return f"Layer {layer.layer_number} ({layer.name}): {layer.message}"
        return None
