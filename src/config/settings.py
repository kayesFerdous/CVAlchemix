from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # --- LLM -----------------------------------------------------------------
    DEFAULT_MODEL: str = "gemini-2.5-flash-lite"
    GOOGLE_API_KEY: str = ""

    # --- Paths ---------------------------------------------------------------
    PROFILE_DIR: str = "./linkedin_profile"
    OUTPUT_DIR: str = "./output"

    # --- Browser -------------------------------------------------------------
    BROWSER_HEADLESS: bool = False
    SCRAPE_TIMEOUT_MS: int = 30_000

    # --- Resilience ----------------------------------------------------------
    MAX_RETRIES: int = 3

    # --- Logging -------------------------------------------------------------
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
    )

    # -- Validators -----------------------------------------------------------

    @field_validator("PROFILE_DIR", "OUTPUT_DIR")
    @classmethod
    def _ensure_directory_exists(cls, v: str) -> str:
        """Create the directory if it doesn't exist yet."""
        Path(v).mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def _validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(
                f"LOG_LEVEL must be one of {allowed}, got '{v}'"
            )
        return upper


settings = Settings()  # type: ignore[call-arg]
