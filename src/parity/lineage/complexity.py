"""SQL query complexity scorer based on AST depth, joins, subqueries, and dialect features."""

import sqlglot
from sqlglot import exp


def _calculate_ast_depth(node: exp.Expression, current_depth: int = 1) -> int:
    """Recursively computes maximum depth of AST hierarchy."""
    max_d = current_depth
    for child in node.iter_expressions():
        d = _calculate_ast_depth(child, current_depth + 1)
        if d > max_d:
            max_d = d
    return max_d


def score_query_complexity(parsed: exp.Expression) -> dict:
    """
    Computes a weighted complexity score (1-10) and assigns a tier.
    Factors:
    - AST Depth: > 8 adds points
    - Joins: 1 point per join
    - Subqueries and CTEs: 2 points each
    - Window/Analytic functions: 2 points each
    - Recursive/Hierarchical queries: 4 points
    """
    depth = _calculate_ast_depth(parsed)
    joins = len(list(parsed.find_all(exp.Join)))
    subqueries = len(list(parsed.find_all(exp.Subquery)))
    ctes = len(list(parsed.find_all(exp.CTE)))
    windows = len(list(parsed.find_all(exp.Window)))

    # Check for Oracle recursive / hierarchical features
    is_hierarchical = bool(list(parsed.find_all(exp.Connect))) or "CONNECT BY" in str(parsed).upper()

    score = 1
    # Depth contribution
    if depth > 10:
        score += 3
    elif depth > 5:
        score += 1

    # Structural components
    score += min(joins, 3)
    score += min((subqueries + ctes) * 2, 3)
    score += min(windows * 2, 2)

    if is_hierarchical:
        score += 3

    # Clamp to [1, 10]
    final_score = max(1, min(score, 10))

    if final_score <= 2:
        tier = "Simple"
    elif final_score <= 5:
        tier = "Moderate"
    elif final_score <= 7:
        tier = "Complex"
    else:
        tier = "Extreme"

    return {
        "score": final_score,
        "tier": tier,
        "ast_depth": depth,
        "join_count": joins,
        "subquery_count": subqueries + ctes,
        "window_count": windows,
    }
