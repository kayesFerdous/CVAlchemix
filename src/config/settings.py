from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.config.config import PROFILE_DIR as DEFAULT_PROFILE_DIR
from src.config.config import ensure_profile_dir


class Settings(BaseSettings):

    # --- LLM -----------------------------------------------------------------
    DEFAULT_MODEL: str = "gemini-2.5-flash-lite"
    GOOGLE_API_KEY: str = ""

    # --- Paths ---------------------------------------------------------------
    PROFILE_DIR: Path = DEFAULT_PROFILE_DIR
    OUTPUT_DIR: Path = Path("./output")
    CV_LOCATION: str = "/home/kayes/Documents/emni/"

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

    @field_validator("PROFILE_DIR", mode="before")
    @classmethod
    def _ensure_profile_directory_exists(cls, _v: str | Path) -> Path:
        """Always use the managed profile directory under config_dir."""
        return ensure_profile_dir()

    @field_validator("OUTPUT_DIR", mode="before")
    @classmethod
    def _ensure_output_directory_exists(cls, v: str | Path) -> Path:
        """Create the directory if it doesn't exist yet."""
        path = Path(v).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return path

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
