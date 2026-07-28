# Routina

App de coaching de fitness asistida por IA. Es el caso de estudio del programa de formación en AI evals de Alaimo Labs: [AI Evals para Product managers y Testers](https://alaimolabs.com/es/eva): a lo largo del curso evaluamos este producto en sus distintas dimensiones.

Esta versión es **local**: corre en tu computadora, usa tu propia API key (OpenAI, Anthropic y/o Google) y guarda la información en una base de datos local (SQLite).

---

## Qué necesitas antes de empezar

1. **Al menos una API key** de alguno de los proveedores soportados: OpenAI (https://platform.openai.com/api-keys), Anthropic (https://console.anthropic.com/) y/o Google (https://aistudio.google.com/apikey). Solo puedes usar los modelos del proveedor cuya key hayas configurado.
2. **Git** instalado para clonar el repositorio (te explicamos abajo cómo verificarlo).
3. Tener permisos para abrir la terminal en tu computadora. No hace falta ser administrador.

---

## Instalación paso a paso

### En macOS

Abre la app **Terminal** (`Cmd + Espacio`, escribe "Terminal", Enter) y pega los siguientes bloques uno por uno.

**1. Instalar `uv`** (el gestor que va a manejar Python por ti):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Luego de pegar esa línea en la Terminal, haz Enter.

Cierra y vuelve a abrir la Terminal después de que termine.

**2. Clonar el repositorio y entrar a la carpeta**:

Pega el siguiente texto en la Terminal y luego haz Enter:

```bash
git clone https://github.com/alaimo-labs/routina routina
cd routina
```

**3. Configurar tu API key**:

Pega el siguiente texto en la Terminal y luego haz Enter:

```bash
cp .env.example .env
```

Después abre el archivo `.env` con cualquier editor y pega tu(s) API key(s) después del `=`. Configura solo las que vayas a usar; el archivo puede quedar así:

```
OPENAI_API_KEY=sk-...tu-key-aquí...
ANTHROPIC_API_KEY=sk-ant-...tu-key-aquí...
GOOGLE_API_KEY=...tu-key-aquí...
```

Después, pega el siguiente texto en la Terminal y haz Enter (se abrirá Finder):

```
open .
```

Una vez en finder, haz `Command + Shift + .` (Command + Shift + Punto).

Verás los archivos ocultos (los que comienzan con ".").

Haz click derecho al archivo `.env` y abrelo con cualquier editor (por ejemplo TextEdit) y pega el API key (que obtuviste previamente de OpenAI) después del `=`. El archivo tiene que quedar así:

```

OPENAI_API_KEY=sk-proj-AbCdEfGhIjKlMnOpQrStUvWxYzAbCdEfGhIjKlMnOpQrStUvWxYz

```

NOTA: El código `sk-proj-AbCdEfGhIjKlMnOpQrStUvWxYzAbCdEfGhIjKlMnOpQrStUvWxYz` será diferente, porque cada quien tien el suyo propio (API Key).

Guarda el archivo.

**4. Instalar las dependencias y levantar la app**:

Pega el siguiente texto en la Terminal y luego haz Enter:

```bash
uv sync
uv run uvicorn server:app --port 8000
```

Después abre tu navegador en `http://localhost:8000`. Listo.

---

### En Windows

Abre **PowerShell** (botón inicio, escribe "PowerShell", Enter).

**1. Instalar `uv`**:

Pega el siguiente texto y luego haz Enter:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Cierra y vuelve a abrir PowerShell después de que termine.

> Si escribes solo `irm https://astral.sh/uv/install.ps1 | iex` y la ventana se cierra de golpe, es la política de ejecución de PowerShell bloqueando el script. El comando de arriba (con `-ExecutionPolicy ByPass`) evita justamente eso. Ver también "La ventana de PowerShell se cierra sola" más abajo.

**2. Clonar el repositorio y entrar a la carpeta**:

Pega el siguiente texto y luego haz Enter:

```powershell
git clone https://github.com/alaimo-labs/routina routina
cd routina
```

**3. Configurar tu API key**:

Pega el siguiente texto y luego haz Enter:

```powershell
copy .env.example .env
notepad .env
```

Se abre el Bloc de notas. Pega tu(s) API key(s) después del `=` y guarda. Configura solo las que vayas a usar; el archivo puede quedar así:

```
OPENAI_API_KEY=sk-...tu-key-aquí...
ANTHROPIC_API_KEY=sk-ant-...tu-key-aquí...
GOOGLE_API_KEY=...tu-key-aquí...
```

**4. Instalar las dependencias y levantar la app**:

Pega el siguiente texto y luego haz Enter:

```powershell
uv sync
uv run uvicorn server:app --port 8000
```

Después abre tu navegador en `http://localhost:8000`. Listo.

---

## Cómo se usa

La app expone tres "modos" como rutas distintas, alineadas con la progresión del programa de evals (cada una representa un escope de evaluación distinto):

- **`/` Rutinas (one-shot)** — biblioteca de rutinas guardadas con un botón **"+ Nueva rutina"** que abre un modal. Escribes el caso, generas la rutina y decides si guardarla o descartarla. Cada generación es independiente, sin contexto previo. Es el modo más simple para evaluar calidad de salida pura.
- **`/chat` Chat (multi-turno)** — conversación al estilo ChatGPT/Claude. Cada turno se acumula en el contexto del LLM, así puedes refinar (_"hazla más corta"_, _"cambia el formato a HIIT"_). El modelo decide en cada turno si responde con un mensaje conversacional (para preguntar o aclarar) o con una rutina; ambos son JSON con la forma `{"type": "message" | "routine", ...}`. El historial de chats persiste en la barra lateral. Pensado para evaluar coherencia conversacional y la decisión mensaje-vs-rutina.
- **`/agent` Agente** — conversación con herramientas (tool calling). El agente lee tu perfil, busca en el catálogo curado de ejercicios, te hace preguntas con opciones (multiple choice), valida la rutina contra el schema antes de entregarla y puede guardarla en tu biblioteca. Cada tool que usa queda visible en la conversación como chips, y la traza completa (llamadas, argumentos y resultados) queda en el historial. Pensado para evaluar agentes: elección de tools, grounding en el catálogo y respeto del perfil.

Adicionalmente hay **`/historial`**: la traza completa de evals — toda corrida (one-shot o chat, exitosa o fallida) queda registrada con su input, prompt, respuesta cruda, errores y mensajes de la traza.

**Perfil** (botón al pie de la barra lateral): marcas con checkboxes tu equipamiento disponible y tus lesiones o molestias, más notas libres. El agente lo consulta al armar rutinas en el modo Agente (es la base de sus tools).

**Configuración** (botón al pie de la barra lateral): eliges el modelo (agrupado por proveedor: OpenAI, Anthropic, Google), el **idioma** (español o inglés: cambia los textos de la UI y el idioma de generación) y editas los system prompts — hay uno por modo (one-shot, chat, agente) y por idioma; cada uno se abre en un editor a pantalla casi completa con su botón para restaurar el default. La app rutea cada modelo al proveedor correcto según su API key.

**Tools del agente**: en el modo Agente el modelo trabaja dentro de un loop (máximo 8 iteraciones por turno) con cinco herramientas: `read_profile` (lee tu perfil), `search_exercises` (busca en el catálogo curado, con filtros por grupo muscular, nivel, equipamiento y lesiones), `ask_user` (te hace hasta 3 preguntas con opciones y pausa la conversación hasta que respondes), `validate_routine` (valida la rutina contra el schema oficial) y `save_routine` (la valida y la guarda en tu biblioteca). Puedes inspeccionar las definiciones exactas que recibe el modelo — descripciones, parámetros y valores posibles, en el idioma activo — desde **Configuración → Tools del agente**, haciendo click en cualquier chip de tool de una conversación del agente, o vía `GET /api/agent/tools?lang=es|en`.

**Idiomas**: la app es bilingüe (español / inglés). El selector de Configuración cambia la UI y el idioma en el que genera el modelo. Las claves del JSON de las rutinas son siempre en inglés (`goal`, `exercises`, …) en ambos idiomas; lo que cambia es el contenido de los textos. Cada run registra el idioma con el que se generó.

**Validación de salida**: la app valida cada respuesta del LLM en tres capas (parseo JSON, conformidad con el schema, contenido) y te muestra cada resultado por separado — útil para razonar sobre dónde falla.

---

## Si te quedas atascado

**"git: command not found" o "git no se reconoce"**

- macOS: ejecuta `xcode-select --install` y acepta.
- Windows: descarga Git for Windows desde https://git-scm.com/download/win e instálalo.

**La ventana de PowerShell se cierra sola al instalar `uv`**

- Es la política de ejecución (execution policy) bloqueando el script descargado. Usa la forma con `ByPass`, que es la que recomienda uv para Windows:
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- Abre PowerShell **primero** (menú Inicio → "PowerShell" → Enter) y pega el comando ahí dentro; no lo corras por doble clic en un `.ps1` ni desde un acceso directo, porque esos cierran la ventana al terminar y no llegas a leer el error.
- Si quieres ver el mensaje aunque se cierre, agrega `-NoExit` para mantener la ventana abierta: `powershell -NoExit -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`.
- Como alternativa, puedes instalarlo con winget: `winget install --id=astral-sh.uv -e`.

**"Falta la API key" aunque tengas `.env`**

- Verifica que el archivo se llame exactamente `.env` (no `.env.txt`) y esté en la raíz del proyecto, junto a `pyproject.toml`.
- En Windows, el Bloc de notas a veces agrega `.txt` automáticamente. Activa "Mostrar extensiones de archivo" en el Explorador y renómbralo si fue así.

**"Address already in use" o el puerto 8000 está ocupado**

- Cierra cualquier otra app que esté usando ese puerto. Si persiste, levanta el servidor en otro puerto: `uv run uvicorn server:app --port 8002`.

**Errores de OpenAI: "Incorrect API key" o "Insufficient quota"**

- Ve a https://platform.openai.com y verifica que la key sea válida y tu cuenta tenga crédito.

---

## Estructura del proyecto

```
routina/
├── server.py                   # FastAPI: endpoints + sirve la SPA
├── static/
│   ├── index.html              # Layout (sidebar + 4 vistas + modales)
│   ├── styles.css              # Tema visual
│   └── app.js                  # Router cliente + lógica (vanilla JS)
├── src/routina/
│   ├── config.py               # Rutas y carga de .env
│   ├── db.py                   # SQLite: chats, runs, routines
│   ├── llm.py                  # Capa multi-proveedor + loop agéntico con tools
│   ├── agent_tools.py          # Tools del agente: definiciones y ejecución
│   ├── catalog.py              # Búsqueda sobre el catálogo de ejercicios
│   └── validate.py             # Validación contra el JSON Schema
├── catalog/
│   └── exercises_v1.json       # Catálogo de ejercicios (vocabulario cerrado, nombres/labels bilingües)
├── prompts/
│   ├── routina_oneshot_es.txt  # System prompt por defecto del modo one-shot (español)
│   ├── routina_oneshot_en.txt  # System prompt por defecto del modo one-shot (inglés)
│   ├── routina_chat_es.txt     # Ídem chat, por idioma
│   ├── routina_chat_en.txt
│   ├── routina_agent_es.txt    # Ídem agente, por idioma
│   └── routina_agent_en.txt
├── schemas/
│   ├── routina_v1.json         # JSON Schema de la rutina (one-shot; claves en inglés)
│   ├── chat_v1.json            # JSON Schema del sobre de chat (message | routine)
│   └── agent_v1.json           # JSON Schema del sobre del agente (+ questions)
└── data/                       # SQLite (se crea solo, no se versiona)
```

La base de datos vive en `data/routina.db`. Si quieres inspeccionarla a mano, puedes descargar [DB Browser for SQLite](https://sqlitebrowser.org/) y abrirla. Tres tablas: `chats` (conversaciones de `/chat`), `runs` (toda llamada al LLM, con o sin chat) y `routines` (rutinas guardadas, con FK al run que las generó).

## API HTTP

El frontend es una SPA estática que habla con FastAPI vía estos endpoints (útil si quieres correr scripts de eval contra el mismo backend):

| Método   | Path                    | Propósito                                                                |
| -------- | ----------------------- | ------------------------------------------------------------------------ |
| `POST`   | `/api/oneshot/generate` | Generación independiente, sin chat ni contexto previo                    |
| `POST`   | `/api/chat/generate`    | Generación dentro de un chat: incluye los turnos previos como contexto   |
| `POST`   | `/api/agent/generate`   | Loop agéntico con tools (perfil, catálogo, preguntas, validación, guardado) |
| `GET`    | `/api/chats?mode=chat`  | Lista de chats persistidos                                               |
| `GET`    | `/api/chats/{id}`       | Detalle de un chat con todos sus runs                                    |
| `DELETE` | `/api/chats/{id}`       | Borra un chat (las rutinas guardadas se mantienen)                       |
| `GET`    | `/api/runs?status=...`  | Toda la traza de runs                                                    |
| `GET`    | `/api/runs/{id}`        | Detalle de un run con messages, errores y respuesta cruda                |
| `POST`   | `/api/routines`         | Body `{run_id, lang?}`. Guarda como rutina el output del run             |
| `GET`    | `/api/routines`         | Lista de rutinas guardadas (filtros: `goal`, `format`)                   |
| `GET`    | `/api/profile`          | Perfil del usuario (`equipment`, `injuries`, `notes`) + vocabulario bilingüe |
| `PUT`    | `/api/profile`          | Guarda el perfil (valida los IDs contra el vocabulario del catálogo)     |
| `GET`    | `/api/catalog`          | Catálogo de ejercicios; filtros: `muscle_group`, `level`, `equipment`, `avoid_injuries` |
| `GET`    | `/api/config`           | Modelos disponibles (con proveedor), default, idiomas, qué proveedores tienen key |
| `GET`    | `/api/system-prompt`    | Los system prompts por defecto, por modo y por idioma (`{mode: {es, en}}`) |
| `GET`    | `/api/schema?mode=...`  | El JSON Schema del modo (`oneshot`, `chat` o `agent`; default `oneshot`) |
| `GET`    | `/api/agent/tools`      | Definiciones de las tools del agente tal como las recibe el modelo (`?lang=es\|en`) |

---

## Licencia

MIT — ver [LICENSE](LICENSE). Copyright (c) 2026 MTN LABS LLC d/b/a Alaimo Labs.
