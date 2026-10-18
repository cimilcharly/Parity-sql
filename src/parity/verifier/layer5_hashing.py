"""Layer 5: Row-level cryptographic fingerprinting and bucket hash verification."""

from collections import Counter
import hashlib
import time
from typing import Any, List, Optional, Tuple
from parity.config import settings
from parity.verifier.models import LayerResult, LayerStatus


def _canonicalize_value(val: Any, float_precision: int = 9) -> str:
    """Normalizes values into a canonical string representation for hashing."""
    if val is None:
        return "__PARITY_NULL__"
    if isinstance(val, (float,)):
        return f"{val:.{float_precision}f}"
    if isinstance(val, (int,)):
        return str(val)
    if isinstance(val, str):
        return val.strip()
    return str(val)


def _hash_row(row: Tuple[Any, ...]) -> str:
    """Computes a SHA-256 fingerprint for a single normalized row."""
    canonical_tokens = [_canonicalize_value(v) for v in row]
    row_bytes = "|".join(canonical_tokens).encode("utf-8")
    return hashlib.sha256(row_bytes).hexdigest()


def verify_layer5_hashing(
    oracle_rows: List[Tuple[Any, ...]],
    postgres_rows: List[Tuple[Any, ...]],
) -> LayerResult:
    """
    Verifies that the multiset of row hashes from Oracle matches PostgreSQL exactly.
    Identifies count of mismatched rows without leaking any raw row data.
    """
    start_time = time.perf_counter()

    oracle_hashes = [_hash_row(r) for r in oracle_rows]
    postgres_hashes = [_hash_row(r) for r in postgres_rows]

    o_counter = Counter(oracle_hashes)
    p_counter = Counter(postgres_hashes)

    only_in_oracle = o_counter - p_counter
    only_in_postgres = p_counter - o_counter

    total_mismatched_rows = sum(only_in_oracle.values()) + sum(only_in_postgres.values())

    metrics = {
        "oracle_rows_hashed": len(oracle_hashes),
        "postgres_rows_hashed": len(postgres_hashes),
        "hash_collisions_or_unique_in_oracle": len(only_in_oracle),
        "hash_collisions_or_unique_in_postgres": len(only_in_postgres),
        "total_mismatched_rows": total_mismatched_rows,
    }

    elapsed = (time.perf_counter() - start_time) * 1000

    if total_mismatched_rows > 0:
        return LayerResult(
            layer_number=5,
            name="Row-Level Hashing",
            status=LayerStatus.FAILED,
            message=f"Hash mismatch detected: {total_mismatched_rows} row difference(s) between Oracle and PostgreSQL",
            metrics=metrics,
            diff_details={
                "unique_hashes_oracle_count": len(only_in_oracle),
                "unique_hashes_postgres_count": len(only_in_postgres),
            },
            duration_ms=elapsed,
        )

    return LayerResult(
        layer_number=5,
        name="Row-Level Hashing",
        status=LayerStatus.PASSED,
        message=f"All {len(oracle_hashes)} rows match hash fingerprints with zero divergence",
        metrics=metrics,
        duration_ms=elapsed,
    )
