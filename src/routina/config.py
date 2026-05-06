import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "routina.db"
PROMPTS_DIR = ROOT / "prompts"
SCHEMAS_DIR = ROOT / "schemas"
DEFAULT_PROMPT_PATH = PROMPTS_DIR / "routina_default.txt"
DEFAULT_SCHEMA_PATH = SCHEMAS_DIR / "routina_v1.json"

DEFAULT_MODEL = "gpt-4o-mini"
AVAILABLE_MODELS = ["gpt-4o-mini", "gpt-4o", "gpt-4.1", "gpt-4.1-mini"]


def load_env() -> None:
    load_dotenv(ROOT / ".env")


def get_api_key() -> str | None:
    return os.environ.get("OPENAI_API_KEY")


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def read_default_prompt() -> str:
    return DEFAULT_PROMPT_PATH.read_text(encoding="utf-8")
