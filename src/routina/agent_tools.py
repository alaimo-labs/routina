"""Tools del modo agente: definiciones neutrales + ejecución server-side.

Las definiciones son provider-neutral ({name, description, parameters}) y `llm.py`
las convierte al formato de cada proveedor. La ejecución vive acá (con acceso a
db/catalog/validate); `preguntar_usuario` NO se ejecuta: es una tool terminal que
corta el loop y devuelve las preguntas al usuario (ver llm.run_agent).
"""

import json
from typing import Any

from . import catalog, config, db, validate

# Tool terminal: al llamarla, el loop se corta y el run termina con el sobre
# {tipo: "preguntas", ...}. La respuesta del usuario llega como próximo mensaje.
USER_TOOL = "preguntar_usuario"

# Cap de resultados de buscar_ejercicios para no inflar el contexto del modelo.
_MAX_RESULTADOS = 30

# Schema simplificado de la rutina para parámetros de tools (sin additionalProperties
# ni minLength, que el function calling de Gemini no soporta). La validación real la
# hace validar_rutina/guardar_rutina contra schemas/routina_v1.json.
_RUTINA_PARAM = {
    "type": "object",
    "description": "La rutina completa en el formato de Routina.",
    "properties": {
        "objetivo": {"type": "string"},
        "dias_por_semana": {"type": "integer"},
        "duracion_sesion": {"type": "integer", "description": "Minutos por sesión."},
        "formato": {"type": "string"},
        "ejercicios": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string"},
                    "series": {"type": "integer"},
                    "repeticiones": {"type": "string"},
                    "descanso_seg": {"type": "integer"},
                    "notas": {"type": "string"},
                },
                "required": ["nombre", "series", "repeticiones", "descanso_seg", "notas"],
            },
        },
        "notas_generales": {"type": "string"},
        "advertencia": {"type": "string"},
    },
    "required": [
        "objetivo",
        "dias_por_semana",
        "duracion_sesion",
        "formato",
        "ejercicios",
        "notas_generales",
        "advertencia",
    ],
}


def tool_defs() -> list[dict[str, Any]]:
    grupos = sorted(catalog.valid_ids("grupos_musculares"))
    niveles = list(catalog.load_catalog()["niveles"])
    equipamiento = sorted(catalog.valid_ids("equipamiento"))
    lesiones = sorted(catalog.valid_ids("lesiones"))
    return [
        {
            "name": "leer_perfil",
            "description": (
                "Lee el perfil del usuario: equipamiento disponible, lesiones o "
                "molestias, y notas libres. Consúltalo antes de hacer preguntas."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "buscar_ejercicios",
            "description": (
                "Busca ejercicios en el catálogo curado. Todos los filtros son "
                "opcionales y combinables. Prescribe únicamente ejercicios devueltos "
                "por esta tool, usando su campo 'nombre' tal cual."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "grupo": {
                        "type": "string",
                        "enum": grupos,
                        "description": "Grupo muscular a trabajar.",
                    },
                    "nivel": {
                        "type": "string",
                        "enum": niveles,
                        "description": "Nivel del usuario; incluye ejercicios de ese nivel o inferior.",
                    },
                    "equipamiento": {
                        "type": "array",
                        "items": {"type": "string", "enum": equipamiento},
                        "description": (
                            "Equipamiento disponible del usuario. Solo devuelve "
                            "ejercicios realizables con ese equipamiento (lista vacía "
                            "= solo ejercicios sin equipamiento). Si se omite, no filtra."
                        ),
                    },
                    "evitar_lesiones": {
                        "type": "array",
                        "items": {"type": "string", "enum": lesiones},
                        "description": "Excluye ejercicios contraindicados para estas lesiones.",
                    },
                },
            },
        },
        {
            "name": USER_TOOL,
            "description": (
                "Hace preguntas al usuario con opciones para elegir (multiple choice). "
                "Úsala solo para información que falte y que el perfil no responda. "
                "Máximo 3 preguntas por llamada. La conversación se pausa hasta que "
                "el usuario responda."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "preguntas": {
                        "type": "array",
                        "description": "Entre 1 y 3 preguntas.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": "Identificador corto, ej. 'objetivo'.",
                                },
                                "pregunta": {"type": "string"},
                                "opciones": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Entre 2 y 5 opciones concretas.",
                                },
                                "multiple": {
                                    "type": "boolean",
                                    "description": "true si puede elegir varias opciones.",
                                },
                            },
                            "required": ["id", "pregunta", "opciones"],
                        },
                    }
                },
                "required": ["preguntas"],
            },
        },
        {
            "name": "validar_rutina",
            "description": (
                "Valida una rutina contra el schema oficial de Routina. Úsala antes "
                "de entregar la rutina; si devuelve errores, corrígelos y revalida."
            ),
            "parameters": {
                "type": "object",
                "properties": {"rutina": _RUTINA_PARAM},
                "required": ["rutina"],
            },
        },
        {
            "name": "guardar_rutina",
            "description": (
                "Valida y guarda la rutina en la biblioteca del usuario. Úsala solo "
                "cuando el usuario lo pida o lo confirme."
            ),
            "parameters": {
                "type": "object",
                "properties": {"rutina": _RUTINA_PARAM},
                "required": ["rutina"],
            },
        },
    ]


def execute(
    name: str,
    args: dict[str, Any],
    *,
    saved_routine_ids: list[int],
) -> dict[str, Any]:
    """Ejecuta una tool server-side y devuelve su resultado como dict serializable.

    Los errores se devuelven como {"error": ...} para que el agente pueda reaccionar
    (y queden observables en la traza) en lugar de romper el loop.
    """
    try:
        if name == "leer_perfil":
            conn = db.get_conn()
            try:
                return db.get_profile(conn)
            finally:
                conn.close()

        if name == "buscar_ejercicios":
            ejercicios = catalog.search(
                grupo=args.get("grupo"),
                nivel=args.get("nivel"),
                equipamiento_disponible=args.get("equipamiento"),
                evitar_lesiones=args.get("evitar_lesiones"),
            )
            total = len(ejercicios)
            return {
                "total": total,
                "truncado": total > _MAX_RESULTADOS,
                "ejercicios": ejercicios[:_MAX_RESULTADOS],
            }

        if name == "validar_rutina":
            return _validar(args.get("rutina"))

        if name == "guardar_rutina":
            resultado = _validar(args.get("rutina"))
            if not resultado["valida"]:
                return {"guardada": False, **resultado}
            conn = db.get_conn()
            try:
                # El run todavía no existe (el loop sigue corriendo); se inserta sin
                # run_id y el server lo linkea después de persistir el run.
                routine_id = db.insert_routine(conn, run_id=None, payload=args["rutina"])
            finally:
                conn.close()
            saved_routine_ids.append(routine_id)
            return {"guardada": True, "routine_id": routine_id}

        return {"error": f"Tool desconocida: {name}"}
    except Exception as exc:  # pragma: no cover - red de seguridad
        return {"error": f"{type(exc).__name__}: {exc}"}


def _validar(rutina: Any) -> dict[str, Any]:
    if not isinstance(rutina, dict):
        return {"valida": False, "errores": ["El parámetro 'rutina' debe ser un objeto."]}
    schema = validate.load_schema(config.SCHEMA_PATHS["oneshot"])
    ok, errores = validate.validate_against_schema(rutina, schema)
    return {"valida": ok, "errores": errores}
