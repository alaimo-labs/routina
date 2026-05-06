# Routina

App de coaching de fitness asistida por IA. Es el caso de estudio del programa de formación en AI evals de [alaimolabs.com/es/eva](https://alaimolabs.com/es/eva): a lo largo del curso vamos a evaluar este producto en sus distintas dimensiones.

Esta versión es **local**: corre en tu computadora, usa tu propia API key de OpenAI y guarda la información en una base de datos local (SQLite).

---

## Qué necesitas antes de empezar

1. **Una API key de OpenAI**. La obtienes en https://platform.openai.com/api-keys.
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

Cierra y vuelve a abrir la Terminal después de que termine.

**2. Clonar el repositorio y entrar a la carpeta**:

```bash
git clone https://github.com/alaimo-labs/routina routina
cd routina
```

**3. Configurar tu API key**:

```bash
cp .env.example .env
```

Después abre el archivo `.env` con cualquier editor y pega tu API key después del `=`. El archivo tiene que quedar así:

```
OPENAI_API_KEY=sk-...tu-key-aquí...
```

**4. Instalar las dependencias y levantar la app**:

```bash
uv sync
uv run uvicorn server:app --port 8000
```

Después abre tu navegador en `http://localhost:8000`. Listo.

---

### En Windows

Abre **PowerShell** (botón inicio, escribe "PowerShell", Enter).

**1. Instalar `uv`**:

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

Cierra y vuelve a abrir PowerShell después de que termine.

**2. Clonar el repositorio y entrar a la carpeta**:

```powershell
git clone https://github.com/alaimo-labs/routina routina
cd routina
```

**3. Configurar tu API key**:

```powershell
copy .env.example .env
notepad .env
```

Se abre el Bloc de notas. Pega tu API key después del `=` y guarda. El archivo tiene que quedar así:

```
OPENAI_API_KEY=sk-...tu-key-aquí...
```

**4. Instalar las dependencias y levantar la app**:

```powershell
uv sync
uv run uvicorn server:app --port 8000
```

Después abre tu navegador en `http://localhost:8000`. Listo.

---

## Cómo se usa

La app expone tres "modos" como rutas distintas, alineadas con la progresión del programa de evals (cada una representa un escope de evaluación distinto):

- **`/` Rutinas (one-shot)** — biblioteca de rutinas guardadas con un botón **"+ Nueva rutina"** que abre un modal. Escribes el caso, generás la rutina y decidís si guardarla o descartarla. Cada generación es independiente, sin contexto previo. Es el modo más simple para evaluar calidad de salida pura.
- **`/chat` Chat (multi-turno)** — conversación al estilo ChatGPT/Claude. Cada turno se acumula en el contexto del LLM, así podés refinar (*"hacela más corta"*, *"cambiá el formato a HIIT"*). El historial de chats persiste en la barra lateral. Pensado para evaluar coherencia conversacional.
- **`/agent` Agente** — placeholder por ahora. Vendrá en encuentros futuros del curso con tool calling, RAG y loop multi-step.

Adicionalmente hay **`/historial`**: la traza completa de evals — toda corrida (one-shot o chat, exitosa o fallida) queda registrada con su input, prompt, respuesta cruda, errores y mensajes de la traza.

**Configuración** (botón al pie de la barra lateral): eliges el modelo, decides si editar el system prompt en local o usar uno guardado en OpenAI (con su `prompt_id`).

**Validación de salida**: la app valida cada respuesta del LLM en tres capas (parseo JSON, conformidad con el schema, contenido) y te muestra cada resultado por separado — útil para razonar sobre dónde falla.

---

## Si te quedas atascado

**"git: command not found" o "git no se reconoce"**
- macOS: ejecuta `xcode-select --install` y acepta.
- Windows: descarga Git for Windows desde https://git-scm.com/download/win e instálalo.

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
│   ├── llm.py                  # Wrapper de la API de OpenAI (Responses)
│   └── validate.py             # Validación contra el JSON Schema
├── prompts/
│   └── routina_default.txt     # System prompt por defecto
├── schemas/
│   └── routina_v1.json         # JSON Schema de la rutina
└── data/                       # SQLite (se crea solo, no se versiona)
```

La base de datos vive en `data/routina.db`. Si quieres inspeccionarla a mano, puedes descargar [DB Browser for SQLite](https://sqlitebrowser.org/) y abrirla. Tres tablas: `chats` (conversaciones de `/chat`), `runs` (toda llamada al LLM, con o sin chat) y `routines` (rutinas guardadas, con FK al run que las generó).

## API HTTP

El frontend es una SPA estática que habla con FastAPI vía estos endpoints (útil si querés correr scripts de eval contra el mismo backend):

| Método | Path | Propósito |
| --- | --- | --- |
| `POST` | `/api/oneshot/generate` | Generación independiente, sin chat ni contexto previo |
| `POST` | `/api/chat/generate` | Generación dentro de un chat: incluye los turnos previos como contexto |
| `GET` | `/api/chats?mode=chat` | Lista de chats persistidos |
| `GET` | `/api/chats/{id}` | Detalle de un chat con todos sus runs |
| `DELETE` | `/api/chats/{id}` | Borra un chat (las rutinas guardadas se mantienen) |
| `GET` | `/api/runs?status=...` | Toda la traza de runs |
| `GET` | `/api/runs/{id}` | Detalle de un run con messages, errores y respuesta cruda |
| `POST` | `/api/routines` | Body `{run_id}`. Guarda como rutina el output del run |
| `GET` | `/api/routines` | Lista de rutinas guardadas (filtros: `objetivo`, `formato`) |
| `GET` | `/api/config` | Modelos disponibles, default, si la API key está cargada |
| `GET` | `/api/system-prompt` | El system prompt por defecto (texto plano) |
| `GET` | `/api/schema` | El JSON Schema activo |
