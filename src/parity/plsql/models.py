"""Data models for PL/SQL to PL/pgSQL transpilation and construct validation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class PLSQLConstructType(str, Enum):
    FUNCTION = "FUNCTION"
    PROCEDURE = "PROCEDURE"
    PACKAGE = "PACKAGE"
    TRIGGER = "TRIGGER"
    ANONYMOUS_BLOCK = "ANONYMOUS_BLOCK"


@dataclass
class UnsupportedConstruct:
    """Details of an Oracle PL/SQL feature not safely supported in PL/pgSQL."""
    name: str
    line_number: Optional[int]
    description: str
    remedy: str


@dataclass
class PLSQLTranspileResult:
    """Result of attempting to convert an Oracle PL/SQL object to PL/pgSQL."""
    object_name: str
    object_type: PLSQLConstructType
    source_code: str
    target_code: str
    success: bool
    unsupported_constructs: List[UnsupportedConstruct] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def has_unsupported(self) -> bool:
        return len(self.unsupported_constructs) > 0
