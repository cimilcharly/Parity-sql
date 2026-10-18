"""Persistent and in-memory response cache for LLM repair invocations."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional


class ResponseCache:
    """Caches LLM query responses using SHA-256 keys."""

    def __init__(self, cache_dir: Optional[Path] = None):
        if cache_dir is None:
            cache_dir = Path(__file__).resolve().parent.parent.parent.parent / ".cache" / "llm"
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, Dict[str, Any]] = {}

    def _make_key(self, model: str, system_prompt: str, user_prompt: str) -> str:
        payload = f"{model}:::{system_prompt}:::{user_prompt}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def get(self, model: str, system_prompt: str, user_prompt: str) -> Optional[Dict[str, Any]]:
        key = self._make_key(model, system_prompt, user_prompt)
        # Check memory first
        if key in self._memory_cache:
            return self._memory_cache[key]

        # Check disk
        file_path = self.cache_dir / f"{key}.json"
        if file_path.exists():
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                self._memory_cache[key] = data
                return data
            except Exception:
                return None
        return None

    def set(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        response_text: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        key = self._make_key(model, system_prompt, user_prompt)
        payload = {
            "key": key,
            "model": model,
            "response_text": response_text,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }
        self._memory_cache[key] = payload
        file_path = self.cache_dir / f"{key}.json"
        try:
            file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            pass

    def clear(self) -> None:
        self._memory_cache.clear()
        for f in self.cache_dir.glob("*.json"):
            try:
                f.unlink()
            except Exception:
                pass


llm_cache = ResponseCache()
