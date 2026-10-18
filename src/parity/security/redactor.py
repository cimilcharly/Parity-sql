"""Security and PII Redactor for Parity.

Ensures no raw table rows, credentials, or confidential literals are ever
transmitted to external models or leaked in unredacted reports.
"""

import re
from typing import Any, Dict, List, Tuple


class SecurityViolationError(Exception):
    """Raised when a non-read-only or potentially destructive query is detected."""
    pass


class Redactor:
    """Sanitizes SQL, diagnostics, and data structures."""

    # Mutation patterns that violate read-only safety
    MUTATION_PATTERNS = [
        r"\bDROP\s+(TABLE|VIEW|INDEX|SCHEMA|DATABASE|TRIGGER|PROCEDURE|FUNCTION)\b",
        r"\bTRUNCATE\s+TABLE\b",
        r"\bALTER\s+(TABLE|VIEW|INDEX|SCHEMA|DATABASE)\b",
        r"\bINSERT\s+INTO\b",
        r"\bUPDATE\s+[a-zA-Z0-9_\.]+\s+SET\b",
        r"\bDELETE\s+FROM\b",
        r"\bGRANT\s+\b",
        r"\bREVOKE\s+\b",
    ]

    # Sensitive key regex
    SENSITIVE_KEYS = re.compile(
        r"(password|secret|token|api[_-]?key|auth|credential|ssn|credit[_-]?card)",
        re.IGNORECASE,
    )

    @classmethod
    def assert_read_only(cls, sql: str) -> None:
        """Enforces read-only compliance by rejecting DDL/DML mutation queries."""
        clean_sql = cls._strip_comments(sql).strip()
        for pattern in cls.MUTATION_PATTERNS:
            if re.search(pattern, clean_sql, re.IGNORECASE):
                raise SecurityViolationError(
                    f"Read-only violation: Query contains disallowed statement matching '{pattern}'"
                )

    @classmethod
    def redact_sql_literals(cls, sql: str) -> str:
        """Replaces string and numeric literals in SQL queries with placeholders."""
        # Replace string literals '...' with '<STR_LITERAL>'
        redacted = re.sub(r"'(?:''|[^'])*'", "'<REDACTED_LITERAL>'", sql)
        # Replace standalone numbers in values (not identifiers)
        redacted = re.sub(r"\b\d+\.?\d*\b", "<NUM>", redacted)
        return redacted

    @classmethod
    def sanitize_mismatch_data(
        cls,
        columns: List[str],
        oracle_row: Tuple[Any, ...],
        postgres_row: Tuple[Any, ...]
    ) -> Dict[str, Any]:
        """Converts raw mismatched row data into metadata-only diagnostics without raw values."""
        diff_info = {}
        for col_name, o_val, p_val in zip(columns, oracle_row, postgres_row):
            if o_val != p_val:
                diff_info[col_name] = {
                    "oracle_type": type(o_val).__name__,
                    "postgres_type": type(p_val).__name__,
                    "oracle_is_null": o_val is None,
                    "postgres_is_null": p_val is None,
                    "oracle_len": len(str(o_val)) if o_val is not None else 0,
                    "postgres_len": len(str(p_val)) if p_val is not None else 0,
                }
        return {
            "mismatch_columns": list(diff_info.keys()),
            "details": diff_info,
        }

    @staticmethod
    def _strip_comments(sql: str) -> str:
        """Removes single-line -- comments and multi-line /* */ comments."""
        no_single = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
        no_multi = re.sub(r"/\*.*?\*/", "", no_single, flags=re.DOTALL)
        return no_multi
