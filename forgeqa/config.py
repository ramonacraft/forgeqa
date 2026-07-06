"""Central configuration. One place to change model / endpoint.

Everything is env-driven (loaded from .env) so a customer never edits code to
switch models. Dev uses LM Studio, docker deploy uses Ollama. Both are
OpenAI-compatible, so the rest of the app treats them identically.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "lmstudio" (dev) or "ollama" (docker deploy)
    llm_mode: str = Field(default="lmstudio")

    # LM Studio
    lmstudio_base_url: str = Field(default="http://localhost:1234/v1")
    lmstudio_model: str = Field(default="qwen2.5-7b-instruct")
    lmstudio_api_key: str = Field(default="lm-studio")

    # Ollama
    ollama_base_url: str = Field(default="http://ollama:11434/v1")
    ollama_model: str = Field(default="qwen2.5:7b-instruct")
    ollama_api_key: str = Field(default="ollama")

    # Optional cloud fallback (stays off unless explicitly enabled)
    cloud_fallback_enabled: bool = Field(default=False)
    cloud_model: str = Field(default="")
    cloud_api_key: str = Field(default="")

    llm_temperature: float = Field(default=0.1)
    llm_timeout_seconds: int = Field(default=120)

    @property
    def active_base_url(self) -> str:
        return self.ollama_base_url if self.llm_mode == "ollama" else self.lmstudio_base_url

    @property
    def active_model(self) -> str:
        return self.ollama_model if self.llm_mode == "ollama" else self.lmstudio_model

    @property
    def active_api_key(self) -> str:
        return self.ollama_api_key if self.llm_mode == "ollama" else self.lmstudio_api_key


# Import this everywhere. Single source of truth.
settings = Settings()
