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
    # Estado nativo del loop agéntico cuando quedó pausado esperando la respuesta
    # del usuario (ask_user). El server lo persiste y lo devuelve en el
    # próximo turno para reanudar con un tool_result nativo. None = no hay pausa.
    pending_state: dict[str, Any] | None = None


def generate_routine(
    *,
    provider: str,
    api_key: str,
    model: str,
    user_input: str,
    system_prompt: str | None = None,
    prior_messages: list[dict[str, Any]] | None = None,
    tools: list[dict[str, Any]] | None = None,
    lang: str = "es",
) -> LLMResult:
    """
    Genera una rutina llamando al proveedor indicado y devuelve un LLMResult uniforme.

    `prior_messages` permite multi-turno: si viene, los mensajes previos (roles
    user/assistant) van antes del nuevo `user_input`, dándole al LLM el contexto de
    la conversación. Ningún proveedor usa modo JSON del API: el formato se pide
    solo por prompting (system prompt), para que la validación en tres capas de la
    app siga siendo observable y comparable entre proveedores. `lang` solo localiza
    los mensajes de error visibles en la UI (parse_error, api_error inesperado).
    """
    if provider == "anthropic":
        return _generate_anthropic(
            api_key=api_key,
            model=model,
            user_input=user_input,
            system_prompt=system_prompt,
            prior_messages=prior_messages,
            lang=lang,
        )
    if provider == "google":
        return _generate_google(
            api_key=api_key,
            model=model,
            user_input=user_input,
            system_prompt=system_prompt,
            prior_messages=prior_messages,
            lang=lang,
        )
    return _generate_openai(
        api_key=api_key,
        model=model,
        user_input=user_input,
        system_prompt=system_prompt,
        prior_messages=prior_messages,
        tools=tools,
        lang=lang,
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
    lang: str = "es",
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
                parse_error = (
                    "El JSON devuelto no es un objeto en la raíz."
                    if lang == "es"
                    else "The returned JSON is not an object at the root."
                )
                parsed = None
        except json.JSONDecodeError as exc:
            parse_error = (
                f"JSON inválido en línea {exc.lineno}, columna {exc.colno}: {exc.msg}"
                if lang == "es"
                else f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
            )

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
    lang: str = "es",
) -> LLMResult:
    client = OpenAI(api_key=api_key)

    prior = list(prior_messages or [])

    # `messages` es la traza que se persiste (incluye el system prompt si lo hay).
    messages: list[dict[str, Any]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(dict(m) for m in prior)
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
        lang=lang,
    )


def _generate_anthropic(
    *,
    api_key: str,
    model: str,
    user_input: str,
    system_prompt: str | None,
    prior_messages: list[dict[str, Any]] | None,
    lang: str = "es",
) -> LLMResult:
    client = anthropic.Anthropic(api_key=api_key)

    prior = list(prior_messages or [])

    # Traza persistida: replica la forma de OpenAI (system como primer mensaje).
    messages: list[dict[str, Any]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(dict(m) for m in prior)
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
        lang=lang,
    )


def _generate_google(
    *,
    api_key: str,
    model: str,
    user_input: str,
    system_prompt: str | None,
    prior_messages: list[dict[str, Any]] | None,
    lang: str = "es",
) -> LLMResult:
    client = genai.Client(api_key=api_key)

    prior = list(prior_messages or [])

    # Traza persistida: misma forma que los otros proveedores.
    messages: list[dict[str, Any]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(dict(m) for m in prior)
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
        lang=lang,
    )


# ======================================================================================
# Loop agéntico (modo /agent)
# ======================================================================================
# El loop llama al proveedor con tools; ejecuta las tools server-side vía
# `tool_executor` y vuelve a llamar, hasta que el modelo responde texto (el sobre
# JSON final) o llama a `ask_user`. En ese caso el loop se PAUSA: se sintetiza el
# sobre {type: "questions", ...} para la UI y se captura el estado nativo de la
# conversación (mensajes provider-native, todos dicts serializables) en
# `pending_state`. El server lo persiste por chat, y cuando el usuario responde
# se reanuda el loop entregando la respuesta como tool_result NATIVO del
# ask_user — no como un mensaje user sintético.

MAX_AGENT_ITERATIONS = 8
_USER_TOOL = "ask_user"


def run_agent(
    *,
    provider: str,
    api_key: str,
    model: str,
    user_input: str,
    system_prompt: str | None,
    prior_messages: list[dict[str, Any]] | None,
    tools: list[dict[str, Any]],
    tool_executor: Any,
    on_tool_start: Any = None,
    resume_state: dict[str, Any] | None = None,
    lang: str = "es",
) -> LLMResult:
    """Corre el loop agéntico en el proveedor indicado y devuelve un LLMResult uniforme.

    `tools` son definiciones neutrales ({name, description, parameters}); acá se
    convierten al formato de cada proveedor. `tool_executor(name, args) -> dict`
    ejecuta las tools server-side. `on_tool_start(name)` (opcional) se invoca al
    comenzar cada tool — lo usa el server para streamear progreso a la UI.

    Si `resume_state` viene (el `pending_state` de un run anterior pausado en
    ask_user), el loop se reanuda desde la conversación nativa guardada y
    `user_input` viaja como el tool_result de esa llamada, no como mensaje user.
    """
    if provider == "anthropic":
        runner = _agent_anthropic
    elif provider == "google":
        runner = _agent_google
    else:
        runner = _agent_openai

    # Copias defensivas: estos dicts van tanto a la traza persistida como al request
    # del proveedor; los SDKs (o su instrumentación) pueden mutarlos in-place y
    # contaminarían la traza con campos espurios.
    prior = [dict(m) for m in (prior_messages or [])]
    # Traza persistida: misma forma que los otros modos + entradas de tools.
    trace: list[dict[str, Any]] = []
    if system_prompt:
        trace.append({"role": "system", "content": system_prompt})
    if resume_state:
        # La conversación previa del loop pausado (incluida la llamada a
        # ask_user), tal como la sigue viendo el proveedor.
        trace.extend(resume_state.get("trace_prefix") or [])
        trace.append(
            {
                "role": "tool_result",
                "name": _USER_TOOL,
                "result": {"user_answers": user_input},
            }
        )
    else:
        trace.extend(dict(m) for m in prior)
        trace.append({"role": "user", "content": user_input})

    state = _AgentState(trace=trace, on_tool_start=on_tool_start, lang=lang)

    def _executor_with_notify(name: str, args: dict[str, Any]) -> dict[str, Any]:
        state.notify(name)
        return tool_executor(name, args)

    start = time.perf_counter()
    try:
        raw_text = runner(
            api_key=api_key,
            model=model,
            user_input=user_input,
            system_prompt=system_prompt,
            prior=prior,
            tools=tools,
            tool_executor=_executor_with_notify,
            state=state,
            resume_state=resume_state,
        )
    except Exception as exc:  # red de seguridad para un mensaje legible en UI
        state.api_error = state.api_error or f"Error inesperado: {type(exc).__name__}: {exc}"
        raw_text = ""
    latency_ms = int((time.perf_counter() - start) * 1000)

    result = _finalize(
        messages=state.trace,
        raw_text=raw_text,
        api_error=state.api_error,
        latency_ms=latency_ms,
        input_tokens=state.input_tokens if state.iterations else None,
        output_tokens=state.output_tokens if state.iterations else None,
        model=state.used_model or model,
        lang=lang,
    )
    result.num_turns = max(state.iterations, 1)
    result.tool_calls = state.tool_calls
    result.pending_state = state.pending_state
    return result


@dataclass
class _AgentState:
    trace: list[dict[str, Any]]
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    iterations: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    used_model: str | None = None
    api_error: str | None = None
    on_tool_start: Any = None
    pending_state: dict[str, Any] | None = None
    lang: str = "es"

    def add_usage(self, input_tokens: int | None, output_tokens: int | None) -> None:
        self.input_tokens += input_tokens or 0
        self.output_tokens += output_tokens or 0

    def notify(self, name: str) -> None:
        """Avisa (best-effort) que arranca una tool; el server lo streamea a la UI."""
        if self.on_tool_start:
            try:
                self.on_tool_start(name)
            except Exception:
                pass

    def record_call(self, name: str, args: dict[str, Any], result: Any) -> None:
        # Round-trip por JSON: los SDKs pueden devolver args con tipos propios
        # (proto/pydantic) que romperían el json.dumps al persistir el run.
        args = json.loads(json.dumps(args, ensure_ascii=False, default=str))
        result = json.loads(json.dumps(result, ensure_ascii=False, default=str))
        self.tool_calls.append({"name": name, "args": args, "result": result})
        self.trace.append({"role": "tool_call", "name": name, "args": args})
        self.trace.append({"role": "tool_result", "name": name, "result": result})


def _preguntas_terminal(state: _AgentState, args: dict[str, Any]) -> str:
    """Sintetiza el sobre {type: questions} cuando el agente llama a ask_user.

    Además guarda en `pending_state` un snapshot de la traza neutral hasta la
    llamada a ask_user inclusive ("trace_prefix"): el run reanudado lo antepone a
    su propia traza, para que messages_json refleje la conversación completa que
    el proveedor realmente ve al continuar el loop.
    """
    state.notify(_USER_TOOL)
    args = json.loads(json.dumps(args, ensure_ascii=False, default=str))
    envelope = {"type": "questions", "questions": args.get("questions", [])}

    state.tool_calls.append(
        {"name": _USER_TOOL, "args": args, "result": {"status": "waiting_for_user_answer"}}
    )
    state.trace.append({"role": "tool_call", "name": _USER_TOOL, "args": args})
    if state.pending_state is not None:
        # Snapshot (deep copy) sin el system: el run reanudado antepone el suyo.
        prefix = [m for m in state.trace if m.get("role") != "system"]
        state.pending_state["trace_prefix"] = json.loads(json.dumps(prefix, ensure_ascii=False))
    state.trace.append(
        {"role": "tool_result", "name": _USER_TOOL, "result": {"status": "waiting_for_user_answer"}}
    )
    return json.dumps(envelope, ensure_ascii=False)


def _max_iter_error(state: _AgentState) -> str:
    state.api_error = (
        f"El agente superó el máximo de {MAX_AGENT_ITERATIONS} iteraciones sin respuesta final."
        if state.lang == "es"
        else f"The agent exceeded the maximum of {MAX_AGENT_ITERATIONS} iterations without a final answer."
    )
    return ""


def _user_tool_result_payload(user_input: str) -> str:
    return json.dumps({"user_answers": user_input}, ensure_ascii=False)


def _agent_openai(
    *,
    api_key: str,
    model: str,
    user_input: str,
    system_prompt: str | None,
    prior: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    tool_executor: Any,
    state: _AgentState,
    resume_state: dict[str, Any] | None,
) -> str:
    client = OpenAI(api_key=api_key)
    oai_tools = [
        {
            "type": "function",
            "name": t["name"],
            "description": t["description"],
            "parameters": t["parameters"],
        }
        for t in tools
    ]
    if resume_state:
        # Reanudación: la respuesta del usuario viaja como function_call_output
        # del ask_user pendiente, sobre la conversación nativa guardada.
        input_items: list[Any] = list(resume_state["native_messages"])
        input_items.append(
            {
                "type": "function_call_output",
                "call_id": resume_state["pending"]["call_id"],
                "output": _user_tool_result_payload(user_input),
            }
        )
    else:
        input_items = list(prior) + [{"role": "user", "content": user_input}]

    while state.iterations < MAX_AGENT_ITERATIONS:
        state.iterations += 1
        try:
            response = client.responses.create(
                model=model,
                input=input_items,
                instructions=system_prompt or None,
                tools=oai_tools,
            )
        except OpenAIError as exc:
            state.api_error = f"{type(exc).__name__}: {exc}"
            return ""
        if response.usage is not None:
            state.add_usage(response.usage.input_tokens, response.usage.output_tokens)
        state.used_model = getattr(response, "model", None) or model

        fn_calls = [item for item in response.output if item.type == "function_call"]
        if not fn_calls:
            return response.output_text or ""

        # Se guardan como dicts (no objetos del SDK) para que el estado pendiente
        # sea serializable si hay pausa.
        input_items.extend(
            item.model_dump(exclude_none=True) for item in response.output
        )
        ask_call = None
        for call in fn_calls:
            if call.name == _USER_TOOL:
                ask_call = call
                continue
            args = json.loads(call.arguments or "{}")
            result = tool_executor(call.name, args)
            state.record_call(call.name, args, result)
            input_items.append(
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": json.dumps(result, ensure_ascii=False),
                }
            )
        if ask_call is not None:
            state.pending_state = {
                "native_messages": input_items,
                "pending": {"call_id": ask_call.call_id},
            }
            return _preguntas_terminal(state, json.loads(ask_call.arguments or "{}"))
    return _max_iter_error(state)


def _agent_anthropic(
    *,
    api_key: str,
    model: str,
    user_input: str,
    system_prompt: str | None,
    prior: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    tool_executor: Any,
    state: _AgentState,
    resume_state: dict[str, Any] | None,
) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    anth_tools = [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["parameters"],
        }
        for t in tools
    ]
    if resume_state:
        # Reanudación: tool_result del ask_user pendiente. Si en el mismo
        # turno hubo otras tools, sus resultados (ya ejecutados antes de la pausa)
        # van en el mismo mensaje user, como exige la API.
        api_messages: list[dict[str, Any]] = list(resume_state["native_messages"])
        blocks = list(resume_state["pending"].get("partial_results") or [])
        blocks.append(
            {
                "type": "tool_result",
                "tool_use_id": resume_state["pending"]["tool_use_id"],
                "content": _user_tool_result_payload(user_input),
            }
        )
        api_messages.append({"role": "user", "content": blocks})
    else:
        api_messages = list(prior) + [{"role": "user", "content": user_input}]

    while state.iterations < MAX_AGENT_ITERATIONS:
        state.iterations += 1
        request_kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": _MAX_OUTPUT_TOKENS,
            "messages": api_messages,
            "tools": anth_tools,
        }
        if system_prompt:
            request_kwargs["system"] = system_prompt
        try:
            response = client.messages.create(**request_kwargs)
        except anthropic.AnthropicError as exc:
            state.api_error = f"{type(exc).__name__}: {exc}"
            return ""
        if response.usage is not None:
            state.add_usage(response.usage.input_tokens, response.usage.output_tokens)
        state.used_model = getattr(response, "model", None) or model

        tool_uses = [b for b in response.content if getattr(b, "type", None) == "tool_use"]
        if not tool_uses:
            return "".join(
                b.text for b in response.content if getattr(b, "type", None) == "text"
            )

        # Dicts serializables (no objetos del SDK) por si hay pausa.
        api_messages.append(
            {
                "role": "assistant",
                "content": [b.model_dump(exclude_none=True) for b in response.content],
            }
        )
        result_blocks = []
        ask_use = None
        for tu in tool_uses:
            if tu.name == _USER_TOOL:
                ask_use = tu
                continue
            args = dict(tu.input or {})
            result = tool_executor(tu.name, args)
            state.record_call(tu.name, args, result)
            result_blocks.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )
        if ask_use is not None:
            state.pending_state = {
                "native_messages": api_messages,
                "pending": {
                    "tool_use_id": ask_use.id,
                    "partial_results": result_blocks,
                },
            }
            return _preguntas_terminal(state, dict(ask_use.input or {}))
        api_messages.append({"role": "user", "content": result_blocks})
    return _max_iter_error(state)


def _agent_google(
    *,
    api_key: str,
    model: str,
    user_input: str,
    system_prompt: str | None,
    prior: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    tool_executor: Any,
    state: _AgentState,
    resume_state: dict[str, Any] | None,
) -> str:
    client = genai.Client(api_key=api_key)
    declarations = []
    for t in tools:
        decl: dict[str, Any] = {"name": t["name"], "description": t["description"]}
        # Gemini rechaza schemas de objeto sin propiedades (caso read_profile):
        # se omite `parameters` y la tool queda sin argumentos.
        if t["parameters"].get("properties"):
            decl["parameters"] = t["parameters"]
        declarations.append(decl)

    gen_config = genai_types.GenerateContentConfig(
        max_output_tokens=_MAX_OUTPUT_TOKENS,
        system_instruction=system_prompt or None,
        tools=[genai_types.Tool(function_declarations=declarations)],
    )
    if resume_state:
        # Reanudación: function_response del ask_user pendiente (+ los
        # resultados de otras tools del mismo turno, si los hubo).
        contents: list[Any] = list(resume_state["native_messages"])
        parts = list(resume_state["pending"].get("partial_results") or [])
        parts.append(
            {
                "function_response": {
                    "name": _USER_TOOL,
                    "response": {"result": {"user_answers": user_input}},
                }
            }
        )
        contents.append({"role": "user", "parts": parts})
    else:
        contents = [_to_gemini_content(m) for m in prior]
        contents.append(_to_gemini_content({"role": "user", "content": user_input}))

    while state.iterations < MAX_AGENT_ITERATIONS:
        state.iterations += 1
        try:
            response = client.models.generate_content(
                model=model, contents=contents, config=gen_config
            )
        except genai.errors.APIError as exc:
            state.api_error = f"{type(exc).__name__}: {exc}"
            return ""
        usage = getattr(response, "usage_metadata", None)
        if usage is not None:
            state.add_usage(
                getattr(usage, "prompt_token_count", None),
                getattr(usage, "candidates_token_count", None),
            )
        state.used_model = getattr(response, "model_version", None) or model

        candidate = response.candidates[0] if response.candidates else None
        parts = list(candidate.content.parts or []) if candidate and candidate.content else []
        fn_calls = [p.function_call for p in parts if getattr(p, "function_call", None)]
        if not fn_calls:
            return getattr(response, "text", "") or ""

        # Dicts serializables (no objetos del SDK) por si hay pausa.
        contents.append(candidate.content.model_dump(exclude_none=True))
        response_parts = []
        ask_call = None
        for fc in fn_calls:
            if fc.name == _USER_TOOL:
                ask_call = fc
                continue
            args = dict(fc.args or {})
            result = tool_executor(fc.name, args)
            state.record_call(fc.name, args, result)
            response_parts.append(
                {"function_response": {"name": fc.name, "response": {"result": result}}}
            )
        if ask_call is not None:
            state.pending_state = {
                "native_messages": contents,
                "pending": {"partial_results": response_parts},
            }
            return _preguntas_terminal(state, dict(ask_call.args or {}))
        contents.append({"role": "user", "parts": response_parts})
    return _max_iter_error(state)


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
