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

# Registro de modelos con su proveedor. El frontend arma el <select> a partir de
# esto (agrupado por proveedor) y el backend rutea cada modelo al SDK correcto.
MODELS: list[dict[str, str]] = [
    {"id": "gpt-5.5", "provider": "openai"},
    {"id": "gpt-5.4", "provider": "openai"},
    {"id": "gpt-5.4-mini", "provider": "openai"},
    {"id": "gpt-5.4-nano", "provider": "openai"},
    {"id": "claude-opus-4-8", "provider": "anthropic"},
    {"id": "claude-sonnet-5", "provider": "anthropic"},
    {"id": "claude-haiku-4-5", "provider": "anthropic"},
    {"id": "gemini-2.5-pro", "provider": "google"},
    {"id": "gemini-2.5-flash", "provider": "google"},
]

DEFAULT_MODEL = "gpt-5.4-mini"
AVAILABLE_MODELS = [m["id"] for m in MODELS]
PROVIDER_BY_MODEL = {m["id"]: m["provider"] for m in MODELS}

# Variable de entorno con la API key de cada proveedor. Todas viven en `.env`.
PROVIDER_ENV = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
}


def load_env() -> None:
    load_dotenv(ROOT / ".env")


def provider_for(model: str) -> str:
    """Proveedor de un modelo; default a openai para IDs desconocidos."""
    return PROVIDER_BY_MODEL.get(model, "openai")


def get_api_key(provider: str = "openai") -> str | None:
    env_var = PROVIDER_ENV.get(provider)
    return os.environ.get(env_var) if env_var else None


def providers_with_key() -> dict[str, bool]:
    """Qué proveedores tienen su API key configurada (para /api/config y la UI)."""
    return {p: bool(get_api_key(p)) for p in PROVIDER_ENV}


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def read_default_prompt() -> str:
    return DEFAULT_PROMPT_PATH.read_text(encoding="utf-8")
