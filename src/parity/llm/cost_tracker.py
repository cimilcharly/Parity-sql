"""Budget tracking, token limits, and runaway loop prevention for LLM repair calls."""

from dataclasses import dataclass, field
import time
from typing import Dict, List, Optional


class BudgetExceededError(Exception):
    """Raised when an LLM call exceeds object or run budget limits."""
    pass


class RunawayLoopError(Exception):
    """Raised when repair attempts exceed the maximum allowed iterations."""
    pass


@dataclass
class ModelPricing:
    """Pricing per 1M tokens in USD."""
    prompt_price_per_1m: float
    completion_price_per_1m: float


# Default pricing catalog (in USD per 1M tokens)
MODEL_PRICING: Dict[str, ModelPricing] = {
    "mock": ModelPricing(0.0, 0.0),
    "ollama": ModelPricing(0.0, 0.0),  # Local compute is free
    "gpt-4o-mini": ModelPricing(0.15, 0.60),
    "gpt-4o": ModelPricing(2.50, 10.00),
    "gemini-1.5-flash": ModelPricing(0.075, 0.30),
    "gemini-1.5-pro": ModelPricing(1.25, 5.00),
    "claude-3-5-sonnet": ModelPricing(3.00, 15.00),
}


@dataclass
class UsageRecord:
    timestamp: float
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    object_name: Optional[str] = None


@dataclass
class BudgetLimits:
    max_attempts_per_object: int = 3
    max_tokens_per_call: int = 2048
    max_cost_per_object_usd: float = 0.05
    max_cost_per_run_usd: float = 1.00


class CostTracker:
    """
    Tracks and enforces token and monetary expenditure across calls,
    objects, and benchmark runs. Prevents infinite repair loops.
    """

    def __init__(self, limits: Optional[BudgetLimits] = None):
        self.limits = limits or BudgetLimits()
        self.history: List[UsageRecord] = []
        self._object_costs: Dict[str, float] = {}
        self._object_attempts: Dict[str, int] = {}

    @property
    def total_cost_usd(self) -> float:
        return sum(r.cost_usd for r in self.history)

    @property
    def total_prompt_tokens(self) -> int:
        return sum(r.prompt_tokens for r in self.history)

    @property
    def total_completion_tokens(self) -> int:
        return sum(r.completion_tokens for r in self.history)

    def get_object_cost(self, object_name: str) -> float:
        return self._object_costs.get(object_name, 0.0)

    def get_object_attempts(self, object_name: str) -> int:
        return self._object_attempts.get(object_name, 0)

    def assert_can_proceed(self, object_name: str, requested_tokens: int = 0) -> None:
        """Enforces limits before calling the LLM."""
        attempts = self.get_object_attempts(object_name)
        if attempts >= self.limits.max_attempts_per_object:
            raise RunawayLoopError(
                f"Runaway loop detected for object '{object_name}': "
                f"attempt count {attempts} reached hard cap {self.limits.max_attempts_per_object}"
            )

        obj_cost = self.get_object_cost(object_name)
        if obj_cost >= self.limits.max_cost_per_object_usd:
            raise BudgetExceededError(
                f"Per-object budget cap exceeded for '{object_name}': "
                f"${obj_cost:.4f} >= ${self.limits.max_cost_per_object_usd:.4f}"
            )

        if self.total_cost_usd >= self.limits.max_cost_per_run_usd:
            raise BudgetExceededError(
                f"Total run budget cap exceeded: "
                f"${self.total_cost_usd:.4f} >= ${self.limits.max_cost_per_run_usd:.4f}"
            )

    def record_usage(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        object_name: Optional[str] = None,
    ) -> UsageRecord:
        """Calculates cost and appends record to usage log."""
        pricing = MODEL_PRICING.get(model.lower(), ModelPricing(0.50, 1.50))
        cost = (
            (prompt_tokens / 1_000_000.0) * pricing.prompt_price_per_1m
            + (completion_tokens / 1_000_000.0) * pricing.completion_price_per_1m
        )

        record = UsageRecord(
            timestamp=time.time(),
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost,
            object_name=object_name,
        )
        self.history.append(record)

        if object_name:
            self._object_costs[object_name] = self._object_costs.get(object_name, 0.0) + cost
            self._object_attempts[object_name] = self._object_attempts.get(object_name, 0) + 1

        return record

    def reset_object(self, object_name: str) -> None:
        """Resets tracking for a specific object."""
        self._object_costs.pop(object_name, None)
        self._object_attempts.pop(object_name, None)
