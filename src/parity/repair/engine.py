"""Autonomous repair loop orchestrator: Analyze -> Diagnose -> Propose -> Verify."""

import time
from typing import Any, List, Optional, Tuple

from parity.kb.loader import kb
from parity.llm.prompts import build_repair_prompt, extract_sql_from_response
from parity.llm.providers import BaseLLMProvider, get_llm_provider
from parity.repair.models import RepairAttempt, RepairResult
from parity.transpiler import Transpiler
from parity.verifier import verifier, VerificationReport


class RepairEngine:
    """Coordinates autonomous iterative repair of failing SQL conversions."""

    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        transpiler: Optional[Transpiler] = None,
        max_attempts: int = 3,
    ):
        self.provider = llm_provider or get_llm_provider()
        self.transpiler = transpiler or Transpiler(use_parity_rules=True)
        self.max_attempts = max_attempts

    def repair(
        self,
        object_name: str,
        oracle_sql: str,
        oracle_mock_data: Optional[Tuple[List[str], List[Tuple[Any, ...]]]] = None,
        postgres_mock_data: Optional[Tuple[List[str], List[Tuple[Any, ...]]]] = None,
    ) -> RepairResult:
        """Executes the closed repair loop up to max_attempts."""
        start_time = time.perf_counter()

        # Step 1: Initial Transpilation
        t_res = self.transpiler.transpile(oracle_sql)
        current_sql = t_res.target_sql if t_res.success else oracle_sql

        # Step 2: Initial Verification
        init_report: VerificationReport = verifier.verify_query(
            query_name=object_name,
            oracle_sql=oracle_sql,
            postgres_sql=current_sql,
            oracle_mock_data=oracle_mock_data,
            postgres_mock_data=postgres_mock_data,
        )

        # If already passes verification, no LLM repair needed!
        if init_report.overall_passed:
            elapsed = (time.perf_counter() - start_time) * 1000
            return RepairResult(
                object_name=object_name,
                original_oracle_sql=oracle_sql,
                initial_postgres_sql=current_sql,
                final_postgres_sql=current_sql,
                verified=True,
                total_duration_ms=elapsed,
            )

        # Step 3: Iterative Repair Loop
        attempts: List[RepairAttempt] = []
        applied_kb_ids: List[str] = []
        current_report = init_report

        for attempt_idx in range(1, self.max_attempts + 1):
            attempt_start = time.perf_counter()

            # Identify failure details
            failed_layer = None
            for layer in current_report.layers:
                if not layer.passed:
                    failed_layer = layer
                    break

            layer_name = failed_layer.name if failed_layer else "Execution"
            layer_msg = failed_layer.message if failed_layer else (current_report.error or "Unknown failure")
            diff_details = failed_layer.diff_details if failed_layer else None

            # Diagnose: Fetch relevant KB entries based on error and query
            matched_entries = kb.match_diagnostic(layer_msg, current_sql)
            for e in matched_entries:
                if e.id not in applied_kb_ids:
                    applied_kb_ids.append(e.id)

            # Build prompt without leaking raw row data
            prompt = build_repair_prompt(
                object_name=object_name,
                source_oracle_sql=oracle_sql,
                failed_target_sql=current_sql,
                failed_layer_name=layer_name,
                layer_diagnostics=layer_msg,
                diff_details=diff_details,
                kb_entries=matched_entries,
            )

            # Query LLM Provider
            try:
                llm_resp = self.provider.generate(prompt=prompt, object_name=object_name)
                candidate_sql = extract_sql_from_response(llm_resp.content)
            except Exception as e:
                elapsed = (time.perf_counter() - start_time) * 1000
                return RepairResult(
                    object_name=object_name,
                    original_oracle_sql=oracle_sql,
                    initial_postgres_sql=t_res.target_sql,
                    final_postgres_sql=current_sql,
                    verified=False,
                    attempts=attempts,
                    applied_kb_entries=applied_kb_ids,
                    total_cost_usd=self.provider.tracker.get_object_cost(object_name),
                    total_duration_ms=elapsed,
                    failure_reason=f"LLM Provider Error: {str(e)}",
                )

            # Re-verify proposed candidate SQL
            cand_report = verifier.verify_query(
                query_name=f"{object_name}_attempt_{attempt_idx}",
                oracle_sql=oracle_sql,
                postgres_sql=candidate_sql,
                oracle_mock_data=oracle_mock_data,
                postgres_mock_data=postgres_mock_data,
            )

            attempt_elapsed = (time.perf_counter() - attempt_start) * 1000
            attempt = RepairAttempt(
                attempt_number=attempt_idx,
                proposed_sql=candidate_sql,
                verification_report=cand_report,
                duration_ms=attempt_elapsed,
                cost_usd=llm_resp.cost_usd,
                error_feedback=cand_report.failure_summary(),
            )
            attempts.append(attempt)
            current_sql = candidate_sql
            current_report = cand_report

            # If passed, return success!
            if cand_report.overall_passed:
                total_elapsed = (time.perf_counter() - start_time) * 1000
                return RepairResult(
                    object_name=object_name,
                    original_oracle_sql=oracle_sql,
                    initial_postgres_sql=t_res.target_sql,
                    final_postgres_sql=candidate_sql,
                    verified=True,
                    attempts=attempts,
                    applied_kb_entries=applied_kb_ids,
                    total_cost_usd=self.provider.tracker.get_object_cost(object_name),
                    total_duration_ms=total_elapsed,
                )

        # Reached attempt limit without passing verification
        total_elapsed = (time.perf_counter() - start_time) * 1000
        return RepairResult(
            object_name=object_name,
            original_oracle_sql=oracle_sql,
            initial_postgres_sql=t_res.target_sql,
            final_postgres_sql=current_sql,
            verified=False,
            attempts=attempts,
            applied_kb_entries=applied_kb_ids,
            total_cost_usd=self.provider.tracker.get_object_cost(object_name),
            total_duration_ms=total_elapsed,
            failure_reason=f"Verification failed after {self.max_attempts} repair attempts: {current_report.failure_summary()}",
        )


repair_engine = RepairEngine()
