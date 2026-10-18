"""Unit tests for the 500-object enterprise benchmark suite and generator."""

import json
from pathlib import Path
import pytest

from parity.benchmark.generator import BenchmarkCorpusGenerator, corpus_generator
from parity.benchmark.large_scale import LargeScaleBenchmarkRunner


def test_generator_creates_500_diverse_objects():
    generator = BenchmarkCorpusGenerator()
    objects = generator.generate_all_500()

    assert len(objects) == 500
    
    # Verify categories
    categories = set(o.category for o in objects)
    assert len(categories) == 10
    for cat in generator.CATEGORIES:
        assert cat in categories
        count = sum(1 for o in objects if o.category == cat)
        assert count == 50

    # Verify complexity tiers
    tiers = set(o.complexity_tier for o in objects)
    assert "Simple" in tiers
    assert "Moderate" in tiers
    assert "Complex" in tiers
    assert "Extreme" in tiers

    # Verify PL/SQL objects
    plsql_objs = [o for o in objects if o.is_plsql]
    assert len(plsql_objs) >= 50

    # Verify deliberate blocker probes exist
    blockers = [o for o in objects if o.expected_outcome == "HUMAN_REVIEW"]
    assert len(blockers) > 0
    assert any("PRAGMA AUTONOMOUS_TRANSACTION" in (o.expected_blocker or "") for o in blockers)
    assert any("BULK COLLECT" in (o.expected_blocker or "") for o in blockers)


def test_large_scale_benchmark_runner_execution(tmp_path: Path):
    runner = LargeScaleBenchmarkRunner(output_dir=tmp_path)
    summary = runner.run_benchmark(save_results=True, filename="test_bench_500.json")

    assert summary["total_objects"] == 500
    assert summary["verified_count"] >= 450
    assert summary["pass_rate_pct"] >= 90.0
    assert summary["human_review_count"] >= 20
    assert summary["failed_count"] == 0
    assert summary["total_cost_usd"] < 1.0  # Kept strictly within micro-budget
    assert summary["avg_duration_ms"] > 0

    # Check output JSON file
    out_file = tmp_path / "test_bench_500.json"
    assert out_file.exists()
    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["total_objects"] == 500
        assert len(data["items"]) == 500


def test_docs_and_showcase_assets_integrity():
    project_root = Path(__file__).resolve().parent.parent
    docs_dir = project_root / "docs"

    assert (docs_dir / "index.html").exists()
    assert (docs_dir / "css" / "style.css").exists()
    assert (docs_dir / "js" / "app.js").exists()
    assert (docs_dir / "js" / "benchmark-data.js").exists()
    assert (docs_dir / "PILOT_PROPOSAL.md").exists()
    assert (docs_dir / "COMMUNITY_LAUNCH.md").exists()
    assert (docs_dir / "UPSTREAM_SQLGLOT_FINDINGS.md").exists()
    assert (docs_dir / "blog" / "01_ten_ways_oracle_sql_silently_changes_meaning_on_postgres.md").exists()
    assert (docs_dir / "blog" / "02_verification_first_migration.md").exists()

    index_html = (docs_dir / "index.html").read_text(encoding="utf-8")
    assert "<h1" in index_html
    assert "5-Layer Mathematical Verification" in index_html
    assert "id=\"playground-run-btn\"" in index_html
    assert "id=\"bench-search\"" in index_html
