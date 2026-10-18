"""Layer 1: Target compilation and syntax validation on PostgreSQL."""

import time
from parity.db import db, DatabaseError
from parity.verifier.models import LayerResult, LayerStatus


def verify_layer1_compile(target_sql: str) -> LayerResult:
    """
    Validates that the target SQL compiles on PostgreSQL using EXPLAIN.
    Does not execute side-effects or retrieve large rowsets.
    """
    start_time = time.perf_counter()
    try:
        db.explain_postgres(target_sql)
        elapsed = (time.perf_counter() - start_time) * 1000
        return LayerResult(
            layer_number=1,
            name="Target Compilation",
            status=LayerStatus.PASSED,
            message="Query compiled and planned successfully on PostgreSQL",
            duration_ms=elapsed,
        )
    except DatabaseError as e:
        elapsed = (time.perf_counter() - start_time) * 1000
        return LayerResult(
            layer_number=1,
            name="Target Compilation",
            status=LayerStatus.FAILED,
            message=str(e),
            duration_ms=elapsed,
        )
