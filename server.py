import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from routina import config, db, llm, validate  # noqa: E402

config.load_env()
STATIC_DIR = ROOT / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = db.get_conn()
    try:
        db.init_schema(conn)
    finally:
        conn.close()
    yield


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
        "available_models": config.AVAILABLE_MODELS,
        "default_model": config.DEFAULT_MODEL,
        "has_api_key": bool(config.get_api_key()),
        "schema_path": str(config.DEFAULT_SCHEMA_PATH.relative_to(config.ROOT)),
    }


@app.get("/api/system-prompt")
def get_system_prompt() -> dict[str, str]:
    return {"text": config.read_default_prompt()}


@app.get("/api/schema")
def get_schema() -> dict[str, Any]:
    return validate.load_schema(config.DEFAULT_SCHEMA_PATH)


# ======================================================================================
# Generate
# ======================================================================================
class OneshotGenerateRequest(BaseModel):
    user_input: str = Field(..., min_length=1)
    prompt_mode: str = Field(..., pattern="^(local|openai_id)$")
    model: str
    system_prompt: Optional[str] = None
    prompt_id: Optional[str] = None
    prompt_version: Optional[str] = None


class ChatGenerateRequest(BaseModel):
    user_input: str = Field(..., min_length=1)
    prompt_mode: str = Field(..., pattern="^(local|openai_id)$")
    model: str
    system_prompt: Optional[str] = None
    prompt_id: Optional[str] = None
    prompt_version: Optional[str] = None
    chat_id: Optional[int] = None


def _make_chat_title(user_input: str) -> str:
    title = user_input.strip().replace("\n", " ")
    if len(title) > 60:
        title = title[:60].rstrip() + "…"
    return title or "Conversación"


def _build_prior_messages(prior_runs: list) -> list[dict[str, Any]]:
    """A partir de runs previos en orden cronológico, arma el historial user/assistant."""
    messages: list[dict[str, Any]] = []
    for r in prior_runs:
        if r["user_input"]:
            messages.append({"role": "user", "content": r["user_input"]})
        if r["raw_response"]:
            messages.append({"role": "assistant", "content": r["raw_response"]})
    return messages


def _validate_and_persist_run(
    *,
    req,
    result,
    chat_id: Optional[int],
) -> tuple[int, str, Optional[list[str]]]:
    """Valida contra schema, decide status, persiste el run, devuelve (run_id, status, schema_errors)."""
    schema_obj = validate.load_schema(config.DEFAULT_SCHEMA_PATH)
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
            prompt_mode=req.prompt_mode,
            system_prompt=req.system_prompt if req.prompt_mode == "local" else None,
            prompt_id=req.prompt_id if req.prompt_mode == "openai_id" else None,
            prompt_version=req.prompt_version if req.prompt_mode == "openai_id" else None,
            schema_path=str(config.DEFAULT_SCHEMA_PATH.relative_to(config.ROOT)),
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


def _common_pre_checks(req) -> None:
    if not config.get_api_key():
        raise HTTPException(
            status_code=400,
            detail="OPENAI_API_KEY no está configurada. Edita el archivo .env y vuelve a iniciar el servidor.",
        )
    if req.prompt_mode == "openai_id" and not (req.prompt_id and req.prompt_id.strip()):
        raise HTTPException(
            status_code=400,
            detail="Falta el prompt_id. Cárgalo en Configuración o cambia a modo local.",
        )


@app.post("/api/oneshot/generate")
def oneshot_generate(req: OneshotGenerateRequest) -> dict[str, Any]:
    """Generación independiente, sin chat ni contexto previo."""
    _common_pre_checks(req)
    api_key = config.get_api_key()

    result = llm.generate_routine(
        api_key=api_key,
        model=req.model,
        user_input=req.user_input,
        prompt_mode=req.prompt_mode,
        system_prompt=req.system_prompt if req.prompt_mode == "local" else None,
        prompt_id=req.prompt_id if req.prompt_mode == "openai_id" else None,
        prompt_version=req.prompt_version if req.prompt_mode == "openai_id" else None,
    )

    run_id, status, schema_errors = _validate_and_persist_run(
        req=req, result=result, chat_id=None
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
    _common_pre_checks(req)
    api_key = config.get_api_key()

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

    result = llm.generate_routine(
        api_key=api_key,
        model=req.model,
        user_input=req.user_input,
        prompt_mode=req.prompt_mode,
        system_prompt=req.system_prompt if req.prompt_mode == "local" else None,
        prompt_id=req.prompt_id if req.prompt_mode == "openai_id" else None,
        prompt_version=req.prompt_version if req.prompt_mode == "openai_id" else None,
        prior_messages=prior_messages,
    )

    run_id, status, schema_errors = _validate_and_persist_run(
        req=req, result=result, chat_id=chat_id
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


# ======================================================================================
# Runs
# ======================================================================================
def _run_summary(row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "status": row["status"],
        "model": row["model"],
        "prompt_mode": row["prompt_mode"],
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
            "prompt_id": row["prompt_id"],
            "prompt_version": row["prompt_version"],
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
        return {"status": "deleted"}
    finally:
        conn.close()


# ======================================================================================
# Admin
# ======================================================================================
@app.post("/api/admin/reset")
def reset_all() -> dict[str, Any]:
    conn = db.get_conn()
    try:
        counts = db.reset_all(conn)
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
