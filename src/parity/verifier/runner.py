"""Verification Runner orchestrating Layers 1 through 5."""

import time
from typing import Any, List, Optional, Tuple

from parity.db import db
from parity.verifier.layer1_compile import verify_layer1_compile
from parity.verifier.layer2_schema import verify_layer2_schema
from parity.verifier.layer3_rowcount import verify_layer3_rowcount
from parity.verifier.layer4_aggregates import verify_layer4_aggregates
from parity.verifier.layer5_hashing import verify_layer5_hashing
from parity.verifier.models import LayerResult, LayerStatus, VerificationReport


class VerificationRunner:
    """Orchestrates all 5 verification layers sequentially."""

    def verify_query(
        self,
        query_name: str,
        oracle_sql: str,
        postgres_sql: str,
        oracle_mock_data: Optional[Tuple[List[str], List[Tuple[Any, ...]]]] = None,
        postgres_mock_data: Optional[Tuple[List[str], List[Tuple[Any, ...]]]] = None,
    ) -> VerificationReport:
        """Runs the 5 verification layers on source Oracle and target PostgreSQL queries."""
        start_time = time.perf_counter()
        layers: List[LayerResult] = []

        # ----------------------------------------------------
        # Layer 1: Target Compilation
        # ----------------------------------------------------
        if postgres_mock_data is None:
            l1 = verify_layer1_compile(postgres_sql)
            layers.append(l1)
            if not l1.passed:
                elapsed = (time.perf_counter() - start_time) * 1000
                return VerificationReport(
                    query_name=query_name,
                    overall_passed=False,
                    source_sql=oracle_sql,
                    target_sql=postgres_sql,
                    layers=layers,
                    total_duration_ms=elapsed,
                    error=f"Layer 1 Failed: {l1.message}",
                )
        else:
            # Mock mode bypasses live EXPLAIN
            layers.append(
                LayerResult(
                    layer_number=1,
                    name="Target Compilation",
                    status=LayerStatus.PASSED,
                    message="Target query compilation passed (mocked)",
                )
            )

        # ----------------------------------------------------
        # Fetch Query Results (Live or Mocked)
        # ----------------------------------------------------
        try:
            if oracle_mock_data:
                o_cols, o_rows = oracle_mock_data
            else:
                o_res = db.execute_oracle(oracle_sql)
                o_cols, o_rows = o_res.columns, o_res.rows

            if postgres_mock_data:
                p_cols, p_rows = postgres_mock_data
            else:
                p_res = db.execute_postgres(postgres_sql)
                p_cols, p_rows = p_res.columns, p_res.rows
        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            return VerificationReport(
                query_name=query_name,
                overall_passed=False,
                source_sql=oracle_sql,
                target_sql=postgres_sql,
                layers=layers,
                total_duration_ms=elapsed,
                error=f"Database execution failed: {str(e)}",
            )

        # ----------------------------------------------------
        # Layer 2: Schema & Columns
        # ----------------------------------------------------
        l2 = verify_layer2_schema(o_cols, p_cols)
        layers.append(l2)
        if not l2.passed:
            elapsed = (time.perf_counter() - start_time) * 1000
            return VerificationReport(
                query_name=query_name,
                overall_passed=False,
                source_sql=oracle_sql,
                target_sql=postgres_sql,
                layers=layers,
                total_duration_ms=elapsed,
            )

        # ----------------------------------------------------
        # Layer 3: Row Count Parity
        # ----------------------------------------------------
        l3 = verify_layer3_rowcount(len(o_rows), len(p_rows))
        layers.append(l3)
        if not l3.passed:
            elapsed = (time.perf_counter() - start_time) * 1000
            return VerificationReport(
                query_name=query_name,
                overall_passed=False,
                source_sql=oracle_sql,
                target_sql=postgres_sql,
                layers=layers,
                total_duration_ms=elapsed,
            )

        # ----------------------------------------------------
        # Layer 4: Column Aggregates
        # ----------------------------------------------------
        l4 = verify_layer4_aggregates(o_cols, o_rows, p_rows)
        layers.append(l4)
        if not l4.passed:
            elapsed = (time.perf_counter() - start_time) * 1000
            return VerificationReport(
                query_name=query_name,
                overall_passed=False,
                source_sql=oracle_sql,
                target_sql=postgres_sql,
                layers=layers,
                total_duration_ms=elapsed,
            )

        # ----------------------------------------------------
        # Layer 5: Row-Level Hashing
        # ----------------------------------------------------
        l5 = verify_layer5_hashing(o_rows, p_rows)
        layers.append(l5)

        elapsed = (time.perf_counter() - start_time) * 1000
        overall = all(l.passed for l in layers)

        return VerificationReport(
            query_name=query_name,
            overall_passed=overall,
            source_sql=oracle_sql,
            target_sql=postgres_sql,
            layers=layers,
            total_duration_ms=elapsed,
        )


verifier = VerificationRunner()
