import json
import time
from dataclasses import dataclass, field
from typing import Any, Literal

from openai import OpenAI, OpenAIError

PromptMode = Literal["local", "openai_id"]

# Guardrail de la Responses API: cuando se usa text.format=json_object, al menos un
# mensaje de `input` tiene que contener la palabra "json". El system prompt en
# `instructions` no cuenta para ese chequeo. Anexamos este sufijo al contenido que
# enviamos al modelo. El user_input original (sin sufijo) se preserva intacto en DB.
_JSON_HINT_SUFFIX = "\n\nResponde en formato JSON."


@dataclass
class LLMResult:
    messages: list[dict[str, Any]]
    raw: str
    parsed: dict[str, Any] | None
    parse_error: str | None
    latency_ms: int
    input_tokens: int | None
    output_tokens: int | None
    model: str
    num_turns: int
    api_error: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


def generate_routine(
    *,
    api_key: str,
    model: str,
    user_input: str,
    prompt_mode: PromptMode,
    system_prompt: str | None = None,
    prompt_id: str | None = None,
    prompt_version: str | None = None,
    prior_messages: list[dict[str, Any]] | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> LLMResult:
    """
    Llama a OpenAI Responses API y devuelve un LLMResult uniforme.

    `prior_messages` permite multi-turno: si viene, los mensajes previos van en el
    `input` antes del nuevo user_input, dándole al LLM contexto de la conversación.
    """
    client = OpenAI(api_key=api_key)

    user_content_for_api = user_input + _JSON_HINT_SUFFIX
    prior = list(prior_messages or [])

    messages: list[dict[str, Any]] = []
    if prompt_mode == "local":
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
    messages.extend(prior)
    messages.append({"role": "user", "content": user_content_for_api})

    request_kwargs: dict[str, Any] = {
        "model": model,
        "text": {"format": {"type": "json_object"}},
    }

    input_messages = list(prior) + [{"role": "user", "content": user_content_for_api}]

    if prompt_mode == "local":
        if system_prompt:
            request_kwargs["instructions"] = system_prompt
        request_kwargs["input"] = input_messages
    else:
        prompt_obj: dict[str, Any] = {"id": prompt_id}
        if prompt_version:
            prompt_obj["version"] = prompt_version
        request_kwargs["prompt"] = prompt_obj
        request_kwargs["input"] = input_messages

    if tools:
        request_kwargs["tools"] = tools

    raw_text = ""
    parsed: dict[str, Any] | None = None
    parse_error: str | None = None
    api_error: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    used_model = model

    start = time.perf_counter()
    try:
        response = client.responses.create(**request_kwargs)
        raw_text = getattr(response, "output_text", "") or ""
        if hasattr(response, "usage") and response.usage is not None:
            input_tokens = getattr(response.usage, "input_tokens", None)
            output_tokens = getattr(response.usage, "output_tokens", None)
        used_model = getattr(response, "model", model) or model
    except OpenAIError as exc:
        api_error = f"{type(exc).__name__}: {exc}"
    except Exception as exc:  # red de seguridad para un mensaje legible en UI
        api_error = f"Error inesperado: {type(exc).__name__}: {exc}"
    latency_ms = int((time.perf_counter() - start) * 1000)

    if raw_text and not api_error:
        messages.append({"role": "assistant", "content": raw_text})
        try:
            parsed = json.loads(raw_text)
            if not isinstance(parsed, dict):
                parse_error = "El JSON devuelto no es un objeto en la raíz."
                parsed = None
        except json.JSONDecodeError as exc:
            parse_error = f"JSON inválido en línea {exc.lineno}, columna {exc.colno}: {exc.msg}"

    return LLMResult(
        messages=messages,
        raw=raw_text,
        parsed=parsed,
        parse_error=parse_error,
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model=used_model,
        num_turns=1,
        api_error=api_error,
        tool_calls=[],
    )
