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
git clone <URL-DEL-REPO> routina
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
git clone <URL-DEL-REPO> routina
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

La app abre con tres vistas accesibles desde la barra lateral izquierda: **Conversación**, **Rutinas guardadas** e **Historial**.

1. **Conversación**: escribes el pedido en el campo inferior (ej: *"Quiero perder peso, tengo 30 minutos, 4 veces por semana, sin equipamiento"*) y presionas Enter. La rutina aparece como respuesta.
2. **Configuración** (botón al pie de la barra lateral): eliges el modelo, decides si editar el system prompt en local o usar uno guardado en OpenAI (con su `prompt_id`).
3. La app te muestra tres capas de validación: parseo del JSON, validación contra el schema, y la rutina renderizada.
4. Si el resultado te gusta, puedes guardar la rutina con un click. Aparece en la vista **Rutinas guardadas**.
5. Cada corrida (incluso las que fallaron) queda registrada en **Historial**.

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
├── server.py                   # FastAPI: endpoints + sirve la UI
├── static/
│   ├── index.html              # Layout completo de la app
│   ├── styles.css              # Tema visual
│   └── app.js                  # Lógica del frontend (vanilla JS)
├── src/routina/
│   ├── config.py               # Rutas y carga de .env
│   ├── db.py                   # Persistencia SQLite (runs y routines)
│   ├── llm.py                  # Wrapper de la API de OpenAI
│   └── validate.py             # Validación contra el JSON Schema
├── prompts/
│   └── routina_default.txt     # System prompt por defecto
├── schemas/
│   └── routina_v1.json         # JSON Schema de la rutina
└── data/                       # SQLite (se crea solo, no se versiona)
```

La base de datos vive en `data/routina.db`. Si quieres inspeccionarla a mano, puedes descargar [DB Browser for SQLite](https://sqlitebrowser.org/) y abrirla.
