"""Transpiler engine orchestrating sqlglot and Parity rewrite rules."""

from dataclasses import dataclass, field
import logging
from typing import List, Optional
import sqlglot
from sqlglot import exp

logging.getLogger("sqlglot").setLevel(logging.ERROR)

from parity.transpiler.rules import DEFAULT_RULES, RewriteRule


@dataclass
class TranspileResult:
    source_sql: str
    target_sql: str
    success: bool
    error: Optional[str] = None
    applied_rules: List[str] = field(default_factory=list)
    ast_summary: Optional[str] = None


class Transpiler:
    """Transpiles Oracle SQL to PostgreSQL SQL using deterministic AST transformation."""

    def __init__(self, use_parity_rules: bool = True):
        self.use_parity_rules = use_parity_rules
        self.rules: List[RewriteRule] = DEFAULT_RULES if use_parity_rules else []

    def transpile(self, oracle_sql: str, pretty: bool = True) -> TranspileResult:
        """Transpiles Oracle SQL query to PostgreSQL."""
        try:
            # 1. Parse Oracle SQL into sqlglot AST
            parsed = sqlglot.parse_one(oracle_sql, read="oracle")
            applied: List[str] = []

            # 2. Apply Parity custom AST rules if enabled
            if self.use_parity_rules:
                for rule in self.rules:
                    before_str = str(parsed)
                    parsed = rule.apply(parsed)
                    if str(parsed) != before_str:
                        applied.append(rule.rule_id)

            # 3. Transpile AST to PostgreSQL dialect
            pg_sql = parsed.sql(dialect="postgres", pretty=pretty)

            return TranspileResult(
                source_sql=oracle_sql,
                target_sql=pg_sql,
                success=True,
                applied_rules=applied,
                ast_summary=f"Root: {type(parsed).__name__}",
            )
        except Exception as e:
            return TranspileResult(
                source_sql=oracle_sql,
                target_sql="",
                success=False,
                error=f"Transpilation failed: {str(e)}",
            )
