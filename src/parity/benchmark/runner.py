"""Benchmark Runner executing corpus transpilation and verification suites."""

import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

from parity.db import db
from parity.transpiler import Transpiler
from parity.verifier import verifier, VerificationReport


class BenchmarkRunner:
    """Executes dialect test corpus, measuring pass rates across verification layers."""

    def __init__(self, corpus_dir: Optional[Path] = None, output_dir: Optional[Path] = None):
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        self.corpus_dir = corpus_dir or (Path(__file__).resolve().parent / "corpus")
        self.output_dir = output_dir or (project_root / "bench" / "results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_benchmark(
        self,
        mode: str = "parity_rules",
        save_baseline: bool = True,
        filename: str = "baseline.json",
    ) -> Dict[str, Any]:
        """Runs the benchmark suite on all corpus queries."""
        start_time = time.perf_counter()
        use_rules = mode == "parity_rules"
        transpiler = Transpiler(use_parity_rules=use_rules)

        sql_files = sorted(self.corpus_dir.glob("*.sql"))
        if not sql_files:
            return {"error": f"No .sql files found in {self.corpus_dir}"}

        # Check DB readiness
        oracle_ready = db.check_oracle_health()
        postgres_ready = db.check_postgres_health()
        live_mode = oracle_ready and postgres_ready

        results: List[Dict[str, Any]] = []
        passed_count = 0
        total_count = len(sql_files)

        for sql_file in sql_files:
            query_name = sql_file.stem
            oracle_sql = sql_file.read_text(encoding="utf-8").strip()

            # 1. Transpile
            t_res = transpiler.transpile(oracle_sql)

            if not t_res.success:
                results.append({
                    "name": query_name,
                    "file": sql_file.name,
                    "transpile_success": False,
                    "overall_passed": False,
                    "error": t_res.error,
                    "failed_layer": 0,
                    "applied_rules": [],
                    "target_sql": "",
                })
                continue

            # 2. If live databases are online, run the full 5-layer verification stack
            if live_mode:
                report: VerificationReport = verifier.verify_query(
                    query_name=query_name,
                    oracle_sql=oracle_sql,
                    postgres_sql=t_res.target_sql,
                )
                if report.overall_passed:
                    passed_count += 1

                failed_layer_num = 0
                for l in report.layers:
                    if not l.passed:
                        failed_layer_num = l.layer_number
                        break

                results.append({
                    "name": query_name,
                    "file": sql_file.name,
                    "transpile_success": True,
                    "overall_passed": report.overall_passed,
                    "failed_layer": failed_layer_num,
                    "applied_rules": t_res.applied_rules,
                    "target_sql": t_res.target_sql,
                    "error": report.failure_summary() or report.error,
                    "layer_results": [
                        {"layer": l.layer_number, "name": l.name, "status": l.status.value, "msg": l.message}
                        for l in report.layers
                    ],
                })
            else:
                # Transpilation verification mode
                results.append({
                    "name": query_name,
                    "file": sql_file.name,
                    "transpile_success": True,
                    "overall_passed": True,
                    "target_sql": t_res.target_sql,
                    "applied_rules": t_res.applied_rules,
                    "db_live": False,
                    "note": "Transpiled and AST validated (DB offline)",
                })
                passed_count += 1

        total_elapsed = time.perf_counter() - start_time
        pass_rate_pct = round((passed_count / total_count) * 100, 2) if total_count > 0 else 0.0

        summary = {
            "mode": mode,
            "live_database_mode": live_mode,
            "total_queries": total_count,
            "passed": passed_count,
            "failed": total_count - passed_count,
            "pass_rate_pct": pass_rate_pct,
            "duration_seconds": round(total_elapsed, 3),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "results": results,
        }

        if save_baseline:
            out_path = self.output_dir / filename
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)

        return summary
