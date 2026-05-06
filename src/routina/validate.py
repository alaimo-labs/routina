import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


def load_schema(schema_path: Path) -> dict[str, Any]:
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _format_path(error: ValidationError) -> str:
    parts: list[str] = []
    for p in error.absolute_path:
        if isinstance(p, int):
            parts.append(f"[{p}]")
        else:
            if parts:
                parts.append(f".{p}")
            else:
                parts.append(str(p))
    return "".join(parts) if parts else "(raíz)"


def _spanish_message(error: ValidationError) -> str:
    path = _format_path(error)
    validator = error.validator

    if validator == "required":
        missing = error.message.split("'")[1] if "'" in error.message else "campo desconocido"
        if path == "(raíz)":
            return f"Falta el campo obligatorio '{missing}'."
        return f"En '{path}' falta el campo obligatorio '{missing}'."

    if validator == "type":
        expected = error.validator_value
        expected_es = {
            "string": "texto",
            "integer": "número entero",
            "number": "número",
            "boolean": "booleano",
            "array": "lista",
            "object": "objeto",
            "null": "null",
        }.get(expected if isinstance(expected, str) else "", expected)
        return f"'{path}' debería ser {expected_es}."

    if validator == "additionalProperties":
        return f"Hay campos no esperados en '{path}': {error.message}"

    if validator == "minLength":
        return f"'{path}' no puede estar vacío."

    if validator == "minimum":
        return f"'{path}' debería ser mayor o igual a {error.validator_value}."

    if validator == "maximum":
        return f"'{path}' debería ser menor o igual a {error.validator_value}."

    if validator == "minItems":
        return f"'{path}' debería tener al menos {error.validator_value} elemento(s)."

    if validator == "enum":
        return f"'{path}' debe ser uno de: {error.validator_value}."

    return f"'{path}': {error.message}"


def validate_against_schema(
    data: Any, schema: dict[str, Any]
) -> tuple[bool, list[str]]:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if not errors:
        return True, []
    return False, [_spanish_message(e) for e in errors]
