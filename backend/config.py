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
    # LLM Provider and Model
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

    # API Keys for all supported providers
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Other ARIA settings
    ARIA_OUTPUT_DIR: Path = Path(os.path.expanduser(os.getenv("ARIA_OUTPUT_DIR", "~/ARIA/outputs")))
    MAX_CONCURRENT_TASKS: int = int(os.getenv("ARIA_MAX_CONCURRENT_TASKS", "4"))
    WEBSOCKET_PORT: int = int(os.getenv("ARIA_WEBSOCKET_PORT", "8765"))
    MAX_STEPS_PER_TASK: int = int(os.getenv("ARIA_MAX_STEPS_PER_TASK", "40"))
    TASK_TIMEOUT_SECONDS: int = int(os.getenv("ARIA_TASK_TIMEOUT_SECONDS", "300"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DB_PATH: Path = Path(__file__).parent / "aria.db"
    HOST: str = "127.0.0.1"

settings = Settings()


def validate_config() -> list[str]:
    """Return list of validation errors. Empty list = all good."""
    errors: list[str] = []
    if settings.LLM_PROVIDER == "anthropic" and not settings.ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY is not set in .env")
    if settings.LLM_PROVIDER == "groq" and not settings.GROQ_API_KEY:
        errors.append("GROQ_API_KEY is not set in .env")
    if settings.LLM_PROVIDER == "deepseek" and not settings.DEEPSEEK_API_KEY:
        errors.append("DEEPSEEK_API_KEY is not set in .env")
    if settings.LLM_PROVIDER == "openai" and not settings.OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is not set in .env")
    settings.ARIA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return errors
