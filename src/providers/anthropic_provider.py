import json
import logging
from typing import Iterator

import anthropic

from src.providers.base import BaseProvider
from src.schemas import CodeReviewOutput, PairEngineerOutput, TokenUsage
from src.prompts import (
    get_review_system_prompt,
    get_review_user_prompt,
    get_pair_system_prompt,
    get_pair_user_prompt,
)
from config import settings

logger = logging.getLogger(__name__)

COST_PER_1K = {
    "claude-sonnet-4-20250514": {"prompt": 0.003, "completion": 0.015},
    "claude-3-5-sonnet-20241022": {"prompt": 0.003, "completion": 0.015},
}


class AnthropicProvider(BaseProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def model(self) -> str:
        return self._model

    def _call(self, system: str, user: str) -> tuple[dict, TokenUsage]:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        content = response.content[0].text
        usage = TokenUsage(
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
        )
        cost = COST_PER_1K.get(self._model, {"prompt": 0.003, "completion": 0.015})
        usage.cost_usd = round(
            (usage.prompt_tokens / 1000) * cost["prompt"]
            + (usage.completion_tokens / 1000) * cost["completion"],
            5,
        )
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end > start:
            content = content[start:end]
        return json.loads(content), usage

    def _call_stream(self, system: str, user: str) -> Iterator[str]:
        with self._client.messages.stream(
            model=self._model,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            for text in stream.text_stream:
                yield text

    def review_code(self, code: str, language: str, two_pass: bool = True) -> tuple[CodeReviewOutput, TokenUsage]:
        system = get_review_system_prompt()
        user = get_review_user_prompt(code, language)

        if two_pass:
            scan_user = f"Quick scan — list only the top 3 issues in this {language} code as bullet points. Keep it brief.\n\n```{language}\n{code[:3000]}\n```"
            scan_result, scan_usage = self._call(system, scan_user)
            context = f"\n## Preliminary Scan Results\n{json.dumps(scan_result)}\n"
            user = context + user

        result, usage = self._call(system, user)
        if two_pass:
            usage.prompt_tokens += scan_usage.prompt_tokens
            usage.completion_tokens += scan_usage.completion_tokens
            usage.total_tokens += scan_usage.total_tokens
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
