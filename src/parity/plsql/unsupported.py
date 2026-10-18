"""Scanner for unsupported or ambiguous Oracle PL/SQL constructs."""

import re
from typing import List
from parity.plsql.models import UnsupportedConstruct


PATTERNS = [
    (
        "PRAGMA AUTONOMOUS_TRANSACTION",
        re.compile(r"\bPRAGMA\s+AUTONOMOUS_TRANSACTION\b", re.IGNORECASE),
        "Autonomous transactions are not natively supported in PostgreSQL.",
        "Refactor using dblink_connect / dblink_exec, or isolate into an external client transaction.",
    ),
    (
        "BULK COLLECT / FORALL",
        re.compile(r"\b(BULK\s+COLLECT|FORALL)\b", re.IGNORECASE),
        "Oracle collection bulk-fetching is not supported in PL/pgSQL.",
        "Refactor to standard set-based INSERT/UPDATE statements or UNNEST(array).",
    ),
    (
        "PIPE ROW (Pipelined Functions)",
        re.compile(r"\bPIPE\s+ROW\b", re.IGNORECASE),
        "Pipelined table functions have different semantics in PostgreSQL.",
        "Declare function with RETURNS TABLE(...) and replace PIPE ROW with RETURN NEXT.",
    ),
    (
        "CREATE PACKAGE",
        re.compile(r"\bCREATE\s+(?:OR\s+REPLACE\s+)?PACKAGE\b", re.IGNORECASE),
        "PostgreSQL does not support Oracle packages (namespace bundles of procedures/state).",
        "Decompose package members into individual functions in a dedicated PostgreSQL schema.",
    ),
    (
        "COLLECTION / RECORD TYPE DEFINITION",
        re.compile(r"\bTYPE\s+\w+\s+IS\s+(TABLE\s+OF|RECORD|VARRAY)\b", re.IGNORECASE),
        "Custom PL/SQL collection and record types are not directly supported within PL/pgSQL function headers.",
        "Use PostgreSQL composite types (CREATE TYPE name AS (...)) or native array types.",
    ),
    (
        "GOTO STATEMENT",
        re.compile(r"\bGOTO\s+\w+\b", re.IGNORECASE),
        "GOTO statements do not exist in PostgreSQL PL/pgSQL.",
        "Restructure logic into standard WHILE/LOOP/EXIT WHEN control flow.",
    ),
    (
        "DYNAMIC SQL WITH BIND VARIABLES",
        re.compile(r"\bEXECUTE\s+IMMEDIATE\b.*?\bUSING\b", re.IGNORECASE | re.DOTALL),
        "Oracle EXECUTE IMMEDIATE USING requires parameter mapping syntax in PostgreSQL.",
        "Rewrite using PostgreSQL EXECUTE format(...) USING param1, param2.",
    ),
    (
        "ORACLE PROPRIETARY PACKAGES",
        re.compile(r"\b(UTL_FILE|UTL_HTTP|DBMS_SCHEDULER|DBMS_ALERT|DBMS_PIPE)\b", re.IGNORECASE),
        "Oracle-specific system packages are unavailable in standard PostgreSQL.",
        "Replace with PostgreSQL extensions (e.g., pg_cron, http) or application-level logic.",
    ),
]


def detect_unsupported_constructs(code: str) -> List[UnsupportedConstruct]:
    """Scans PL/SQL code line by line and identifies unsupported constructs."""
    findings: List[UnsupportedConstruct] = []
    lines = code.splitlines()

    for pattern_name, regex, desc, remedy in PATTERNS:
        # Check against entire code first
        if regex.search(code):
            # Locate line number
            matched_line = None
            for idx, line in enumerate(lines, 1):
                if regex.search(line):
                    matched_line = idx
                    break
            findings.append(
                UnsupportedConstruct(
                    name=pattern_name,
                    line_number=matched_line,
                    description=desc,
                    remedy=remedy,
                )
            )

    return findings
