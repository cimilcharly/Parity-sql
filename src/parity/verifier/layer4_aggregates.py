"""Layer 4: Column-by-column statistical and numerical aggregate verification."""

import math
import time
from typing import Any, Dict, List, Optional, Tuple
from parity.config import settings
from parity.verifier.models import LayerResult, LayerStatus


def _is_numeric(val: Any) -> bool:
    return isinstance(val, (int, float)) and not isinstance(val, bool)


def compute_column_metrics(values: List[Any]) -> Dict[str, Any]:
    """Computes summary metrics for a list of column values."""
    total = len(values)
    null_count = sum(1 for v in values if v is None)
    non_nulls = [v for v in values if v is not None]
    distinct_count = len(set(non_nulls))

    metrics: Dict[str, Any] = {
        "total": total,
        "null_count": null_count,
        "distinct_count": distinct_count,
    }

    # Check if column is numeric
    numeric_vals = [float(v) for v in non_nulls if _is_numeric(v)]
    if len(numeric_vals) == len(non_nulls) and len(numeric_vals) > 0:
        metrics["is_numeric"] = True
        metrics["sum"] = sum(numeric_vals)
        metrics["min"] = min(numeric_vals)
        metrics["max"] = max(numeric_vals)
        metrics["avg"] = sum(numeric_vals) / len(numeric_vals)
    else:
        metrics["is_numeric"] = False

    return metrics


def verify_layer4_aggregates(
    columns: List[str],
    oracle_rows: List[Tuple[Any, ...]],
    postgres_rows: List[Tuple[Any, ...]],
    tolerance: Optional[float] = None,
) -> LayerResult:
    """Verifies that all column aggregates match within allowable numeric tolerance."""
    start_time = time.perf_counter()
    tol = tolerance if tolerance is not None else settings.numeric_tolerance

    if not columns or (not oracle_rows and not postgres_rows):
        elapsed = (time.perf_counter() - start_time) * 1000
        return LayerResult(
            layer_number=4,
            name="Column Aggregates",
            status=LayerStatus.PASSED,
            message="No columns or empty rowsets to aggregate",
            duration_ms=elapsed,
        )

    # Transpose rows to columns
    o_cols = list(zip(*oracle_rows)) if oracle_rows else [() for _ in columns]
    p_cols = list(zip(*postgres_rows)) if postgres_rows else [() for _ in columns]

    mismatches = []
    col_summaries = {}

    for idx, col_name in enumerate(columns):
        o_vals = list(o_cols[idx]) if idx < len(o_cols) else []
        p_vals = list(p_cols[idx]) if idx < len(p_cols) else []

        o_meta = compute_column_metrics(o_vals)
        p_meta = compute_column_metrics(p_vals)

        col_summaries[col_name] = {
            "oracle_nulls": o_meta["null_count"],
            "postgres_nulls": p_meta["null_count"],
            "oracle_distinct": o_meta["distinct_count"],
            "postgres_distinct": p_meta["distinct_count"],
        }

        # Compare null counts
        if o_meta["null_count"] != p_meta["null_count"]:
            mismatches.append({
                "column": col_name,
                "metric": "null_count",
                "oracle": o_meta["null_count"],
                "postgres": p_meta["null_count"],
            })

        # Compare distinct counts
        if o_meta["distinct_count"] != p_meta["distinct_count"]:
            mismatches.append({
                "column": col_name,
                "metric": "distinct_count",
                "oracle": o_meta["distinct_count"],
                "postgres": p_meta["distinct_count"],
            })

        # Compare numeric metrics if applicable using strict absolute delta vs tolerance
        if o_meta.get("is_numeric") and p_meta.get("is_numeric"):
            for num_key in ["sum", "min", "max", "avg"]:
                o_num = o_meta[num_key]
                p_num = p_meta[num_key]
                delta = abs(p_num - o_num)
                if delta > tol:
                    mismatches.append({
                        "column": col_name,
                        "metric": num_key,
                        "oracle": o_num,
                        "postgres": p_num,
                        "delta": delta,
                    })

    elapsed = (time.perf_counter() - start_time) * 1000

    if mismatches:
        return LayerResult(
            layer_number=4,
            name="Column Aggregates",
            status=LayerStatus.FAILED,
            message=f"Aggregate mismatch in {len(mismatches)} metric(s) across columns",
            metrics={"columns_verified": len(columns), "mismatch_count": len(mismatches)},
            diff_details={"mismatches": mismatches},
            duration_ms=elapsed,
        )

    return LayerResult(
        layer_number=4,
        name="Column Aggregates",
        status=LayerStatus.PASSED,
        message=f"All {len(columns)} columns match in nulls, distinct counts, and numeric aggregates",
        metrics={"columns_verified": len(columns)},
        duration_ms=elapsed,
    )
