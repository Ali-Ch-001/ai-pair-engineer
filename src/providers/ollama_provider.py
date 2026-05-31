import json
import logging
from typing import Iterator

import requests

from src.providers.base import BaseProvider
from src.schemas import CodeReviewOutput, PairEngineerOutput, TokenUsage
from src.prompts import (
    get_review_system_prompt,
    get_review_user_prompt,
    get_pair_system_prompt,
    get_pair_user_prompt,
)

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "codellama:13b"):
        self._base_url = base_url.rstrip("/")
        self._model = model

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def model(self) -> str:
        return self._model

    def _call(self, system: str, user: str) -> tuple[dict, TokenUsage]:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "format": "json",
        }
        resp = requests.post(f"{self._base_url}/api/chat", json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        content = data["message"]["content"]
        usage = TokenUsage(
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
        )
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = {"error": "Failed to parse Ollama response as JSON", "raw": content}
        return parsed, usage

    def _call_stream(self, system: str, user: str) -> Iterator[str]:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": True,
        }
        with requests.post(f"{self._base_url}/api/chat", json=payload, stream=True, timeout=120) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            yield chunk["message"]["content"]
                    except json.JSONDecodeError:
                        continue

    def review_code(self, code: str, language: str, two_pass: bool = True) -> tuple[CodeReviewOutput, TokenUsage]:
        result, usage = self._call(
            get_review_system_prompt(),
            get_review_user_prompt(code, language),
        )
        return CodeReviewOutput(**result), usage

    def review_code_stream(self, code: str, language: str) -> Iterator[str]:
        yield from self._call_stream(
            get_review_system_prompt(),
            get_review_user_prompt(code, language),
        )

    def pair_engineer(self, code: str, language: str, focus: str, context: str) -> tuple[PairEngineerOutput, TokenUsage]:
        result, usage = self._call(
            get_pair_system_prompt(focus),
            get_pair_user_prompt(code, language, context),
        )
        return PairEngineerOutput(**result), usage

    def pair_engineer_stream(self, code: str, language: str, focus: str, context: str) -> Iterator[str]:
        yield from self._call_stream(
            get_pair_system_prompt(focus),
            get_pair_user_prompt(code, language, context),
        )
