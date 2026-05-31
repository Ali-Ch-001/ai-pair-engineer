from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "codellama:13b"

    default_provider: str = "openai"
    log_level: str = "INFO"
    max_tokens: int = 4096
    temperature: float = 0.3
    enable_streaming: bool = True


settings = Settings()
