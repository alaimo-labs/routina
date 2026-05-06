import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import DB_PATH, ensure_data_dir

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS chats (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL,
  title           TEXT NOT NULL,
  mode            TEXT NOT NULL DEFAULT 'chat'
);

CREATE TABLE IF NOT EXISTS runs (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at      TEXT NOT NULL,
  user_input      TEXT NOT NULL,
  prompt_mode     TEXT NOT NULL,
  system_prompt   TEXT,
  prompt_id       TEXT,
  prompt_version  TEXT,
  schema_path     TEXT NOT NULL,
  model           TEXT NOT NULL,
  messages_json   TEXT NOT NULL,
  tool_calls_json TEXT,
  raw_response    TEXT NOT NULL,
  parsed_json     TEXT,
  parse_error     TEXT,
  schema_errors   TEXT,
  latency_ms      INTEGER,
  input_tokens    INTEGER,
  output_tokens   INTEGER,
  num_turns       INTEGER NOT NULL DEFAULT 1,
  status          TEXT NOT NULL,
  chat_id         INTEGER REFERENCES chats(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS routines (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id          INTEGER REFERENCES runs(id) ON DELETE SET NULL,
  created_at      TEXT NOT NULL,
  objetivo        TEXT NOT NULL,
  dias_por_semana INTEGER,
  duracion_sesion INTEGER,
  formato         TEXT,
  payload_json    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs(created_at);
CREATE INDEX IF NOT EXISTS idx_chats_updated   ON chats(updated_at);
CREATE INDEX IF NOT EXISTS idx_routines_created_at ON routines(created_at);
"""


def get_conn() -> sqlite3.Connection:
    ensure_data_dir()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    # Migración: agregar chat_id a runs si la tabla viene de una versión anterior.
    cur = conn.execute("PRAGMA table_info(runs)")
    existing_cols = {row[1] for row in cur.fetchall()}
    if "chat_id" not in existing_cols:
        conn.execute("ALTER TABLE runs ADD COLUMN chat_id INTEGER")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_chat_id ON runs(chat_id)")
    # Migración: agregar mode a chats si viene de una versión anterior.
    cur = conn.execute("PRAGMA table_info(chats)")
    chat_cols = {row[1] for row in cur.fetchall()}
    if "mode" not in chat_cols:
        conn.execute("ALTER TABLE chats ADD COLUMN mode TEXT NOT NULL DEFAULT 'chat'")
    conn.commit()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def insert_run(
    conn: sqlite3.Connection,
    *,
    user_input: str,
    prompt_mode: str,
    system_prompt: str | None,
    prompt_id: str | None,
    prompt_version: str | None,
    schema_path: str,
    model: str,
    messages: list[dict[str, Any]],
    tool_calls: list[dict[str, Any]] | None,
    raw_response: str,
    parsed_json: dict[str, Any] | None,
    parse_error: str | None,
    schema_errors: list[str] | None,
    latency_ms: int | None,
    input_tokens: int | None,
    output_tokens: int | None,
    num_turns: int,
    status: str,
    chat_id: int | None = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO runs (
            created_at, user_input, prompt_mode, system_prompt, prompt_id, prompt_version,
            schema_path, model, messages_json, tool_calls_json, raw_response, parsed_json,
            parse_error, schema_errors, latency_ms, input_tokens, output_tokens, num_turns, status, chat_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            _now_iso(),
            user_input,
            prompt_mode,
            system_prompt,
            prompt_id,
            prompt_version,
            schema_path,
            model,
            json.dumps(messages, ensure_ascii=False),
            json.dumps(tool_calls, ensure_ascii=False) if tool_calls else None,
            raw_response,
            json.dumps(parsed_json, ensure_ascii=False) if parsed_json is not None else None,
            parse_error,
            json.dumps(schema_errors, ensure_ascii=False) if schema_errors else None,
            latency_ms,
            input_tokens,
            output_tokens,
            num_turns,
            status,
            chat_id,
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


# ----- Chats -----

def insert_chat(conn: sqlite3.Connection, *, title: str, mode: str = "chat") -> int:
    now = _now_iso()
    cur = conn.execute(
        "INSERT INTO chats (created_at, updated_at, title, mode) VALUES (?, ?, ?, ?)",
        (now, now, title, mode),
    )
    conn.commit()
    return int(cur.lastrowid)


def list_chats(
    conn: sqlite3.Connection,
    *,
    mode: str | None = None,
    limit: int = 200,
) -> list[sqlite3.Row]:
    if mode:
        cur = conn.execute(
            "SELECT * FROM chats WHERE mode = ? ORDER BY updated_at DESC LIMIT ?",
            (mode, limit),
        )
    else:
        cur = conn.execute(
            "SELECT * FROM chats ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        )
    return list(cur.fetchall())


def get_chat(conn: sqlite3.Connection, chat_id: int) -> sqlite3.Row | None:
    cur = conn.execute("SELECT * FROM chats WHERE id = ?", (chat_id,))
    return cur.fetchone()


def list_runs_for_chat(conn: sqlite3.Connection, chat_id: int) -> list[sqlite3.Row]:
    cur = conn.execute(
        "SELECT * FROM runs WHERE chat_id = ? ORDER BY created_at ASC, id ASC",
        (chat_id,),
    )
    return list(cur.fetchall())


def touch_chat(conn: sqlite3.Connection, chat_id: int) -> None:
    conn.execute(
        "UPDATE chats SET updated_at = ? WHERE id = ?",
        (_now_iso(), chat_id),
    )
    conn.commit()


def update_chat_title(conn: sqlite3.Connection, chat_id: int, title: str) -> None:
    conn.execute(
        "UPDATE chats SET title = ?, updated_at = ? WHERE id = ?",
        (title, _now_iso(), chat_id),
    )
    conn.commit()


def delete_chat(conn: sqlite3.Connection, chat_id: int) -> None:
    conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
    conn.commit()


def insert_routine(
    conn: sqlite3.Connection,
    *,
    run_id: int,
    payload: dict[str, Any],
) -> int:
    cur = conn.execute(
        """
        INSERT INTO routines (
            run_id, created_at, objetivo, dias_por_semana, duracion_sesion, formato, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            _now_iso(),
            payload.get("objetivo", ""),
            payload.get("dias_por_semana"),
            payload.get("duracion_sesion"),
            payload.get("formato"),
            json.dumps(payload, ensure_ascii=False),
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def list_runs(
    conn: sqlite3.Connection,
    *,
    status: str | None = None,
    limit: int = 200,
) -> list[sqlite3.Row]:
    query = "SELECT * FROM runs"
    params: list[Any] = []
    if status:
        query += " WHERE status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    return list(conn.execute(query, params))


def get_run(conn: sqlite3.Connection, run_id: int) -> sqlite3.Row | None:
    cur = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
    return cur.fetchone()


def list_routines(
    conn: sqlite3.Connection,
    *,
    objetivo_contains: str | None = None,
    formato: str | None = None,
    limit: int = 200,
) -> list[sqlite3.Row]:
    query = "SELECT * FROM routines"
    clauses: list[str] = []
    params: list[Any] = []
    if objetivo_contains:
        clauses.append("objetivo LIKE ?")
        params.append(f"%{objetivo_contains}%")
    if formato:
        clauses.append("formato = ?")
        params.append(formato)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    return list(conn.execute(query, params))


def get_routine(conn: sqlite3.Connection, routine_id: int) -> sqlite3.Row | None:
    cur = conn.execute("SELECT * FROM routines WHERE id = ?", (routine_id,))
    return cur.fetchone()


def distinct_formatos(conn: sqlite3.Connection) -> list[str]:
    cur = conn.execute(
        "SELECT DISTINCT formato FROM routines WHERE formato IS NOT NULL ORDER BY formato"
    )
    return [row["formato"] for row in cur.fetchall()]
