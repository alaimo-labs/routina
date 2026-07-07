import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


def load_schema(schema_path: Path) -> dict[str, Any]:
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _format_path(error: ValidationError, lang: str) -> str:
    parts: list[str] = []
    for p in error.absolute_path:
        if isinstance(p, int):
            parts.append(f"[{p}]")
        else:
            if parts:
                parts.append(f".{p}")
            else:
                parts.append(str(p))
    if parts:
        return "".join(parts)
    return "(raíz)" if lang == "es" else "(root)"


_TYPE_NAMES = {
    "es": {
        "string": "texto",
        "integer": "número entero",
        "number": "número",
        "boolean": "booleano",
        "array": "lista",
        "object": "objeto",
        "null": "null",
    },
    "en": {
        "string": "a string",
        "integer": "an integer",
        "number": "a number",
        "boolean": "a boolean",
        "array": "an array",
        "object": "an object",
        "null": "null",
    },
}


def _message(error: ValidationError, lang: str) -> str:
    path = _format_path(error, lang)
    validator = error.validator
    es = lang == "es"

    if validator == "required":
        if "'" in error.message:
            missing = error.message.split("'")[1]
        else:
            missing = "campo desconocido" if es else "unknown field"
        if path in ("(raíz)", "(root)"):
            return (
                f"Falta el campo obligatorio '{missing}'."
                if es
                else f"Missing required field '{missing}'."
            )
        return (
            f"En '{path}' falta el campo obligatorio '{missing}'."
            if es
            else f"'{path}' is missing the required field '{missing}'."
        )

    if validator == "type":
        expected = error.validator_value
        expected_name = _TYPE_NAMES[lang].get(
            expected if isinstance(expected, str) else "", expected
        )
        return (
            f"'{path}' debería ser {expected_name}."
            if es
            else f"'{path}' should be {expected_name}."
        )

    if validator == "additionalProperties":
        return (
            f"Hay campos no esperados en '{path}': {error.message}"
            if es
            else f"Unexpected fields in '{path}': {error.message}"
        )

    if validator == "minLength":
        return f"'{path}' no puede estar vacío." if es else f"'{path}' cannot be empty."

    if validator == "minimum":
        return (
            f"'{path}' debería ser mayor o igual a {error.validator_value}."
            if es
            else f"'{path}' should be greater than or equal to {error.validator_value}."
        )

    if validator == "maximum":
        return (
            f"'{path}' debería ser menor o igual a {error.validator_value}."
            if es
            else f"'{path}' should be less than or equal to {error.validator_value}."
        )

    if validator == "minItems":
        return (
            f"'{path}' debería tener al menos {error.validator_value} elemento(s)."
            if es
            else f"'{path}' should have at least {error.validator_value} item(s)."
        )

    if validator == "maxItems":
        return (
            f"'{path}' debería tener como máximo {error.validator_value} elemento(s)."
            if es
            else f"'{path}' should have at most {error.validator_value} item(s)."
        )

    if validator == "enum":
        return (
            f"'{path}' debe ser uno de: {error.validator_value}."
            if es
            else f"'{path}' must be one of: {error.validator_value}."
        )

    return f"'{path}': {error.message}"


def validate_against_schema(
    data: Any, schema: dict[str, Any], lang: str = "es"
) -> tuple[bool, list[str]]:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if not errors:
        return True, []
    return False, [_message(e, lang) for e in errors]
