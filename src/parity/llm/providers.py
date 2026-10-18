"""Multi-provider LLM wrapper with budget caps, caching, and offline mock support."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
import os
import re
from typing import Any, Dict, Optional
import urllib.request
import urllib.error

from parity.llm.cache import llm_cache
from parity.llm.cost_tracker import CostTracker, UsageRecord
from parity.llm.prompts import SYSTEM_REPAIR_PROMPT
from parity.security.audit import audit_logger


@dataclass
class LLMResponse:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    cached: bool = False


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    def __init__(self, model: str, cost_tracker: Optional[CostTracker] = None, use_cache: bool = True):
        self.model = model
        self.tracker = cost_tracker or CostTracker()
        self.use_cache = use_cache

    @abstractmethod
    def _call_api(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """Internal call to provider API returning dict with 'content', 'prompt_tokens', 'completion_tokens'."""
        raise NotImplementedError

    def generate(
        self,
        prompt: str,
        system_prompt: str = SYSTEM_REPAIR_PROMPT,
        object_name: Optional[str] = None,
    ) -> LLMResponse:
        """Executes prompt with budget assertion, caching, and cost logging."""
        # Check runaway loop and budget caps
        if object_name:
            self.tracker.assert_can_proceed(object_name)

        # Check response cache
        if self.use_cache:
            cached = llm_cache.get(self.model, system_prompt, prompt)
            if cached:
                # Log usage record at 0 additional cost
                record = self.tracker.record_usage(
                    model=self.model,
                    prompt_tokens=0,
                    completion_tokens=0,
                    object_name=object_name,
                )
                return LLMResponse(
                    content=cached["response_text"],
                    model=self.model,
                    prompt_tokens=cached.get("prompt_tokens", 0),
                    completion_tokens=cached.get("completion_tokens", 0),
                    cost_usd=0.0,
                    cached=True,
                )

        # Call underlying provider
        result = self._call_api(prompt, system_prompt)
        content = result["content"]
        p_tokens = result.get("prompt_tokens", len(prompt.split()) * 2)
        c_tokens = result.get("completion_tokens", len(content.split()) * 2)

        record = self.tracker.record_usage(
            model=self.model,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            object_name=object_name,
        )

        # Store in cache
        if self.use_cache:
            llm_cache.set(
                model=self.model,
                system_prompt=system_prompt,
                user_prompt=prompt,
                response_text=content,
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
            )

        # Audit log the LLM invocation
        audit_logger.log_llm_call(
            object_name=object_name,
            provider=self.__class__.__name__,
            model=self.model,
            prompt=prompt,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            cost_usd=record.cost_usd,
            duration_ms=0.0,
            status="SUCCESS",
        )

        return LLMResponse(
            content=content,
            model=self.model,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            cost_usd=record.cost_usd,
            cached=False,
        )


class MockProvider(BaseLLMProvider):
    """Deterministic offline mock provider for testing and development."""

    def __init__(self, model: str = "mock", cost_tracker: Optional[CostTracker] = None):
        super().__init__(model=model, cost_tracker=cost_tracker, use_cache=True)

    def _call_api(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """Synthesizes a rule-based repair from diagnostics."""
        # Extract candidate sql (block 2 is the candidate PostgreSQL SQL)
        sql_blocks = re.findall(r"```sql\s*(.*?)\s*```", prompt, re.DOTALL)
        candidate_sql = sql_blocks[1].strip() if len(sql_blocks) > 1 else (sql_blocks[0].strip() if sql_blocks else prompt)

        # Case 1: NVL in prompt or candidate
        if "nvl(" in candidate_sql.lower():
            repaired_sql = re.sub(r"nvl\(([^,]+),\s*([^)]+)\)", r"COALESCE(\1, \2)", candidate_sql, flags=re.IGNORECASE)

        # Case 2: (+) outer join
        elif "(+)" in candidate_sql:
            repaired_sql = candidate_sql.replace("(+)", "")

        # Case 3: Empty string vs null
        elif "empty string" in prompt.lower() or "ora_diff_001" in prompt.lower():
            repaired_sql = candidate_sql.replace("= ''", "IS NULL")

        # Case 4: ROWNUM pagination
        elif "rownum" in candidate_sql.lower() or "ora_diff_006" in prompt.lower():
            repaired_sql = re.sub(r"WHERE ROWNUM\s*<=\s*(\d+)", r"LIMIT \1", candidate_sql, flags=re.IGNORECASE)

        else:
            repaired_sql = candidate_sql

        mock_content = f"```sql\n{repaired_sql}\n```"
        return {
            "content": mock_content,
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": len(mock_content.split()),
        }


class OllamaProvider(BaseLLMProvider):
    """Local provider using Ollama HTTP REST API."""

    def __init__(
        self,
        model: str = "llama3:latest",
        base_url: str = "http://localhost:11434",
        cost_tracker: Optional[CostTracker] = None,
    ):
        super().__init__(model=model, cost_tracker=cost_tracker)
        self.base_url = base_url.rstrip("/")

    def _call_api(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data.get("message", {}).get("content", "")
                p_tokens = data.get("prompt_eval_count", len(prompt.split()) * 2)
                c_tokens = data.get("eval_count", len(content.split()) * 2)
                return {
                    "content": content,
                    "prompt_tokens": p_tokens,
                    "completion_tokens": c_tokens,
                }
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to connect to local Ollama at {self.base_url}: {e}")


class HostedProvider(BaseLLMProvider):
    """Hosted API provider compatible with OpenAI, Gemini, Groq, etc."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        cost_tracker: Optional[CostTracker] = None,
    ):
        super().__init__(model=model, cost_tracker=cost_tracker)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    def _call_api(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("API key is not configured for hosted provider.")

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choice = data["choices"][0]
                content = choice["message"]["content"]
                usage = data.get("usage", {})
                return {
                    "content": content,
                    "prompt_tokens": usage.get("prompt_tokens", len(prompt.split()) * 2),
                    "completion_tokens": usage.get("completion_tokens", len(content.split()) * 2),
                }
        except Exception as e:
            raise RuntimeError(f"Hosted LLM API error: {e}")


def get_llm_provider(
    provider_name: Optional[str] = None,
    model: Optional[str] = None,
    cost_tracker: Optional[CostTracker] = None,
) -> BaseLLMProvider:
    """Factory creating configured LLM provider."""
    name = (provider_name or os.getenv("PARITY_LLM_PROVIDER", "mock")).lower()

    if name == "ollama":
        return OllamaProvider(model=model or "llama3:latest", cost_tracker=cost_tracker)
    elif name in ["hosted", "openai", "gemini"]:
        return HostedProvider(model=model or "gpt-4o-mini", cost_tracker=cost_tracker)
    else:
        return MockProvider(model=model or "mock", cost_tracker=cost_tracker)
