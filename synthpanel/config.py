"""Runtime configuration, loaded from env (SYNTHPANEL_*) with sane defaults."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SYNTHPANEL_", env_file=".env")

    # LLM
    provider: str = "fake"  # "fake" | "anthropic"
    model: str = "claude-opus-4-8"
    anthropic_api_key: str | None = None

    # Run
    max_steps: int = 25
    concurrency: int = 4
    vision: bool = False
    headless: bool = True


def load_settings() -> Settings:
    return Settings()
