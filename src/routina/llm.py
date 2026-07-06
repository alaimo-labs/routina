import json
import time
from dataclasses import dataclass, field
from typing import Any

import anthropic
from google import genai
from google.genai import types as genai_types
from openai import OpenAI, OpenAIError

# Los tres proveedores se llaman SIN modo JSON del API (ni text.format de OpenAI, ni
# response_mime_type de Google): la instrucción de responder JSON vive únicamente en
# el system prompt. Así el user_input viaja intacto al proveedor (la traza de
# observabilidad coincide con lo persistido en DB) y la capa de parse_error se
# ejercita en igualdad de condiciones en los tres proveedores.

# max_tokens para los proveedores que lo exigen (Anthropic) o aceptan (Google).
_MAX_OUTPUT_TOKENS = 8192


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
    provider: str,
    api_key: str,
    model: str,
    user_input: str,
    system_prompt: str | None = None,
    prior_messages: list[dict[str, Any]] | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> LLMResult:
    """
    Genera una rutina llamando al proveedor indicado y devuelve un LLMResult uniforme.

    `prior_messages` permite multi-turno: si viene, los mensajes previos (roles
    user/assistant) van antes del nuevo `user_input`, dándole al LLM el contexto de
    la conversación. Ningún proveedor usa modo JSON del API: el formato se pide
    solo por prompting (system prompt), para que la validación en tres capas de la
    app siga siendo observable y comparable entre proveedores.
    """
    if provider == "anthropic":
        return _generate_anthropic(
            api_key=api_key,
            model=model,
            user_input=user_input,
            system_prompt=system_prompt,
            prior_messages=prior_messages,
        )
    if provider == "google":
        return _generate_google(
            api_key=api_key,
            model=model,
            user_input=user_input,
            system_prompt=system_prompt,
            prior_messages=prior_messages,
        )
    return _generate_openai(
        api_key=api_key,
        model=model,
        user_input=user_input,
        system_prompt=system_prompt,
        prior_messages=prior_messages,
        tools=tools,
    )


def _finalize(
    *,
    messages: list[dict[str, Any]],
    raw_text: str,
    api_error: str | None,
    latency_ms: int,
    input_tokens: int | None,
    output_tokens: int | None,
    model: str,
) -> LLMResult:
    """Parseo JSON común y armado del LLMResult para los tres proveedores."""
    parsed: dict[str, Any] | None = None
    parse_error: str | None = None

    if raw_text and not api_error:
        messages.append({"role": "assistant", "content": raw_text})
        # Sin modo JSON del API, cualquier proveedor puede envolver la respuesta en
        # un code fence markdown (```json ... ```). Lo quitamos solo para parsear;
        # `raw` conserva la respuesta original para la traza de evals.
        text_to_parse = _strip_code_fence(raw_text)
        try:
            parsed = json.loads(text_to_parse)
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
        model=model,
        num_turns=1,
        api_error=api_error,
        tool_calls=[],
    )


def _generate_openai(
    *,
    api_key: str,
    model: str,
    user_input: str,
    system_prompt: str | None,
    prior_messages: list[dict[str, Any]] | None,
    tools: list[dict[str, Any]] | None,
) -> LLMResult:
    client = OpenAI(api_key=api_key)

    prior = list(prior_messages or [])

    # `messages` es la traza que se persiste (incluye el system prompt si lo hay).
    messages: list[dict[str, Any]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(prior)
    messages.append({"role": "user", "content": user_input})

    input_messages = list(prior) + [{"role": "user", "content": user_input}]
    request_kwargs: dict[str, Any] = {
        "model": model,
        "input": input_messages,
    }
    if system_prompt:
        request_kwargs["instructions"] = system_prompt
    if tools:
        request_kwargs["tools"] = tools

    raw_text = ""
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

    return _finalize(
        messages=messages,
        raw_text=raw_text,
        api_error=api_error,
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model=used_model,
    )


def _generate_anthropic(
    *,
    api_key: str,
    model: str,
    user_input: str,
    system_prompt: str | None,
    prior_messages: list[dict[str, Any]] | None,
) -> LLMResult:
    client = anthropic.Anthropic(api_key=api_key)

    prior = list(prior_messages or [])

    # Traza persistida: replica la forma de OpenAI (system como primer mensaje).
    messages: list[dict[str, Any]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(prior)
    messages.append({"role": "user", "content": user_input})

    # La Messages API de Anthropic toma el system aparte y solo roles user/assistant.
    api_messages = list(prior) + [{"role": "user", "content": user_input}]

    raw_text = ""
    api_error: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    used_model = model

    request_kwargs: dict[str, Any] = {
        "model": model,
        "max_tokens": _MAX_OUTPUT_TOKENS,
        "messages": api_messages,
    }
    if system_prompt:
        request_kwargs["system"] = system_prompt

    start = time.perf_counter()
    try:
        response = client.messages.create(**request_kwargs)
        raw_text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )
        if getattr(response, "usage", None) is not None:
            input_tokens = getattr(response.usage, "input_tokens", None)
            output_tokens = getattr(response.usage, "output_tokens", None)
        used_model = getattr(response, "model", model) or model
    except anthropic.AnthropicError as exc:
        api_error = f"{type(exc).__name__}: {exc}"
    except Exception as exc:
        api_error = f"Error inesperado: {type(exc).__name__}: {exc}"
    latency_ms = int((time.perf_counter() - start) * 1000)

    return _finalize(
        messages=messages,
        raw_text=raw_text,
        api_error=api_error,
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model=used_model,
    )


def _generate_google(
    *,
    api_key: str,
    model: str,
    user_input: str,
    system_prompt: str | None,
    prior_messages: list[dict[str, Any]] | None,
) -> LLMResult:
    client = genai.Client(api_key=api_key)

    prior = list(prior_messages or [])

    # Traza persistida: misma forma que los otros proveedores.
    messages: list[dict[str, Any]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(prior)
    messages.append({"role": "user", "content": user_input})

    # Gemini usa roles "user"/"model" y estructura contents[].parts[].
    contents = [_to_gemini_content(m) for m in prior]
    contents.append(_to_gemini_content({"role": "user", "content": user_input}))

    gen_config = genai_types.GenerateContentConfig(
        max_output_tokens=_MAX_OUTPUT_TOKENS,
        system_instruction=system_prompt or None,
    )

    raw_text = ""
    api_error: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    used_model = model

    start = time.perf_counter()
    try:
        response = client.models.generate_content(
            model=model, contents=contents, config=gen_config
        )
        raw_text = getattr(response, "text", "") or ""
        usage = getattr(response, "usage_metadata", None)
        if usage is not None:
            input_tokens = getattr(usage, "prompt_token_count", None)
            output_tokens = getattr(usage, "candidates_token_count", None)
        used_model = getattr(response, "model_version", None) or model
    except genai.errors.APIError as exc:
        api_error = f"{type(exc).__name__}: {exc}"
    except Exception as exc:
        api_error = f"Error inesperado: {type(exc).__name__}: {exc}"
    latency_ms = int((time.perf_counter() - start) * 1000)

    return _finalize(
        messages=messages,
        raw_text=raw_text,
        api_error=api_error,
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model=used_model,
    )


def _strip_code_fence(text: str) -> str:
    """Quita un code fence markdown (```json ... ``` o ``` ... ```) que rodee todo
    el texto. Si no hay fence, devuelve el texto tal cual (con trim). Solo se
    considera fence si la línea de apertura es ``` opcionalmente seguida de un
    identificador de lenguaje (sin espacios), para no tocar contenido legítimo."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    newline = stripped.find("\n")
    if newline == -1:
        return stripped
    lang_tag = stripped[3:newline].strip()
    if " " in lang_tag:  # no es un fence de apertura típico
        return stripped

    body = stripped[newline + 1 :]
    closing = body.rfind("```")
    if closing != -1:
        body = body[:closing]
    return body.strip()


def _to_gemini_content(message: dict[str, Any]) -> dict[str, Any]:
    """Convierte un mensaje {role, content} al formato contents[] de Gemini."""
    role = "model" if message.get("role") == "assistant" else "user"
    return {"role": role, "parts": [{"text": message.get("content", "")}]}
