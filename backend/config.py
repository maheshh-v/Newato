"""
ARIA Backend Configuration
Loads settings from .env file and provides typed config values.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")


class Settings:
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ARIA_OUTPUT_DIR: Path = Path(os.path.expanduser(os.getenv("ARIA_OUTPUT_DIR", "~/ARIA/outputs")))
    MAX_CONCURRENT_TASKS: int = int(os.getenv("ARIA_MAX_CONCURRENT_TASKS", "4"))
    WEBSOCKET_PORT: int = int(os.getenv("ARIA_WEBSOCKET_PORT", "8765"))
    MAX_STEPS_PER_TASK: int = int(os.getenv("ARIA_MAX_STEPS_PER_TASK", "40"))
    TASK_TIMEOUT_SECONDS: int = int(os.getenv("ARIA_TASK_TIMEOUT_SECONDS", "300"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    DB_PATH: Path = Path(__file__).parent / "aria.db"
    HOST: str = "127.0.0.1"


settings = Settings()


def validate_config() -> list[str]:
    """Return list of validation errors. Empty list = all good."""
    errors: list[str] = []
    if not settings.ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY is not set in .env")
    settings.ARIA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return errors
