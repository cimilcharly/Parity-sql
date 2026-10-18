"""Custom AST rewrite rules and pre/post-processors for Oracle -> PostgreSQL transpilation."""

import re
from typing import List, Tuple
import sqlglot
from sqlglot import exp


class RewriteRule:
    """Base class for AST or token-based rewrite rules."""
    rule_id: str
    description: str

    def apply(self, expression: exp.Expression) -> exp.Expression:
        raise NotImplementedError


class NormalizeSysdateRule(RewriteRule):
    """Replaces Oracle SYSDATE with standard CURRENT_TIMESTAMP."""
    rule_id = "ORA_RULE_001"
    description = "Transform SYSDATE to CURRENT_TIMESTAMP"

    def apply(self, expression: exp.Expression) -> exp.Expression:
        def _replace_sysdate(node):
            if isinstance(node, exp.CurrentTimestamp):
                node.args["sysdate"] = False
                return node
            if isinstance(node, exp.Var) and node.name.upper() == "SYSDATE":
                return exp.CurrentTimestamp()
            if isinstance(node, exp.Anonymous) and node.name.upper() == "SYSDATE":
                return exp.CurrentTimestamp()
            return node

        return expression.transform(_replace_sysdate)


class NullSafeConcatRule(RewriteRule):
    """
    Transforms `a || b` concatenation into `CONCAT(a, b)`
    to emulate Oracle's NULL-safe concatenation behavior in PostgreSQL.
    """
    rule_id = "ORA_RULE_002"
    description = "Emulate Oracle NULL-safe string concatenation"

    def apply(self, expression: exp.Expression) -> exp.Expression:
        def _transform_concat(node):
            if isinstance(node, exp.Concat):
                return exp.Anonymous(
                    this="CONCAT",
                    expressions=[node.this, *node.expressions]
                )
            return node

        return expression.transform(_transform_concat)


class StripFromDualRule(RewriteRule):
    """Removes redundant 'FROM DUAL' table clause in PostgreSQL target."""
    rule_id = "ORA_RULE_003"
    description = "Strip FROM DUAL table clause"

    def apply(self, expression: exp.Expression) -> exp.Expression:
        def _strip_dual(node):
            if isinstance(node, exp.Select):
                from_clause = node.args.get("from") or node.args.get("from_")
                if from_clause:
                    table = from_clause.this
                    if isinstance(table, exp.Table) and table.name.upper() == "DUAL":
                        node.args.pop("from", None)
                        node.args.pop("from_", None)
            return node

        return expression.transform(_strip_dual)


class TruncDateRule(RewriteRule):
    """
    Transforms TRUNC(date, format) to date_trunc(format, date).
    Oracle: TRUNC(date_col, 'MM')
    Postgres: date_trunc('month', date_col)
    """
    rule_id = "ORA_RULE_004"
    description = "Normalize TRUNC date unit to standard Postgres date_trunc string"

    DATE_FORMAT_MAP = {
        "YYYY": "year",
        "YEAR": "year",
        "YY": "year",
        "Q": "quarter",
        "MM": "month",
        "MONTH": "month",
        "MON": "month",
        "WW": "week",
        "W": "week",
        "DD": "day",
        "DAY": "day",
        "DY": "day",
        "HH": "hour",
        "HH24": "hour",
        "MI": "minute",
        "SS": "second"
    }

    def apply(self, expression: exp.Expression) -> exp.Expression:
        def _transform_trunc(node):
            if isinstance(node, exp.DateTrunc):
                unit = node.args.get("unit")
                if isinstance(unit, exp.Literal):
                    raw_val = unit.this.upper()
                    if raw_val in self.DATE_FORMAT_MAP:
                        node.set("unit", exp.Literal.string(self.DATE_FORMAT_MAP[raw_val]))
            elif isinstance(node, exp.Anonymous) and node.name.upper() == "TRUNC":
                args = node.expressions
                if len(args) == 2 and isinstance(args[1], exp.Literal):
                    fmt_val = args[1].this.upper()
                    if fmt_val in self.DATE_FORMAT_MAP:
                        pg_unit = self.DATE_FORMAT_MAP[fmt_val]
                        return exp.DateTrunc(
                            this=args[0],
                            unit=exp.Literal.string(pg_unit)
                        )
            return node

        return expression.transform(_transform_trunc)


class OuterJoinPlusRule(RewriteRule):
    """
    Transforms Oracle's proprietary (+) outer join syntax into standard ANSI LEFT JOIN.
    WHERE d.dept_id = e.dept_id(+) -> FROM departments d LEFT JOIN employees e ON d.dept_id = e.dept_id
    """
    rule_id = "ORA_RULE_005"
    description = "Transform (+) legacy join operator to ANSI LEFT JOIN"

    def apply(self, expression: exp.Expression) -> exp.Expression:
        def _transform_plus_join(node):
            if isinstance(node, exp.Select):
                where = node.args.get("where")
                if not where:
                    return node

                for eq in list(node.find_all(exp.EQ)):
                    col_a, col_b = eq.this, eq.expression
                    target_col = None
                    if getattr(col_b, "args", {}).get("join_mark"):
                        target_col = col_b
                        on_condition = exp.EQ(this=col_a, expression=col_b)
                    elif getattr(col_a, "args", {}).get("join_mark"):
                        target_col = col_a
                        on_condition = exp.EQ(this=col_b, expression=col_a)

                    if target_col:
                        outer_table_alias = target_col.table
                        target_col.set("join_mark", False)
                        # Find corresponding join table
                        for j in list(node.args.get("joins", [])):
                            if j.this.alias == outer_table_alias:
                                node.args["joins"].remove(j)
                                new_join = exp.Join(this=j.this, kind="LEFT", on=on_condition)
                                node.args["joins"].append(new_join)
                                # If where was only this eq condition, remove where clause
                                if where.this == eq or str(where.this) == str(eq):
                                    node.args.pop("where", None)
            return node

        return expression.transform(_transform_plus_join)


DEFAULT_RULES: List[RewriteRule] = [
    NormalizeSysdateRule(),
    NullSafeConcatRule(),
    StripFromDualRule(),
    TruncDateRule(),
    OuterJoinPlusRule(),
]
