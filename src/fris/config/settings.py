"""Application settings loaded from environment variables and .env files.

Uses pydantic-settings for type-safe configuration with validation.
Never hardcode secrets — all sensitive values come from environment variables.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """FRIS application settings.

    All fields have defaults for development. Required fields (like API keys)
    will cause startup to fail loudly if missing when they're needed.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === LLM Provider Configuration ===
    llm_provider: str = "mock"
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_model: str | None = None
    openai_model: str | None = None
    mock_model: str = "claude-sonnet-4-20250514"

    # === SEC EDGAR Configuration ===
    # SEC requires a User-Agent header identifying your application and contact.
    # Set this via the SEC_USER_AGENT environment variable; default is a placeholder
    # that identifies the application. Override via .env or environment.
    sec_user_agent: str = "FRIS research example.com"
    sec_edgar_rate_limit: float = 5.0
    sec_edgar_timeout_seconds: int = 30

    # === Application Settings ===
    log_level: str = "INFO"
    max_concurrent_tasks: int = 4
    llm_timeout_seconds: int = 60
    testing: bool = False

    # === Output Paths ===
    output_dir: str = "outputs"
    experiments_dir: str = "experiments/data"

    def _get_sec_user_agent(self) -> str:
        """Return the SEC User-Agent string to use for EDGAR requests.

        Uses the configured sec_user_agent if set, otherwise falls back to
        a placeholder that must be replaced before production use.
        """
        if self.sec_user_agent:
            return self.sec_user_agent
        # Fall back to a placeholder that the user MUST replace.
        return "FRIS research@example.com"

    def validate_provider(self) -> None:
        """Validate that the selected provider has the required configuration."""
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance. Call once at application startup."""
    settings = Settings()
    if not settings.testing:
        settings.validate_provider()
    return settings
