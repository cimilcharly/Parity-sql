"""Layer 2: Result set schema and column compatibility verification."""

import time
from typing import List, Tuple
from parity.verifier.models import LayerResult, LayerStatus


def verify_layer2_schema(
    oracle_columns: List[str],
    postgres_columns: List[str],
) -> LayerResult:
    """Compares column counts, names, and positions between Oracle and Postgres results."""
    start_time = time.perf_counter()

    o_cols = [c.lower() for c in oracle_columns]
    p_cols = [c.lower() for c in postgres_columns]

    metrics = {
        "oracle_column_count": len(o_cols),
        "postgres_column_count": len(p_cols),
        "oracle_columns": o_cols,
        "postgres_columns": p_cols,
    }

    if len(o_cols) != len(p_cols):
        elapsed = (time.perf_counter() - start_time) * 1000
        return LayerResult(
            layer_number=2,
            name="Schema & Columns",
            status=LayerStatus.FAILED,
            message=f"Column count mismatch: Oracle returned {len(o_cols)} columns, PostgreSQL returned {len(p_cols)}",
            metrics=metrics,
            diff_details={"missing_in_postgres": list(set(o_cols) - set(p_cols))},
            duration_ms=elapsed,
        )

    # Check for column name differences
    diffs = []
    for idx, (o, p) in enumerate(zip(o_cols, p_cols)):
        if o != p:
            diffs.append({"index": idx, "oracle_name": o, "postgres_name": p})

    elapsed = (time.perf_counter() - start_time) * 1000
    if diffs:
        return LayerResult(
            layer_number=2,
            name="Schema & Columns",
            status=LayerStatus.FAILED,
            message=f"Column naming/ordering mismatch at {len(diffs)} positions",
            metrics=metrics,
            diff_details={"mismatches": diffs},
            duration_ms=elapsed,
        )

    return LayerResult(
        layer_number=2,
        name="Schema & Columns",
        status=LayerStatus.PASSED,
        message=f"All {len(o_cols)} columns match in name and order",
        metrics=metrics,
        duration_ms=elapsed,
    )
