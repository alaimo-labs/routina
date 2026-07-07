"""Tools del modo agente: definiciones neutrales + ejecución server-side.

Las definiciones son provider-neutral ({name, description, parameters}) y `llm.py`
las convierte al formato de cada proveedor. La ejecución vive acá (con acceso a
db/catalog/validate); `ask_user` NO se ejecuta: es una tool terminal que corta el
loop y devuelve las preguntas al usuario (ver llm.run_agent).

Los nombres de tools, los IDs del vocabulario y las claves de los resultados son
en inglés (estructura del contrato); las descripciones y los contenidos de texto
(nombres de ejercicios, errores de validación) se localizan según `lang`.
"""

import json
from typing import Any

from . import catalog, config, db, validate

# Tool terminal: al llamarla, el loop se corta y el run termina con el sobre
# {type: "questions", ...}. La respuesta del usuario llega como próximo mensaje.
USER_TOOL = "ask_user"

# Cap de resultados de search_exercises para no inflar el contexto del modelo.
_MAX_RESULTS = 30

# Schema simplificado de la rutina para parámetros de tools (sin additionalProperties
# ni minLength, que el function calling de Gemini no soporta). La validación real la
# hace validate_routine/save_routine contra schemas/routina_v1.json.
_ROUTINE_PARAM = {
    "type": "object",
    "description": "La rutina completa en el formato de Routina.",
    "properties": {
        "goal": {"type": "string"},
        "days_per_week": {"type": "integer"},
        "session_duration": {"type": "integer", "description": "Minutos por sesión."},
        "format": {"type": "string"},
        "exercises": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "sets": {"type": "integer"},
                    "reps": {"type": "string"},
                    "rest_sec": {"type": "integer"},
                    "notes": {"type": "string"},
                },
                "required": ["name", "sets", "reps", "rest_sec", "notes"],
            },
        },
        "general_notes": {"type": "string"},
        "warning": {"type": "string"},
    },
    "required": [
        "goal",
        "days_per_week",
        "session_duration",
        "format",
        "exercises",
        "general_notes",
        "warning",
    ],
}

# Descripciones de tools y parámetros por idioma. La estructura (nombres, enums,
# tipos) es idéntica en ambos; solo cambia el texto que lee el modelo.
_DESC = {
    "es": {
        "read_profile": (
            "Lee el perfil del usuario: equipamiento disponible, lesiones o "
            "molestias, y notas libres. Consúltalo antes de hacer preguntas."
        ),
        "search_exercises": (
            "Busca ejercicios en el catálogo curado. Todos los filtros son "
            "opcionales y combinables. Prescribe únicamente ejercicios devueltos "
            "por esta tool, usando su campo 'name' tal cual."
        ),
        "search.muscle_group": "Grupo muscular a trabajar.",
        "search.level": "Nivel del usuario; incluye ejercicios de ese nivel o inferior.",
        "search.equipment": (
            "Equipamiento disponible del usuario. Solo devuelve ejercicios "
            "realizables con ese equipamiento (lista vacía = solo ejercicios sin "
            "equipamiento). Si se omite, no filtra."
        ),
        "search.avoid_injuries": "Excluye ejercicios contraindicados para estas lesiones.",
        "ask_user": (
            "Hace preguntas al usuario con opciones para elegir (multiple choice). "
            "Úsala solo para información que falte y que el perfil no responda. "
            "Máximo 3 preguntas por llamada. La conversación se pausa hasta que "
            "el usuario responda."
        ),
        "ask.questions": "Entre 1 y 3 preguntas.",
        "ask.id": "Identificador corto, ej. 'goal'.",
        "ask.options": "Entre 2 y 5 opciones concretas.",
        "ask.multiple": "true si puede elegir varias opciones.",
        "validate_routine": (
            "Valida una rutina contra el schema oficial de Routina. Úsala antes "
            "de entregar la rutina; si devuelve errores, corrígelos y revalida."
        ),
        "save_routine": (
            "Valida y guarda la rutina en la biblioteca del usuario. Úsala solo "
            "cuando el usuario lo pida o lo confirme."
        ),
    },
    "en": {
        "read_profile": (
            "Reads the user's profile: available equipment, injuries or "
            "discomforts, and free-form notes. Check it before asking questions."
        ),
        "search_exercises": (
            "Searches the curated exercise catalog. All filters are optional and "
            "combinable. Prescribe only exercises returned by this tool, using "
            "their 'name' field verbatim."
        ),
        "search.muscle_group": "Muscle group to train.",
        "search.level": "User level; includes exercises of that level or below.",
        "search.equipment": (
            "The user's available equipment. Only returns exercises doable with "
            "that equipment (empty list = only equipment-free exercises). If "
            "omitted, no filtering."
        ),
        "search.avoid_injuries": "Excludes exercises contraindicated for these injuries.",
        "ask_user": (
            "Asks the user multiple-choice questions. Use it only for missing "
            "information that the profile doesn't answer. At most 3 questions "
            "per call. The conversation pauses until the user answers."
        ),
        "ask.questions": "Between 1 and 3 questions.",
        "ask.id": "Short identifier, e.g. 'goal'.",
        "ask.options": "Between 2 and 5 concrete options.",
        "ask.multiple": "true if several options can be chosen.",
        "validate_routine": (
            "Validates a routine against the official Routina schema. Use it "
            "before delivering the routine; if it returns errors, fix them and "
            "revalidate."
        ),
        "save_routine": (
            "Validates and saves the routine to the user's library. Use it only "
            "when the user asks for it or confirms."
        ),
    },
}


def tool_defs(lang: str = "es") -> list[dict[str, Any]]:
    d = _DESC.get(lang, _DESC["es"])
    muscle_groups = sorted(catalog.valid_ids("muscle_groups"))
    levels = list(catalog.load_catalog()["levels"])
    equipment = sorted(catalog.valid_ids("equipment"))
    injuries = sorted(catalog.valid_ids("injuries"))
    return [
        {
            "name": "read_profile",
            "description": d["read_profile"],
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "search_exercises",
            "description": d["search_exercises"],
            "parameters": {
                "type": "object",
                "properties": {
                    "muscle_group": {
                        "type": "string",
                        "enum": muscle_groups,
                        "description": d["search.muscle_group"],
                    },
                    "level": {
                        "type": "string",
                        "enum": levels,
                        "description": d["search.level"],
                    },
                    "equipment": {
                        "type": "array",
                        "items": {"type": "string", "enum": equipment},
                        "description": d["search.equipment"],
                    },
                    "avoid_injuries": {
                        "type": "array",
                        "items": {"type": "string", "enum": injuries},
                        "description": d["search.avoid_injuries"],
                    },
                },
            },
        },
        {
            "name": USER_TOOL,
            "description": d["ask_user"],
            "parameters": {
                "type": "object",
                "properties": {
                    "questions": {
                        "type": "array",
                        "description": d["ask.questions"],
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": d["ask.id"],
                                },
                                "question": {"type": "string"},
                                "options": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": d["ask.options"],
                                },
                                "multiple": {
                                    "type": "boolean",
                                    "description": d["ask.multiple"],
                                },
                            },
                            "required": ["id", "question", "options"],
                        },
                    }
                },
                "required": ["questions"],
            },
        },
        {
            "name": "validate_routine",
            "description": d["validate_routine"],
            "parameters": {
                "type": "object",
                "properties": {"routine": _ROUTINE_PARAM},
                "required": ["routine"],
            },
        },
        {
            "name": "save_routine",
            "description": d["save_routine"],
            "parameters": {
                "type": "object",
                "properties": {"routine": _ROUTINE_PARAM},
                "required": ["routine"],
            },
        },
    ]


def execute(
    name: str,
    args: dict[str, Any],
    *,
    saved_routine_ids: list[int],
    lang: str = "es",
) -> dict[str, Any]:
    """Ejecuta una tool server-side y devuelve su resultado como dict serializable.

    Los errores se devuelven como {"error": ...} para que el agente pueda reaccionar
    (y queden observables en la traza) en lugar de romper el loop. `lang` localiza
    los contenidos de texto (nombres/notas de ejercicios, errores de validación).
    """
    try:
        if name == "read_profile":
            conn = db.get_conn()
            try:
                return db.get_profile(conn)
            finally:
                conn.close()

        if name == "search_exercises":
            exercises = catalog.search(
                muscle_group=args.get("muscle_group"),
                level=args.get("level"),
                available_equipment=args.get("equipment"),
                avoid_injuries=args.get("avoid_injuries"),
            )
            total = len(exercises)
            return {
                "total": total,
                "truncated": total > _MAX_RESULTS,
                "exercises": [
                    catalog.localized(ex, lang) for ex in exercises[:_MAX_RESULTS]
                ],
            }

        if name == "validate_routine":
            return _validate(args.get("routine"), lang)

        if name == "save_routine":
            result = _validate(args.get("routine"), lang)
            if not result["valid"]:
                return {"saved": False, **result}
            conn = db.get_conn()
            try:
                # El run todavía no existe (el loop sigue corriendo); se inserta sin
                # run_id y el server lo linkea después de persistir el run.
                routine_id = db.insert_routine(conn, run_id=None, payload=args["routine"])
            finally:
                conn.close()
            saved_routine_ids.append(routine_id)
            return {"saved": True, "routine_id": routine_id}

        return {"error": f"Unknown tool: {name}"}
    except Exception as exc:  # pragma: no cover - red de seguridad
        return {"error": f"{type(exc).__name__}: {exc}"}


def _validate(routine: Any, lang: str) -> dict[str, Any]:
    if not isinstance(routine, dict):
        msg = (
            "El parámetro 'routine' debe ser un objeto."
            if lang == "es"
            else "The 'routine' parameter must be an object."
        )
        return {"valid": False, "errors": [msg]}
    schema = validate.load_schema(config.SCHEMA_PATHS["oneshot"])
    ok, errors = validate.validate_against_schema(routine, schema, lang)
    return {"valid": ok, "errors": errors}
