import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def resolve_project_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_project_env() -> Path:
    env_file = os.environ.get("ENV_FILE", ".env")
    env_path = resolve_project_path(env_file)
    if env_path.exists():
        load_dotenv(env_path)
    return env_path
