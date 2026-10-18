"""Layer 3: Exact row count parity verification."""

import time
from parity.verifier.models import LayerResult, LayerStatus


def verify_layer3_rowcount(oracle_count: int, postgres_count: int) -> LayerResult:
    """Verifies that both databases return the exact same number of rows."""
    start_time = time.perf_counter()
    elapsed = (time.perf_counter() - start_time) * 1000

    metrics = {
        "oracle_row_count": oracle_count,
        "postgres_row_count": postgres_count,
        "delta": postgres_count - oracle_count,
    }

    if oracle_count != postgres_count:
        return LayerResult(
            layer_number=3,
            name="Row Count",
            status=LayerStatus.FAILED,
            message=f"Row count mismatch: Oracle={oracle_count}, PostgreSQL={postgres_count} (delta={postgres_count - oracle_count})",
            metrics=metrics,
            duration_ms=elapsed,
        )

    return LayerResult(
        layer_number=3,
        name="Row Count",
        status=LayerStatus.PASSED,
        message=f"Row count matches perfectly ({oracle_count} rows)",
        metrics=metrics,
        duration_ms=elapsed,
    )
