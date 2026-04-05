"""
ARIA Backend Configuration
Loads settings from .env file and provides typed config values.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root or backend dir
env_path = Path(__file__).parent.parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)


class Settings:
    """Singleton-style settings that can be hot-reloaded at runtime."""

    def __init__(self):
        self._load_from_env()

    def _load_from_env(self):
        """Read all values from current os.environ (call after load_dotenv)."""
        # LLM Provider and Model
        self.LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
        self.LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

        # API Keys for all supported providers
        self.ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
        self.GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
        self.DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

        # Custom / Other provider (any OpenAI-compatible API)
        self.CUSTOM_API_KEY: str = os.getenv("CUSTOM_API_KEY", "")
        self.CUSTOM_BASE_URL: str = os.getenv("CUSTOM_BASE_URL", "")
        self.CUSTOM_PROVIDER_NAME: str = os.getenv("CUSTOM_PROVIDER_NAME", "custom")

        # Other ARIA settings
        self.ARIA_OUTPUT_DIR: Path = Path(os.path.expanduser(os.getenv("ARIA_OUTPUT_DIR", "~/ARIA/outputs")))
        self.MAX_CONCURRENT_TASKS: int = int(os.getenv("ARIA_MAX_CONCURRENT_TASKS", "4"))
        self.WEBSOCKET_PORT: int = int(os.getenv("ARIA_WEBSOCKET_PORT", "8765"))
        self.MAX_STEPS_PER_TASK: int = int(os.getenv("ARIA_MAX_STEPS_PER_TASK", "40"))
        self.TASK_TIMEOUT_SECONDS: int = int(os.getenv("ARIA_TASK_TIMEOUT_SECONDS", "300"))
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.DB_PATH: Path = Path(__file__).parent / "aria.db"
        self.HOST: str = "127.0.0.1"

    def reload(self):
        """Re-read .env from disk and refresh all settings in-place."""
        # Clear relevant env vars so dotenv can overwrite them
        load_dotenv(ENV_FILE, override=True)
        self._load_from_env()


settings = Settings()


def update_env_file(updates: dict[str, str]):
    """
    Merge key=value pairs into the .env file on disk.
    Preserves comments and ordering; adds new keys at the end.
    """
    lines: list[str] = []
    remaining = dict(updates)  # keys we still need to write

    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.rstrip("\n").rstrip("\r")
                # Check if this line sets one of the keys we want to update
                stripped = line.lstrip()
                if stripped and not stripped.startswith("#"):
                    eq_idx = stripped.find("=")
                    if eq_idx > 0:
                        key = stripped[:eq_idx].strip()
                        if key in remaining:
                            # Preserve any inline comment
                            lines.append(f"{key}={remaining.pop(key)}")
                            continue
                lines.append(line)

    # Append any keys that weren't already in the file
    for key, value in remaining.items():
        lines.append(f"{key}={value}")

    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


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
    if settings.LLM_PROVIDER == "custom":
        if not settings.CUSTOM_API_KEY:
            errors.append("CUSTOM_API_KEY is not set in .env")
        if not settings.CUSTOM_BASE_URL:
            errors.append("CUSTOM_BASE_URL is not set in .env")
    settings.ARIA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return errors
