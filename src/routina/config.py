import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "routina.db"
PROMPTS_DIR = ROOT / "prompts"
SCHEMAS_DIR = ROOT / "schemas"
CATALOG_PATH = ROOT / "catalog" / "ejercicios_v1.json"
# Cada modo de interacción tiene su propio system prompt y su propio schema de
# respuesta.
MODES = ("oneshot", "chat", "agent")
PROMPT_PATHS = {
    "oneshot": PROMPTS_DIR / "routina_oneshot.txt",
    "chat": PROMPTS_DIR / "routina_chat.txt",
    "agent": PROMPTS_DIR / "routina_agent.txt",
}
SCHEMA_PATHS = {
    "oneshot": SCHEMAS_DIR / "routina_v1.json",
    "chat": SCHEMAS_DIR / "chat_v1.json",
    "agent": SCHEMAS_DIR / "agent_v1.json",
}

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


def read_default_prompt(mode: str) -> str:
    return PROMPT_PATHS[mode].read_text(encoding="utf-8")


def schema_path(mode: str):
    return SCHEMA_PATHS[mode]


def schema_rel_path(mode: str) -> str:
    """Ruta del schema relativa a la raíz del repo (para persistir en runs y mostrar en UI)."""
    return str(SCHEMA_PATHS[mode].relative_to(ROOT))
