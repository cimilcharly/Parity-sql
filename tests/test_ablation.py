"""Unit tests for the 4-way ablation study runner."""

import pytest
from parity.benchmark.ablation import AblationStudyRunner
from parity.llm.providers import MockProvider


def test_ablation_study_runner(tmp_path):
    runner = AblationStudyRunner(output_dir=tmp_path)
    summary = runner.run_study(llm_provider=MockProvider())

    assert "configurations" in summary
    assert len(summary["configurations"]) == 4
    assert summary["total_corpus_objects"] >= 10

    # Ensure output json file was written
    out_file = tmp_path / "ablation_study.json"
    assert out_file.exists()
