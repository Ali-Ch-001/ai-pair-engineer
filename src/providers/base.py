from abc import ABC, abstractmethod
from typing import Iterator, Optional
from dataclasses import dataclass

from src.schemas import CodeReviewOutput, PairEngineerOutput, TokenUsage


class BaseProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def model(self) -> str: ...

    @abstractmethod
    def review_code(self, code: str, language: str, two_pass: bool = True) -> tuple[CodeReviewOutput, TokenUsage]: ...

    @abstractmethod
    def review_code_stream(self, code: str, language: str) -> Iterator[str]: ...

    @abstractmethod
    def pair_engineer(self, code: str, language: str, focus: str, context: str) -> tuple[PairEngineerOutput, TokenUsage]: ...

    @abstractmethod
    def pair_engineer_stream(self, code: str, language: str, focus: str, context: str) -> Iterator[str]: ...

    @staticmethod
    def create(provider: str) -> "BaseProvider":
        from config import settings

        if provider == "openai" and settings.openai_api_key:
            from src.providers.openai_provider import OpenAIProvider
            return OpenAIProvider(api_key=settings.openai_api_key, model=settings.openai_model)

        if provider == "anthropic" and settings.anthropic_api_key:
            from src.providers.anthropic_provider import AnthropicProvider
            return AnthropicProvider(api_key=settings.anthropic_api_key, model=settings.anthropic_model)

        if provider == "ollama":
            from src.providers.ollama_provider import OllamaProvider
            return OllamaProvider(base_url=settings.ollama_base_url, model=settings.ollama_model)

        raise ValueError(f"No credentials for provider '{provider}'. Set the API key in .env or the sidebar.")
