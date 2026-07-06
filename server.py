import json
import os
import queue
import sys
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

# `config` no importa los SDKs de LLM, así que es seguro cargarlo y leer el .env antes
# de inicializar verica.
from routina import config  # noqa: E402

config.load_env()

# Observabilidad (opcional, fail-open): verica.init() debe correr ANTES de importar
# `routina.llm` porque parchea los SDKs (openai/anthropic/google-genai) al importarse.
# Sin VERICA_TOKEN no se inicializa nada y la app corre igual, sin trazas.
import verica  # noqa: E402

_verica_on = False
if os.environ.get("VERICA_TOKEN"):
    _verica_on = verica.init(service_name="routina")

# Recién ahora importamos llm/db/validate; los SDKs de LLM se importan ya parcheados.
from routina import agent_tools, catalog, db, llm, validate  # noqa: E402

STATIC_DIR = ROOT / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = db.get_conn()
    try:
        db.init_schema(conn)
    finally:
        conn.close()
    yield
    if _verica_on:
        # Exporta el batch de spans pendiente antes de frenar el server.
        verica.shutdown()


app = FastAPI(title="Routina", lifespan=lifespan)


# ======================================================================================
# Static + index
# ======================================================================================
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))


# ======================================================================================
# Config
# ======================================================================================
@app.get("/api/config")
def get_config() -> dict[str, Any]:
    return {
        "available_models": config.MODELS,
        "default_model": config.DEFAULT_MODEL,
        "providers": config.providers_with_key(),
        "provider_envs": config.PROVIDER_ENV,
        "schema_paths": {mode: config.schema_rel_path(mode) for mode in config.MODES},
    }


@app.get("/api/system-prompt")
def get_system_prompts() -> dict[str, str]:
    """Prompts por defecto de cada modo (oneshot/chat)."""
    return {mode: config.read_default_prompt(mode) for mode in config.MODES}


@app.get("/api/schema")
def get_schema(mode: str = "oneshot") -> dict[str, Any]:
    if mode not in config.MODES:
        raise HTTPException(status_code=400, detail=f"Modo desconocido: {mode}")
    return validate.load_schema(config.schema_path(mode))


# ======================================================================================
# Generate
# ======================================================================================
class OneshotGenerateRequest(BaseModel):
    user_input: str = Field(..., min_length=1)
    model: str
    system_prompt: Optional[str] = None


class ChatGenerateRequest(BaseModel):
    user_input: str = Field(..., min_length=1)
    model: str
    system_prompt: Optional[str] = None
    chat_id: Optional[int] = None


def _make_chat_title(user_input: str) -> str:
    title = user_input.strip().replace("\n", " ")
    if len(title) > 60:
        title = title[:60].rstrip() + "…"
    return title or "Conversación"


def _build_prior_messages(prior_runs: list) -> list[dict[str, Any]]:
    """A partir de runs previos en orden cronológico, arma el historial user/assistant.

    Los turnos de preguntas del agente NO se reinyectan como el sobre JSON
    {tipo: "preguntas"}: si el modelo ve ese JSON como mensaje assistant previo,
    aprende a imitarlo como texto en vez de usar la tool preguntar_usuario. Se
    reemplazan por una descripción neutra (las respuestas del usuario ya citan
    cada pregunta, así que no se pierde contexto).
    """
    messages: list[dict[str, Any]] = []
    for r in prior_runs:
        if r["user_input"]:
            messages.append({"role": "user", "content": r["user_input"]})
        if not r["raw_response"]:
            continue
        content = r["raw_response"]
        parsed = json.loads(r["parsed_json"]) if r["parsed_json"] else None
        if isinstance(parsed, dict) and parsed.get("tipo") == "preguntas":
            listado = "\n".join(
                f"- {q.get('pregunta', '')}" for q in parsed.get("preguntas", [])
            )
            content = (
                "(Con la herramienta preguntar_usuario le hice al usuario estas preguntas:)\n"
                + listado
            )
        messages.append({"role": "assistant", "content": content})
    return messages


def _validate_and_persist_run(
    *,
    req,
    result,
    chat_id: Optional[int],
    mode: str,
) -> tuple[int, str, Optional[list[str]]]:
    """Valida contra el schema del modo, decide status, persiste el run, devuelve (run_id, status, schema_errors)."""
    schema_obj = validate.load_schema(config.schema_path(mode))
    schema_errors: Optional[list[str]] = None
    if result.parsed is not None:
        ok, errs = validate.validate_against_schema(result.parsed, schema_obj)
        if not ok:
            schema_errors = errs

    if result.api_error:
        status = "api_error"
    elif result.parse_error:
        status = "parse_error"
    elif schema_errors:
        status = "schema_error"
    else:
        status = "ok"

    conn = db.get_conn()
    try:
        run_id = db.insert_run(
            conn,
            user_input=req.user_input,
            provider=config.provider_for(req.model),
            system_prompt=req.system_prompt,
            schema_path=config.schema_rel_path(mode),
            model=result.model,
            messages=result.messages,
            tool_calls=result.tool_calls or None,
            raw_response=result.raw,
            parsed_json=result.parsed,
            parse_error=result.parse_error,
            schema_errors=schema_errors,
            latency_ms=result.latency_ms,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            num_turns=result.num_turns,
            status=status,
            chat_id=chat_id,
        )
        if chat_id is not None:
            db.touch_chat(conn, chat_id)
    finally:
        conn.close()

    return run_id, status, schema_errors


def _common_pre_checks(req) -> str:
    """Valida que el proveedor del modelo tenga API key. Devuelve el proveedor."""
    provider = config.provider_for(req.model)
    if not config.get_api_key(provider):
        env_var = config.PROVIDER_ENV.get(provider, "la API key")
        raise HTTPException(
            status_code=400,
            detail=f"{env_var} no está configurada. Edita el archivo .env y vuelve a iniciar el servidor.",
        )
    return provider


@app.post("/api/oneshot/generate")
def oneshot_generate(req: OneshotGenerateRequest) -> dict[str, Any]:
    """Generación independiente, sin chat ni contexto previo."""
    provider = _common_pre_checks(req)
    api_key = config.get_api_key(provider)

    result = llm.generate_routine(
        provider=provider,
        api_key=api_key,
        model=req.model,
        user_input=req.user_input,
        system_prompt=req.system_prompt,
    )

    run_id, status, schema_errors = _validate_and_persist_run(
        req=req, result=result, chat_id=None, mode="oneshot"
    )

    return {
        "run_id": run_id,
        "status": status,
        "parsed": result.parsed,
        "parse_error": result.parse_error,
        "schema_errors": schema_errors,
        "raw": result.raw,
        "api_error": result.api_error,
        "latency_ms": result.latency_ms,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "model": result.model,
    }


@app.post("/api/chat/generate")
def chat_generate(req: ChatGenerateRequest) -> dict[str, Any]:
    """Generación dentro de un chat: incluye los turnos previos como contexto del LLM."""
    provider = _common_pre_checks(req)
    api_key = config.get_api_key(provider)

    conn = db.get_conn()
    try:
        chat_id = req.chat_id
        chat_was_created = False
        prior_messages: list[dict[str, Any]] = []
        if chat_id is None:
            chat_id = db.insert_chat(
                conn,
                title=_make_chat_title(req.user_input),
                mode="chat",
            )
            chat_was_created = True
        else:
            existing = db.get_chat(conn, chat_id)
            if existing is None:
                raise HTTPException(status_code=404, detail="Chat no encontrado.")
            prior_runs = db.list_runs_for_chat(conn, chat_id)
            prior_messages = _build_prior_messages(prior_runs)
    finally:
        conn.close()

    with verica.conversation(f"routina-chat-{chat_id}"):
        result = llm.generate_routine(
            provider=provider,
            api_key=api_key,
            model=req.model,
            user_input=req.user_input,
            system_prompt=req.system_prompt,
            prior_messages=prior_messages,
        )

    run_id, status, schema_errors = _validate_and_persist_run(
        req=req, result=result, chat_id=chat_id, mode="chat"
    )

    return {
        "run_id": run_id,
        "chat_id": chat_id,
        "chat_was_created": chat_was_created,
        "status": status,
        "parsed": result.parsed,
        "parse_error": result.parse_error,
        "schema_errors": schema_errors,
        "raw": result.raw,
        "api_error": result.api_error,
        "latency_ms": result.latency_ms,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "model": result.model,
        "num_turns_in_chat": (len(prior_messages) // 2) + 1,
    }


# Loops agénticos pausados esperando respuesta del usuario (preguntar_usuario),
# por chat_id. En memoria a propósito: el estado es efímero (una pregunta abierta
# en una sesión viva) y si se pierde —reinicio del server, cambio de modelo— el
# turno cae al fallback de historial reconstruido (_build_prior_messages).
AGENT_PENDING: dict[int, dict[str, Any]] = {}


@app.post("/api/agent/generate")
def agent_generate(req: ChatGenerateRequest) -> StreamingResponse:
    """Generación agéntica: loop con tools dentro de un chat de modo 'agent'.

    Responde Server-Sent Events para que la UI muestre el progreso en vivo:
    eventos {"type": "tool", "name": ...} por cada tool que arranca, y al final
    {"type": "result", "data": {...}} con el mismo payload que /api/chat/generate
    (+ tool_calls). Los errores previos al stream (API key, chat inexistente)
    salen como HTTP 4xx normales.

    Si el chat tiene un loop pausado en preguntar_usuario (AGENT_PENDING), este
    turno lo reanuda: el user_input viaja al proveedor como tool_result nativo.
    """
    provider = _common_pre_checks(req)
    api_key = config.get_api_key(provider)

    conn = db.get_conn()
    try:
        chat_id = req.chat_id
        chat_was_created = False
        prior_messages: list[dict[str, Any]] = []
        if chat_id is None:
            chat_id = db.insert_chat(
                conn,
                title=_make_chat_title(req.user_input),
                mode="agent",
            )
            chat_was_created = True
        else:
            existing = db.get_chat(conn, chat_id)
            if existing is None:
                raise HTTPException(status_code=404, detail="Chat no encontrado.")
            prior_runs = db.list_runs_for_chat(conn, chat_id)
            prior_messages = _build_prior_messages(prior_runs)
    finally:
        conn.close()

    # ¿Hay un loop pausado para reanudar? Solo si el proveedor y modelo no cambiaron
    # (el estado nativo no es portable entre proveedores); si cambiaron, se descarta
    # y el turno sigue por el fallback de historial reconstruido.
    resume_state = None
    pending = AGENT_PENDING.pop(chat_id, None)
    if pending is not None and pending["provider"] == provider and pending["model"] == req.model:
        resume_state = pending["state"]

    events: "queue.Queue[dict[str, Any] | None]" = queue.Queue()

    def worker() -> None:
        try:
            # guardar_rutina inserta rutinas antes de que exista el run; se linkean después.
            saved_routine_ids: list[int] = []

            def tool_executor(name: str, args: dict[str, Any]) -> dict[str, Any]:
                return agent_tools.execute(name, args, saved_routine_ids=saved_routine_ids)

            with verica.conversation(f"routina-agent-{chat_id}"):
                result = llm.run_agent(
                    provider=provider,
                    api_key=api_key,
                    model=req.model,
                    user_input=req.user_input,
                    system_prompt=req.system_prompt,
                    prior_messages=prior_messages,
                    tools=agent_tools.tool_defs(),
                    tool_executor=tool_executor,
                    on_tool_start=lambda name: events.put({"type": "tool", "name": name}),
                    resume_state=resume_state,
                )

            # Si el loop quedó pausado en preguntar_usuario, guardar su estado para
            # reanudarlo cuando llegue la respuesta.
            if result.pending_state is not None:
                AGENT_PENDING[chat_id] = {
                    "provider": provider,
                    "model": req.model,
                    "state": result.pending_state,
                }

            run_id, status, schema_errors = _validate_and_persist_run(
                req=req, result=result, chat_id=chat_id, mode="agent"
            )

            if saved_routine_ids:
                link_conn = db.get_conn()
                try:
                    db.link_routines_to_run(link_conn, saved_routine_ids, run_id)
                finally:
                    link_conn.close()

            events.put(
                {
                    "type": "result",
                    "data": {
                        "run_id": run_id,
                        "chat_id": chat_id,
                        "chat_was_created": chat_was_created,
                        "status": status,
                        "parsed": result.parsed,
                        "parse_error": result.parse_error,
                        "schema_errors": schema_errors,
                        "raw": result.raw,
                        "api_error": result.api_error,
                        "latency_ms": result.latency_ms,
                        "input_tokens": result.input_tokens,
                        "output_tokens": result.output_tokens,
                        "model": result.model,
                        "tool_calls": result.tool_calls,
                        "saved_routine_ids": saved_routine_ids,
                        "num_iteraciones": result.num_turns,
                    },
                }
            )
        except Exception as exc:  # el stream ya arrancó: el error viaja como evento
            events.put({"type": "error", "detail": f"{type(exc).__name__}: {exc}"})
        finally:
            events.put(None)

    threading.Thread(target=worker, daemon=True).start()

    def sse_stream():
        while True:
            item = events.get()
            if item is None:
                break
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        sse_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ======================================================================================
# Runs
# ======================================================================================
def _run_summary(row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "status": row["status"],
        "model": row["model"],
        "provider": row["provider"] if "provider" in row.keys() else "openai",
        "user_input": row["user_input"],
        "latency_ms": row["latency_ms"],
        "input_tokens": row["input_tokens"],
        "output_tokens": row["output_tokens"],
    }


def _run_full(row) -> dict[str, Any]:
    base = _run_summary(row)
    base.update(
        {
            "system_prompt": row["system_prompt"],
            "schema_path": row["schema_path"],
            "raw_response": row["raw_response"],
            "parsed_json": json.loads(row["parsed_json"]) if row["parsed_json"] else None,
            "parse_error": row["parse_error"],
            "schema_errors": json.loads(row["schema_errors"]) if row["schema_errors"] else None,
            "messages": json.loads(row["messages_json"]),
            "tool_calls": json.loads(row["tool_calls_json"]) if row["tool_calls_json"] else None,
            "num_turns": row["num_turns"],
        }
    )
    return base


@app.get("/api/runs")
def list_runs(status: Optional[str] = None, limit: int = 100) -> list[dict[str, Any]]:
    conn = db.get_conn()
    try:
        rows = db.list_runs(conn, status=status, limit=limit)
        return [_run_summary(r) for r in rows]
    finally:
        conn.close()


@app.get("/api/runs/{run_id}")
def get_run(run_id: int) -> dict[str, Any]:
    conn = db.get_conn()
    try:
        row = db.get_run(conn, run_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Run no encontrado.")
        return _run_full(row)
    finally:
        conn.close()


# ======================================================================================
# Routines
# ======================================================================================
class SaveRoutineRequest(BaseModel):
    run_id: int


def _routine_summary(row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "objetivo": row["objetivo"],
        "dias_por_semana": row["dias_por_semana"],
        "duracion_sesion": row["duracion_sesion"],
        "formato": row["formato"],
        "run_id": row["run_id"],
    }


def _routine_full(row) -> dict[str, Any]:
    base = _routine_summary(row)
    base["payload"] = json.loads(row["payload_json"])
    return base


@app.post("/api/routines")
def save_routine(req: SaveRoutineRequest) -> dict[str, int]:
    conn = db.get_conn()
    try:
        run = db.get_run(conn, req.run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run no encontrado.")
        if not run["parsed_json"]:
            raise HTTPException(
                status_code=400,
                detail="El run no tiene un JSON válido para guardar como rutina.",
            )
        payload = json.loads(run["parsed_json"])
        # Los runs de chat devuelven un sobre {tipo, rutina|mensaje}; se guarda solo la rutina.
        if isinstance(payload, dict) and payload.get("tipo") == "rutina":
            payload = payload.get("rutina") or {}
        elif isinstance(payload, dict) and payload.get("tipo") == "mensaje":
            raise HTTPException(
                status_code=400,
                detail="Este run es un mensaje conversacional, no tiene una rutina para guardar.",
            )
        routine_id = db.insert_routine(conn, run_id=req.run_id, payload=payload)
        return {"routine_id": routine_id}
    finally:
        conn.close()


@app.get("/api/routines")
def list_routines(
    objetivo: Optional[str] = None,
    formato: Optional[str] = None,
    limit: int = 100,
) -> dict[str, Any]:
    conn = db.get_conn()
    try:
        rows = db.list_routines(
            conn,
            objetivo_contains=objetivo,
            formato=formato,
            limit=limit,
        )
        return {
            "routines": [_routine_summary(r) for r in rows],
            "formatos": db.distinct_formatos(conn),
        }
    finally:
        conn.close()


@app.get("/api/routines/{routine_id}")
def get_routine(routine_id: int) -> dict[str, Any]:
    conn = db.get_conn()
    try:
        row = db.get_routine(conn, routine_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Rutina no encontrada.")
        return _routine_full(row)
    finally:
        conn.close()


@app.delete("/api/routines/{routine_id}")
def delete_routine(routine_id: int) -> dict[str, str]:
    conn = db.get_conn()
    try:
        existing = db.get_routine(conn, routine_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Rutina no encontrada.")
        db.delete_routine(conn, routine_id)
        return {"status": "deleted"}
    finally:
        conn.close()


# ======================================================================================
# Chats
# ======================================================================================
class UpdateChatRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)


def _chat_summary(row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "mode": row["mode"] if "mode" in row.keys() else "chat",
    }


@app.get("/api/chats")
def list_chats(mode: Optional[str] = None) -> list[dict[str, Any]]:
    conn = db.get_conn()
    try:
        return [_chat_summary(r) for r in db.list_chats(conn, mode=mode)]
    finally:
        conn.close()


@app.get("/api/chats/{chat_id}")
def get_chat(chat_id: int) -> dict[str, Any]:
    conn = db.get_conn()
    try:
        chat = db.get_chat(conn, chat_id)
        if chat is None:
            raise HTTPException(status_code=404, detail="Chat no encontrado.")
        runs = db.list_runs_for_chat(conn, chat_id)
        return {
            **_chat_summary(chat),
            "runs": [_run_full(r) for r in runs],
        }
    finally:
        conn.close()


@app.patch("/api/chats/{chat_id}")
def update_chat(chat_id: int, req: UpdateChatRequest) -> dict[str, Any]:
    conn = db.get_conn()
    try:
        existing = db.get_chat(conn, chat_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Chat no encontrado.")
        db.update_chat_title(conn, chat_id, req.title.strip())
        return _chat_summary(db.get_chat(conn, chat_id))
    finally:
        conn.close()


@app.delete("/api/chats/{chat_id}")
def delete_chat(chat_id: int) -> dict[str, str]:
    conn = db.get_conn()
    try:
        existing = db.get_chat(conn, chat_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Chat no encontrado.")
        db.delete_chat(conn, chat_id)
        AGENT_PENDING.pop(chat_id, None)
        return {"status": "deleted"}
    finally:
        conn.close()


# ======================================================================================
# Perfil del usuario
# ======================================================================================
class ProfileUpdateRequest(BaseModel):
    equipamiento: list[str] = Field(default_factory=list)
    lesiones: list[str] = Field(default_factory=list)
    notas: str = ""


@app.get("/api/profile")
def get_profile() -> dict[str, Any]:
    """Perfil actual + vocabulario cerrado del catálogo (para armar los checkboxes)."""
    conn = db.get_conn()
    try:
        return {"profile": db.get_profile(conn), "vocab": catalog.vocab()}
    finally:
        conn.close()


@app.put("/api/profile")
def update_profile(req: ProfileUpdateRequest) -> dict[str, Any]:
    invalid_eq = set(req.equipamiento) - catalog.valid_ids("equipamiento")
    invalid_les = set(req.lesiones) - catalog.valid_ids("lesiones")
    if invalid_eq or invalid_les:
        raise HTTPException(
            status_code=400,
            detail=f"IDs desconocidos: {sorted(invalid_eq | invalid_les)}",
        )
    conn = db.get_conn()
    try:
        db.save_profile(
            conn,
            equipamiento=req.equipamiento,
            lesiones=req.lesiones,
            notas=req.notas.strip(),
        )
        return {"profile": db.get_profile(conn)}
    finally:
        conn.close()


# ======================================================================================
# Catálogo de ejercicios
# ======================================================================================
@app.get("/api/catalog")
def get_catalog(
    grupo: Optional[str] = None,
    nivel: Optional[str] = None,
    equipamiento: Optional[str] = None,
    evitar_lesiones: Optional[str] = None,
) -> dict[str, Any]:
    """Búsqueda en el catálogo local. `equipamiento` y `evitar_lesiones` van como CSV.

    Semántica de `equipamiento`: ausente = no filtrar; presente (incluso vacío "") =
    solo ejercicios cuyo equipamiento requerido esté completamente disponible.
    """
    if grupo and grupo not in catalog.valid_ids("grupos_musculares"):
        raise HTTPException(status_code=400, detail=f"Grupo desconocido: {grupo}")
    if nivel and nivel not in catalog.NIVEL_ORDEN:
        raise HTTPException(status_code=400, detail=f"Nivel desconocido: {nivel}")

    def _csv(value: Optional[str]) -> Optional[list[str]]:
        if value is None:
            return None
        return [v for v in (s.strip() for s in value.split(",")) if v]

    ejercicios = catalog.search(
        grupo=grupo,
        nivel=nivel,
        equipamiento_disponible=_csv(equipamiento),
        evitar_lesiones=_csv(evitar_lesiones),
    )
    return {"total": len(ejercicios), "ejercicios": ejercicios}


# ======================================================================================
# Admin
# ======================================================================================
@app.post("/api/admin/reset")
def reset_all() -> dict[str, Any]:
    conn = db.get_conn()
    try:
        counts = db.reset_all(conn)
        AGENT_PENDING.clear()
        return {"status": "reset", "deleted": counts}
    finally:
        conn.close()


# ======================================================================================
# SPA catchall — se ejecuta solo si ningún endpoint anterior matcheó.
# Permite que rutas cliente como /chat, /agent, /history sirvan index.html.
# ======================================================================================
@app.get("/{full_path:path}")
async def spa_catchall(full_path: str) -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))
