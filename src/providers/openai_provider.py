import json
import logging
from typing import Iterator

from openai import OpenAI

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
    "gpt-4o": {"prompt": 0.0025, "completion": 0.010},
    "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
    "gpt-4-turbo": {"prompt": 0.010, "completion": 0.030},
}


class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self._client = OpenAI(api_key=api_key)
        self._model = model

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model(self) -> str:
        return self._model

    def _call(self, messages: list[dict]) -> tuple[dict, TokenUsage]:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )
        usage = TokenUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )
        cost = COST_PER_1K.get(self._model, {"prompt": 0.0025, "completion": 0.010})
        usage.cost_usd = round(
            (usage.prompt_tokens / 1000) * cost["prompt"]
            + (usage.completion_tokens / 1000) * cost["completion"],
            5,
        )
        content = response.choices[0].message.content
        return json.loads(content), usage

    def _call_stream(self, messages: list[dict]) -> Iterator[str]:
        stream = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def review_code(self, code: str, language: str, two_pass: bool = True) -> tuple[CodeReviewOutput, TokenUsage]:
        system = get_review_system_prompt()
        user = get_review_user_prompt(code, language)

        if two_pass:
            scan_prompt = [
                {"role": "system", "content": system},
                {"role": "user", "content": f"Quick scan — list only the top 3 issues in this {language} code as bullet points. Keep it brief.\n\n```{language}\n{code[:3000]}\n```"},
            ]
            scan_result, scan_usage = self._call(scan_prompt)
            context = f"\n## Preliminary Scan Results\n{json.dumps(scan_result)}\n"
            user = context + user

        result, usage = self._call([
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ])
        if two_pass:
            usage.prompt_tokens += scan_usage.prompt_tokens
            usage.completion_tokens += scan_usage.completion_tokens
            usage.total_tokens += scan_usage.total_tokens
        return CodeReviewOutput(**result), usage

    def review_code_stream(self, code: str, language: str) -> Iterator[str]:
        messages = [
            {"role": "system", "content": get_review_system_prompt()},
            {"role": "user", "content": get_review_user_prompt(code, language)},
        ]
        yield from self._call_stream(messages)

    def pair_engineer(self, code: str, language: str, focus: str, context: str) -> tuple[PairEngineerOutput, TokenUsage]:
        messages = [
            {"role": "system", "content": get_pair_system_prompt(focus)},
            {"role": "user", "content": get_pair_user_prompt(code, language, context)},
        ]
        result, usage = self._call(messages)
        return PairEngineerOutput(**result), usage

    def pair_engineer_stream(self, code: str, language: str, focus: str, context: str) -> Iterator[str]:
        messages = [
            {"role": "system", "content": get_pair_system_prompt(focus)},
            {"role": "user", "content": get_pair_user_prompt(code, language, context)},
        ]
        yield from self._call_stream(messages)
