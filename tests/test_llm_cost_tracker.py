"""Unit tests for LLM budget caps, runaway loop detection, and response caching."""

import pytest
from parity.llm.cost_tracker import (
    BudgetExceededError,
    BudgetLimits,
    CostTracker,
    RunawayLoopError,
)
from parity.llm.cache import ResponseCache
from parity.llm.providers import MockProvider


def test_cost_tracker_records_usage():
    limits = BudgetLimits(max_cost_per_object_usd=0.10, max_attempts_per_object=3)
    tracker = CostTracker(limits=limits)

    record = tracker.record_usage(
        model="gpt-4o-mini",
        prompt_tokens=1000,
        completion_tokens=500,
        object_name="test_query",
    )
    assert record.prompt_tokens == 1000
    assert record.completion_tokens == 500
    assert record.cost_usd > 0.0
    assert tracker.get_object_attempts("test_query") == 1
    assert tracker.get_object_cost("test_query") == record.cost_usd


def test_cost_tracker_enforces_runaway_loop():
    limits = BudgetLimits(max_attempts_per_object=2)
    tracker = CostTracker(limits=limits)

    tracker.record_usage("mock", 100, 50, object_name="loop_obj")
    tracker.record_usage("mock", 100, 50, object_name="loop_obj")

    # 3rd attempt should be blocked
    with pytest.raises(RunawayLoopError):
        tracker.assert_can_proceed(object_name="loop_obj")


def test_cost_tracker_enforces_budget_cap():
    # Low budget cap
    limits = BudgetLimits(max_cost_per_object_usd=0.0001)
    tracker = CostTracker(limits=limits)

    # gpt-4o has high pricing, 10000 tokens will exceed 0.0001
    tracker.record_usage("gpt-4o", 10000, 10000, object_name="expensive_obj")

    with pytest.raises(BudgetExceededError):
        tracker.assert_can_proceed(object_name="expensive_obj")


def test_response_cache_get_and_set(tmp_path):
    cache = ResponseCache(cache_dir=tmp_path)
    model = "mock-model"
    sys_prompt = "system"
    user_prompt = "repair this query"

    assert cache.get(model, sys_prompt, user_prompt) is None

    cache.set(model, sys_prompt, user_prompt, "SELECT 1;", 10, 5)
    cached = cache.get(model, sys_prompt, user_prompt)

    assert cached is not None
    assert cached["response_text"] == "SELECT 1;"
    assert cached["prompt_tokens"] == 10
