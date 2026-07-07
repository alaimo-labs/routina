// =====================================================================================
// Routina · frontend (vanilla JS, no frameworks)
// Tres rutas: / (one-shot), /chat (multi-turno), /agent (placeholder), /history.
// =====================================================================================
'use strict';

// -------------------- Íconos (Lucide, inline SVG) --------------------
const ICONS = {
    dumbbell: '<path d="M14.4 14.4 9.6 9.6"/><path d="M18.657 21.485a2 2 0 1 1-2.829-2.828l-1.767 1.768a2 2 0 1 1-2.829-2.829l6.364-6.364a2 2 0 1 1 2.829 2.829l-1.768 1.767a2 2 0 1 1 2.828 2.829z"/><path d="m21.5 21.5-1.4-1.4"/><path d="M3.9 3.9 2.5 2.5"/><path d="M6.404 12.768a2 2 0 1 1-2.829-2.829l1.768-1.767a2 2 0 1 1-2.828-2.829l2.828-2.828a2 2 0 1 1 2.829 2.828l1.767-1.768a2 2 0 1 1 2.829 2.829z"/>',
    'message-square': '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    bookmark: '<path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/>',
    history: '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/>',
    settings: '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
    send: '<path d="M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 3.18a2 2 0 0 1 1.112 1.11z"/><path d="m21.854 2.147-10.94 10.939"/>',
    save: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>',
    plus: '<path d="M5 12h14"/><path d="M12 5v14"/>',
    x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    'panel-left': '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 3v18"/>',
    'alert-triangle': '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    check: '<path d="M20 6 9 17l-5-5"/>',
    clock: '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    calendar: '<path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/>',
    trash: '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    'arrow-up': '<path d="M5 12 12 5l7 7"/><path d="M12 19V5"/>',
    'arrow-down': '<path d="M12 5v14"/><path d="m19 12-7 7-7-7"/>',
    cpu: '<rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/>',
    sparkles: '<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/><path d="M20 3v4"/><path d="M22 5h-4"/><path d="M4 17v2"/><path d="M5 18H3"/>',
    timer: '<line x1="10" x2="14" y1="2" y2="2"/><line x1="12" x2="15" y1="14" y2="11"/><circle cx="12" cy="14" r="8"/>',
    'arrow-up-down': '<path d="m21 16-4 4-4-4"/><path d="M17 20V4"/><path d="m3 8 4-4 4 4"/><path d="M7 4v16"/>',
    home: '<path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    bot: '<path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/>',
    repeat: '<path d="m17 2 4 4-4 4"/><path d="M3 11v-1a4 4 0 0 1 4-4h14"/><path d="m7 22-4-4 4-4"/><path d="M21 13v1a4 4 0 0 1-4 4H3"/>',
    search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
    moon: '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>',
    info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    'chevrons-up-down': '<path d="m7 15 5 5 5-5"/><path d="m7 9 5-5 5 5"/>',
    user: '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    wrench: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
};

function icon(name, size = 16) {
    const path = ICONS[name];
    if (!path) return '';
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-${name}">${path}</svg>`;
}

function replaceIcons(root = document) {
    root.querySelectorAll('[data-icon]').forEach(el => {
        if (el.firstElementChild && el.firstElementChild.tagName === 'svg') return;
        const name = el.dataset.icon;
        const size = parseInt(el.dataset.size || '16', 10);
        el.innerHTML = icon(name, size);
    });
}

// -------------------- i18n --------------------
// Toggle global ES/EN (drawer de Configuración): cambia los textos de la UI y el
// idioma de generación (prompt default del idioma activo + `lang` en cada request).
// Los textos estáticos del HTML se marcan con data-i18n / data-i18n-placeholder /
// data-i18n-aria / data-i18n-html; los dinámicos usan t(key).
const I18N = {
    es: {
        'brand.tag': 'Tu coach personal',
        'sidebar.collapse': 'Colapsar barra lateral',
        'sidebar.show': 'Mostrar barra lateral',
        'nav.routines': 'Rutinas',
        'nav.chat': 'Chat',
        'nav.agent': 'Agente',
        'nav.history': 'Historial',
        'nav.profile': 'Perfil',
        'nav.settings': 'Configuración',
        'nav.about': 'Acerca de',
        'chats.new': 'Conversación',
        'chats.section': 'Conversaciones',
        'chats.empty': 'Sin conversaciones todavía.',
        'footer.credits': 'desarrollado por<br><a href="https://alaimolabs.com" target="_blank" rel="noopener" class="user-meta-link">Alaimo Labs</a> para <a href="https://alaimolabs.com/eva" target="_blank" rel="noopener" class="user-meta-link">AI Evals</a>',
        'home.eyebrow': '01 · Rutinas',
        'home.title': 'Tus rutinas guardadas.',
        'home.sub': 'La colección completa, ordenada por fecha. Genera una nueva o revisa las anteriores.',
        'home.newRoutine': 'Nueva rutina',
        'home.filterGoal': 'Filtrar por objetivo…',
        'home.allFormats': 'Todos los formatos',
        'home.emptyLabel': '· Vacío',
        'home.emptyTitle': 'Todavía no hay rutinas guardadas.',
        'home.emptyBody': 'Haz click en <strong>+ Nueva rutina</strong> para generar la primera. Cada rutina queda guardada acá con su run asociado en el historial.',
        'chat.placeholder': 'Cuanto más concreto seas — objetivo, días disponibles, equipamiento, lesiones — mejor va a ser el plan.',
        'chat.hint': '↩ enviar · ⇧ + ↩ nueva línea · cada turno incluye los anteriores como contexto',
        'agent.placeholder': 'Pídele una rutina a tu agente: él lee tu perfil, busca en el catálogo y te pregunta lo que falte.',
        'agent.hint': '↩ enviar · ⇧ + ↩ nueva línea · el agente usa tools: perfil, catálogo, validación, guardado',
        'composer.send': 'Enviar',
        'composer.answerFirst': 'Responde las preguntas del agente para continuar…',
        'empty.tryLabel': 'Prueba con',
        'empty.chat.eyebrow': '02 · Chat',
        'empty.chat.title': 'Cuéntame qué quieres entrenar.',
        'empty.chat.sub': 'Cuanto más concreto seas — objetivo, días disponibles, equipamiento, lesiones — mejor va a ser el plan que armemos. Cada turno incluye los anteriores como contexto.',
        'empty.chat.ex1': 'Soy intermedio, voy al gimnasio 4 veces por semana. Quiero ganar masa muscular en torso.',
        'empty.chat.ex2': 'Quiero empezar a entrenar pero no sé por dónde. 25 min por día y solo una colchoneta.',
        'empty.chat.ex3': 'Quiero correr una 10K en 3 meses. Hoy corro 4km. 3 sesiones + algo de fuerza.',
        'empty.agent.eyebrow': '03 · Agente',
        'empty.agent.title': 'Tu agente entrenador.',
        'empty.agent.sub': 'Conversación con herramientas: el agente lee tu perfil, busca en el catálogo de ejercicios, te hace preguntas con opciones, valida la rutina y puede guardarla. Cada tool que usa queda visible en la conversación.',
        'empty.agent.ex1': 'Armame la rutina de esta semana.',
        'empty.agent.ex2': 'Quiero una rutina de fuerza que no castigue mis lesiones.',
        'empty.agent.ex3': 'Busca ejercicios de core que pueda hacer con mi equipamiento y armame algo de 20 minutos.',
        'loading.chat': 'Pensando…',
        'loading.agent': 'El agente está trabajando…',
        'history.eyebrow': '04 · Historial',
        'history.eyebrowRight': 'Traza de evals',
        'history.title': 'Historial de corridas.',
        'history.sub': 'Toda la traza: éxitos y fallos, one-shot, chat y agente. Cada llamada al modelo queda registrada.',
        'history.all': 'Todos',
        'history.emptyLabel': '· Sin resultados',
        'history.emptyTitle': 'No hay corridas con este filtro.',
        'history.emptyBody': 'Genera una rutina o cambia el filtro.',
        'history.noInput': '(sin input)',
        'settings.title': 'Configuración',
        'settings.model': 'Modelo',
        'settings.language': 'Idioma',
        'settings.langToggle': 'Cambiar idioma',
        'settings.theme': 'Tema actual',
        'settings.themeToggle': 'Cambiar tema',
        'settings.schemaOneshot': 'Schema one-shot',
        'settings.schemaChat': 'Schema chat',
        'settings.schemaAgent': 'Schema agente',
        'settings.dangerZone': 'Zona de peligro',
        'settings.dangerHelp': 'Borra todas las trazas, conversaciones y rutinas guardadas. La acción no se puede deshacer.',
        'settings.resetAll': 'Borrar todo',
        'settings.keyOk': 'Configurada',
        'settings.keyMissing': 'Faltante',
        'settings.keyHint': (provider, envVar) => `Configura tu API Key de ${provider} en <code>${envVar}</code>`,
        'settings.promptLangHint': 'Editas el system prompt del idioma activo: Español.',
        'theme.dark': 'Oscuro',
        'theme.light': 'Claro',
        'prompt.oneshot': 'System prompt · One-shot',
        'prompt.chat': 'System prompt · Chat',
        'prompt.agent': 'System prompt · Agente',
        'prompt.restore': 'Restaurar default (v0)',
        'prompt.restoreTitle': 'Restaurar default',
        'prompt.restoreMsg': 'Esto reemplaza el contenido del editor por la versión por defecto. Se aplica recién al guardar.',
        'prompt.restoreOk': 'Restaurar',
        'profile.title': 'Tu perfil',
        'profile.help': 'Tu agente consulta este perfil cuando arma rutinas en el modo Agente: marca el equipamiento que tienes y las zonas con lesiones o molestias.',
        'profile.equipment': 'Equipamiento disponible',
        'profile.injuries': 'Lesiones o molestias',
        'profile.notes': 'Notas para tu agente',
        'profile.notesPlaceholder': 'Ej. La rodilla solo molesta al saltar; prefiero entrenar de mañana.',
        'oneshot.title': 'Nueva rutina',
        'oneshot.help': 'Describe el caso del usuario en lenguaje natural. Una sola interacción, una sola rutina.',
        'oneshot.placeholder': 'Ej. Quiero perder peso, tengo 30 minutos por día, 4 veces por semana, sin equipamiento.',
        'oneshot.generate': 'Generar rutina',
        'oneshot.generating': 'Generando…',
        'oneshot.saveRoutine': 'Guardar rutina',
        'oneshot.discard': 'Descartar',
        'oneshot.another': 'Otra rutina',
        'oneshot.close': 'Cerrar',
        'oneshot.retry': 'Reintentar',
        'oneshot.invalidJson': 'JSON inválido:',
        'oneshot.schemaFail': 'Schema no cumplido:',
        'oneshot.apiError': 'Error API:',
        'about.title': 'Acerca de Routina',
        'about.body': `
            <p>
                <strong>Routina</strong> es una app de coaching de fitness asistida por IA,
                desarrollada por <a href="https://alaimolabs.com" target="_blank" rel="noopener" class="about-link">Alaimo Labs</a>
                con fines prácticos: ofrecer a los alumnos del programa
                <a href="https://alaimolabs.com/eva" target="_blank" rel="noopener" class="about-link">AI Evals</a>
                un entorno simulado donde practicar el diseño y la evaluación de aplicaciones con LLMs.
            </p>
            <p>
                Las tres rutas de la app — <em>Rutinas</em>, <em>Chat</em> y <em>Agente</em> — son el lienzo del curso:
                cada una representa un escope distinto de evaluación (calidad de salida, coherencia conversacional, agente con tools)
                que se recorre a lo largo del programa.
            </p>
        `,
        'common.cancel': 'Cancelar',
        'common.save': 'Guardar',
        'common.confirm': 'Confirmar',
        'common.close': 'Cerrar',
        'common.delete': 'Borrar',
        'common.loading': 'Cargando…',
        'common.error': 'Error:',
        'status.parse': 'JSON inválido',
        'status.schema': 'Schema',
        'status.api': 'Error API',
        'routine.goal': 'Objetivo',
        'routine.noGoal': '(sin objetivo)',
        'routine.frequency': 'Frecuencia',
        'routine.daysUnit': 'días/sem',
        'routine.perSession': 'Por sesión',
        'routine.format': 'Formato',
        'routine.warning': '· Aviso',
        'routine.exercise': 'Ejercicio',
        'routine.setsReps': 'Series × Reps',
        'routine.rest': 'Descanso',
        'routine.generalNotes': 'Notas generales',
        'routine.fallbackName': 'Ejercicio',
        'routine.deleteTitle': 'Borrar rutina',
        'routine.deleteMsg': 'La corrida en el historial se mantiene.',
        'routine.save': 'Guardar →',
        'routine.saved': '✓ Guardada',
        'chat.deleteTitle': 'Borrar conversación',
        'chat.deleteMsg': 'Las rutinas guardadas se mantienen.',
        'questions.label': 'El agente necesita saber',
        'questions.answer': 'Responder →',
        'err.cantGenerate': 'No pude generar la respuesta',
        'err.apiCall': 'Error al llamar a la API',
        'err.noValidJson': 'El modelo no devolvió un JSON válido',
        'err.rawResponse': 'Ver respuesta cruda',
        'err.rawEmpty': '(vacía)',
        'err.schemaMismatch': 'El JSON no cumple el schema',
        'err.viewJson': 'Ver JSON devuelto',
        'run.tab.input': 'Input',
        'run.tab.prompt': 'Prompt',
        'run.tab.response': 'Respuesta',
        'run.tab.errors': 'Errores',
        'run.tab.trace': 'Traza',
        'run.tab.details': 'Detalles',
        'run.systemPromptUsed': 'System prompt usado:',
        'run.noResponse': '(sin respuesta)',
        'run.empty': '(vacío)',
        'run.parseError': 'Parse error:',
        'run.schemaErrors': 'Errores de schema:',
        'run.noErrors': 'Este run no tuvo errores.',
        'run.provider': 'Proveedor',
        'run.model': 'Modelo',
        'run.language': 'Idioma',
        'run.date': 'Fecha',
        'run.latency': 'Latencia',
        'run.tokensIn': 'Tokens input',
        'run.tokensOut': 'Tokens output',
        'discard.title': 'Descartar cambios',
        'discard.promptMsg': 'Hay cambios sin guardar en el system prompt. ¿Quieres descartarlos?',
        'discard.profileMsg': 'Hay cambios sin guardar en tu perfil. ¿Quieres descartarlos?',
        'discard.ok': 'Descartar',
        'discard.keep': 'Seguir editando',
        'reset.title': 'Borrar todo',
        'reset.msg': 'Vas a borrar todas las trazas, conversaciones y rutinas guardadas. La acción no se puede deshacer.',
        'reset.ok': 'Borrar todo',
        'toast.routineSaved': 'Rutina guardada',
        'toast.routineDeleted': 'Rutina borrada',
        'toast.chatDeleted': 'Conversación borrada',
        'toast.promptSaved': 'System prompt guardado',
        'toast.profileSaved': 'Perfil guardado',
        'toast.allDeleted': 'Todo borrado',
        'toast.writeCase': 'Escribe el caso del usuario',
        'toast.cantSave': 'No pude guardar: ',
        'toast.cantDelete': 'No pude borrar: ',
        'toast.missingKey': (provider) => `Falta la API key de ${provider} en .env`,
        'agent.usingTool': (name) => `Usando ${name}…`,
        'agent.noResult': 'El agente no devolvió resultado.',
        'agent.errorFallback': 'Error del agente',
        'chip.valid': '✓ válida',
        'chip.invalid': '✗ inválida',
        'chip.errors': (n) => `✗ ${n} errores`,
        'chip.questions': (n) => `${n} pregunta(s)`,
        'chip.error': '✗ error',
        'tool.read_profile': 'Leyendo tu perfil…',
        'tool.search_exercises': 'Buscando ejercicios en el catálogo…',
        'tool.ask_user': 'Preparando preguntas…',
        'tool.validate_routine': 'Validando la rutina…',
        'tool.save_routine': 'Guardando la rutina…',
    },
    en: {
        'brand.tag': 'Your personal coach',
        'sidebar.collapse': 'Collapse sidebar',
        'sidebar.show': 'Show sidebar',
        'nav.routines': 'Routines',
        'nav.chat': 'Chat',
        'nav.agent': 'Agent',
        'nav.history': 'History',
        'nav.profile': 'Profile',
        'nav.settings': 'Settings',
        'nav.about': 'About',
        'chats.new': 'Conversation',
        'chats.section': 'Conversations',
        'chats.empty': 'No conversations yet.',
        'footer.credits': 'built by<br><a href="https://alaimolabs.com" target="_blank" rel="noopener" class="user-meta-link">Alaimo Labs</a> for <a href="https://alaimolabs.com/eva" target="_blank" rel="noopener" class="user-meta-link">AI Evals</a>',
        'home.eyebrow': '01 · Routines',
        'home.title': 'Your saved routines.',
        'home.sub': 'The full collection, sorted by date. Generate a new one or review the previous ones.',
        'home.newRoutine': 'New routine',
        'home.filterGoal': 'Filter by goal…',
        'home.allFormats': 'All formats',
        'home.emptyLabel': '· Empty',
        'home.emptyTitle': 'No saved routines yet.',
        'home.emptyBody': 'Click <strong>+ New routine</strong> to generate the first one. Every routine is saved here with its run linked in the history.',
        'chat.placeholder': 'The more specific you are — goal, available days, equipment, injuries — the better the plan will be.',
        'chat.hint': '↩ send · ⇧ + ↩ new line · each turn includes the previous ones as context',
        'agent.placeholder': 'Ask your agent for a routine: it reads your profile, searches the catalog and asks you what’s missing.',
        'agent.hint': '↩ send · ⇧ + ↩ new line · the agent uses tools: profile, catalog, validation, saving',
        'composer.send': 'Send',
        'composer.answerFirst': 'Answer the agent’s questions to continue…',
        'empty.tryLabel': 'Try',
        'empty.chat.eyebrow': '02 · Chat',
        'empty.chat.title': 'Tell me what you want to train.',
        'empty.chat.sub': 'The more specific you are — goal, available days, equipment, injuries — the better the plan we’ll build. Each turn includes the previous ones as context.',
        'empty.chat.ex1': 'I’m intermediate, I go to the gym 4 times a week. I want to build upper-body muscle.',
        'empty.chat.ex2': 'I want to start training but don’t know where to begin. 25 min a day and just a mat.',
        'empty.chat.ex3': 'I want to run a 10K in 3 months. Today I run 4km. 3 sessions + some strength work.',
        'empty.agent.eyebrow': '03 · Agent',
        'empty.agent.title': 'Your coaching agent.',
        'empty.agent.sub': 'A conversation with tools: the agent reads your profile, searches the exercise catalog, asks you multiple-choice questions, validates the routine and can save it. Every tool it uses is visible in the conversation.',
        'empty.agent.ex1': 'Build me this week’s routine.',
        'empty.agent.ex2': 'I want a strength routine that doesn’t punish my injuries.',
        'empty.agent.ex3': 'Find core exercises I can do with my equipment and build me something 20 minutes long.',
        'loading.chat': 'Thinking…',
        'loading.agent': 'The agent is working…',
        'history.eyebrow': '04 · History',
        'history.eyebrowRight': 'Eval trace',
        'history.title': 'Run history.',
        'history.sub': 'The full trace: successes and failures, one-shot, chat and agent. Every model call is recorded.',
        'history.all': 'All',
        'history.emptyLabel': '· No results',
        'history.emptyTitle': 'No runs match this filter.',
        'history.emptyBody': 'Generate a routine or change the filter.',
        'history.noInput': '(no input)',
        'settings.title': 'Settings',
        'settings.model': 'Model',
        'settings.language': 'Language',
        'settings.langToggle': 'Change language',
        'settings.theme': 'Current theme',
        'settings.themeToggle': 'Change theme',
        'settings.schemaOneshot': 'One-shot schema',
        'settings.schemaChat': 'Chat schema',
        'settings.schemaAgent': 'Agent schema',
        'settings.dangerZone': 'Danger zone',
        'settings.dangerHelp': 'Deletes all traces, conversations and saved routines. This action cannot be undone.',
        'settings.resetAll': 'Delete everything',
        'settings.keyOk': 'Configured',
        'settings.keyMissing': 'Missing',
        'settings.keyHint': (provider, envVar) => `Set your ${provider} API key in <code>${envVar}</code>`,
        'settings.promptLangHint': 'You are editing the system prompt for the active language: English.',
        'theme.dark': 'Dark',
        'theme.light': 'Light',
        'prompt.oneshot': 'System prompt · One-shot',
        'prompt.chat': 'System prompt · Chat',
        'prompt.agent': 'System prompt · Agent',
        'prompt.restore': 'Restore default (v0)',
        'prompt.restoreTitle': 'Restore default',
        'prompt.restoreMsg': 'This replaces the editor content with the default version. It only applies when you save.',
        'prompt.restoreOk': 'Restore',
        'profile.title': 'Your profile',
        'profile.help': 'Your agent checks this profile when building routines in Agent mode: mark the equipment you have and the areas with injuries or discomfort.',
        'profile.equipment': 'Available equipment',
        'profile.injuries': 'Injuries or discomforts',
        'profile.notes': 'Notes for your agent',
        'profile.notesPlaceholder': 'E.g. My knee only hurts when jumping; I prefer training in the morning.',
        'oneshot.title': 'New routine',
        'oneshot.help': 'Describe the user’s case in natural language. One interaction, one routine.',
        'oneshot.placeholder': 'E.g. I want to lose weight, I have 30 minutes a day, 4 times a week, no equipment.',
        'oneshot.generate': 'Generate routine',
        'oneshot.generating': 'Generating…',
        'oneshot.saveRoutine': 'Save routine',
        'oneshot.discard': 'Discard',
        'oneshot.another': 'Another routine',
        'oneshot.close': 'Close',
        'oneshot.retry': 'Retry',
        'oneshot.invalidJson': 'Invalid JSON:',
        'oneshot.schemaFail': 'Schema not met:',
        'oneshot.apiError': 'API error:',
        'about.title': 'About Routina',
        'about.body': `
            <p>
                <strong>Routina</strong> is an AI-assisted fitness coaching app,
                built by <a href="https://alaimolabs.com" target="_blank" rel="noopener" class="about-link">Alaimo Labs</a>
                for a practical purpose: giving students of the
                <a href="https://alaimolabs.com/eva" target="_blank" rel="noopener" class="about-link">AI Evals</a>
                program a simulated environment to practice designing and evaluating LLM applications.
            </p>
            <p>
                The app’s three routes — <em>Routines</em>, <em>Chat</em> and <em>Agent</em> — are the course’s canvas:
                each one represents a different evaluation scope (output quality, conversational coherence, agent with tools)
                covered throughout the program.
            </p>
        `,
        'common.cancel': 'Cancel',
        'common.save': 'Save',
        'common.confirm': 'Confirm',
        'common.close': 'Close',
        'common.delete': 'Delete',
        'common.loading': 'Loading…',
        'common.error': 'Error:',
        'status.parse': 'Invalid JSON',
        'status.schema': 'Schema',
        'status.api': 'API error',
        'routine.goal': 'Goal',
        'routine.noGoal': '(no goal)',
        'routine.frequency': 'Frequency',
        'routine.daysUnit': 'days/wk',
        'routine.perSession': 'Per session',
        'routine.format': 'Format',
        'routine.warning': '· Warning',
        'routine.exercise': 'Exercise',
        'routine.setsReps': 'Sets × Reps',
        'routine.rest': 'Rest',
        'routine.generalNotes': 'General notes',
        'routine.fallbackName': 'Exercise',
        'routine.deleteTitle': 'Delete routine',
        'routine.deleteMsg': 'The run stays in the history.',
        'routine.save': 'Save →',
        'routine.saved': '✓ Saved',
        'chat.deleteTitle': 'Delete conversation',
        'chat.deleteMsg': 'Saved routines are kept.',
        'questions.label': 'The agent needs to know',
        'questions.answer': 'Answer →',
        'err.cantGenerate': 'Couldn’t generate the response',
        'err.apiCall': 'Error calling the API',
        'err.noValidJson': 'The model didn’t return valid JSON',
        'err.rawResponse': 'View raw response',
        'err.rawEmpty': '(empty)',
        'err.schemaMismatch': 'The JSON doesn’t match the schema',
        'err.viewJson': 'View returned JSON',
        'run.tab.input': 'Input',
        'run.tab.prompt': 'Prompt',
        'run.tab.response': 'Response',
        'run.tab.errors': 'Errors',
        'run.tab.trace': 'Trace',
        'run.tab.details': 'Details',
        'run.systemPromptUsed': 'System prompt used:',
        'run.noResponse': '(no response)',
        'run.empty': '(empty)',
        'run.parseError': 'Parse error:',
        'run.schemaErrors': 'Schema errors:',
        'run.noErrors': 'This run had no errors.',
        'run.provider': 'Provider',
        'run.model': 'Model',
        'run.language': 'Language',
        'run.date': 'Date',
        'run.latency': 'Latency',
        'run.tokensIn': 'Input tokens',
        'run.tokensOut': 'Output tokens',
        'discard.title': 'Discard changes',
        'discard.promptMsg': 'There are unsaved changes in the system prompt. Discard them?',
        'discard.profileMsg': 'There are unsaved changes in your profile. Discard them?',
        'discard.ok': 'Discard',
        'discard.keep': 'Keep editing',
        'reset.title': 'Delete everything',
        'reset.msg': 'You are about to delete all traces, conversations and saved routines. This action cannot be undone.',
        'reset.ok': 'Delete everything',
        'toast.routineSaved': 'Routine saved',
        'toast.routineDeleted': 'Routine deleted',
        'toast.chatDeleted': 'Conversation deleted',
        'toast.promptSaved': 'System prompt saved',
        'toast.profileSaved': 'Profile saved',
        'toast.allDeleted': 'Everything deleted',
        'toast.writeCase': 'Describe the user’s case',
        'toast.cantSave': 'Couldn’t save: ',
        'toast.cantDelete': 'Couldn’t delete: ',
        'toast.missingKey': (provider) => `Missing ${provider} API key in .env`,
        'agent.usingTool': (name) => `Using ${name}…`,
        'agent.noResult': 'The agent didn’t return a result.',
        'agent.errorFallback': 'Agent error',
        'chip.valid': '✓ valid',
        'chip.invalid': '✗ invalid',
        'chip.errors': (n) => `✗ ${n} errors`,
        'chip.questions': (n) => `${n} question(s)`,
        'chip.error': '✗ error',
        'tool.read_profile': 'Reading your profile…',
        'tool.search_exercises': 'Searching the exercise catalog…',
        'tool.ask_user': 'Preparing questions…',
        'tool.validate_routine': 'Validating the routine…',
        'tool.save_routine': 'Saving the routine…',
    },
};

function t(key, ...args) {
    const dict = I18N[state.settings.lang] || I18N.es;
    const val = dict[key] ?? I18N.es[key] ?? key;
    return typeof val === 'function' ? val(...args) : val;
}

// Aplica las traducciones a los nodos estáticos del HTML.
function applyI18n() {
    document.documentElement.lang = state.settings.lang;
    document.title = state.settings.lang === 'es'
        ? 'Routina · Coach de fitness asistido por IA'
        : 'Routina · AI-assisted fitness coach';
    document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
    document.querySelectorAll('[data-i18n-html]').forEach(el => { el.innerHTML = t(el.dataset.i18nHtml); });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => { el.placeholder = t(el.dataset.i18nPlaceholder); });
    document.querySelectorAll('[data-i18n-aria]').forEach(el => { el.setAttribute('aria-label', t(el.dataset.i18nAria)); });
}

// -------------------- Estado --------------------
const SETTINGS_KEY = 'routina:settings';
const THEME_KEY = 'routina:theme';

const state = {
    route: window.location.pathname,
    config: null,
    chats: [],          // lista de conversaciones del modo activo (chat o agent)
    // Estado por modo conversacional: /chat y /agent comparten la mecánica.
    conv: {
        chat: { chatId: null, messages: [] },
        agent: { chatId: null, messages: [] },
    },
    isGenerating: false,
    settings: {
        model: '',
        lang: 'es',
        // Un system prompt editable por modo y por idioma.
        prompts: {
            es: { oneshot: '', chat: '', agent: '' },
            en: { oneshot: '', chat: '', agent: '' },
        },
    },
    routinesFilter: { goal: '', format: '' },
    runsFilter: { status: '' },
    drawerOpen: false,
    promptModalMode: null,   // 'oneshot' | 'chat' | 'agent' mientras el editor de prompt está abierto
    sidebarCollapsed: localStorage.getItem('routina:sidebar-collapsed') === '1',
    theme: localStorage.getItem(THEME_KEY) === 'dark' ? 'dark' : 'light',
    oneshot: { lastRunId: null, isSaved: false },
};

// System prompt activo de un modo (según el idioma seleccionado).
function activePrompt(mode) {
    return state.settings.prompts[state.settings.lang][mode];
}

function loadSettings() {
    try {
        const raw = localStorage.getItem(SETTINGS_KEY);
        if (raw) return JSON.parse(raw);
    } catch {}
    return null;
}

function saveSettings() {
    try {
        localStorage.setItem(SETTINGS_KEY, JSON.stringify(state.settings));
    } catch {}
}

// /chat y /agent comparten la mecánica conversacional; esto mapea cada modo a sus
// elementos del DOM y su endpoint. El modo activo se deriva de la ruta.
const CONV_UI = {
    chat: {
        messagesId: 'chat-messages',
        scrollId: 'chat-scroll',
        inputId: 'chat-input',
        sendBtnId: 'send-btn',
        loadingKey: 'loading.chat',
        placeholderKey: 'chat.placeholder',
        route: '/chat',
    },
    agent: {
        messagesId: 'agent-messages',
        scrollId: 'agent-scroll',
        inputId: 'agent-input',
        sendBtnId: 'agent-send-btn',
        loadingKey: 'loading.agent',
        placeholderKey: 'agent.placeholder',
        route: '/agent',
    },
};

function convMode() {
    return state.route === '/agent' ? 'agent' : 'chat';
}

function activeConv() {
    return state.conv[convMode()];
}

// Proveedor del modelo actualmente seleccionado (según el registro de /api/config).
function providerForModel(model) {
    const m = (state.config?.available_models || []).find(x => x.id === model);
    return m ? m.provider : 'openai';
}

// ¿El proveedor del modelo seleccionado tiene su API key configurada?
function selectedProviderHasKey() {
    const provider = providerForModel(state.settings.model);
    return Boolean(state.config?.providers?.[provider]);
}

// -------------------- API --------------------
const api = {
    async getConfig() {
        const r = await fetch('/api/config');
        if (!r.ok) throw new Error('No pude leer config');
        return r.json();
    },
    async getSystemPrompts() {
        // Devuelve { oneshot: "...", chat: "..." } — un prompt default por modo.
        const r = await fetch('/api/system-prompt');
        return r.json();
    },
    async oneshotGenerate(body) {
        const r = await fetch('/api/oneshot/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!r.ok) {
            const data = await r.json().catch(() => ({}));
            throw new Error(data.detail || `Error ${r.status}`);
        }
        return r.json();
    },
    async chatGenerate(body) {
        const r = await fetch('/api/chat/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!r.ok) {
            const data = await r.json().catch(() => ({}));
            throw new Error(data.detail || `Error ${r.status}`);
        }
        return r.json();
    },
    // El endpoint del agente streamea SSE: eventos {type:"tool"} mientras corre el
    // loop y {type:"result"} al final. `onEvent` recibe los eventos intermedios.
    async agentGenerate(body, onEvent) {
        const r = await fetch('/api/agent/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!r.ok) {
            const data = await r.json().catch(() => ({}));
            throw new Error(data.detail || `Error ${r.status}`);
        }
        const reader = r.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let result = null;
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            let sep;
            while ((sep = buffer.indexOf('\n\n')) !== -1) {
                const chunk = buffer.slice(0, sep);
                buffer = buffer.slice(sep + 2);
                const line = chunk.split('\n').find(l => l.startsWith('data: '));
                if (!line) continue;
                const evt = JSON.parse(line.slice(6));
                if (evt.type === 'result') result = evt.data;
                else if (evt.type === 'error') throw new Error(evt.detail || t('agent.errorFallback'));
                else if (onEvent) onEvent(evt);
            }
        }
        if (!result) throw new Error(t('agent.noResult'));
        return result;
    },
    async listRuns(filter) {
        const params = new URLSearchParams();
        if (filter.status) params.set('status', filter.status);
        const r = await fetch(`/api/runs?${params}`);
        return r.json();
    },
    async getRun(id) {
        const r = await fetch(`/api/runs/${id}`);
        if (!r.ok) throw new Error('Run no encontrado');
        return r.json();
    },
    async saveRoutine(runId) {
        const r = await fetch('/api/routines', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ run_id: runId, lang: state.settings.lang }),
        });
        if (!r.ok) {
            const data = await r.json().catch(() => ({}));
            throw new Error(data.detail || `Error ${r.status}`);
        }
        return r.json();
    },
    async listRoutines(filter) {
        const params = new URLSearchParams();
        if (filter.goal) params.set('goal', filter.goal);
        if (filter.format) params.set('format', filter.format);
        const r = await fetch(`/api/routines?${params}`);
        return r.json();
    },
    async getRoutine(id) {
        const r = await fetch(`/api/routines/${id}`);
        if (!r.ok) throw new Error('Rutina no encontrada');
        return r.json();
    },
    async deleteRoutine(id) {
        const r = await fetch(`/api/routines/${id}`, { method: 'DELETE' });
        if (!r.ok) {
            const data = await r.json().catch(() => ({}));
            throw new Error(data.detail || 'No pude borrar la rutina');
        }
        return r.json();
    },
    async listChats(mode = null) {
        const params = new URLSearchParams();
        if (mode) params.set('mode', mode);
        const r = await fetch(`/api/chats?${params}`);
        return r.json();
    },
    async getChat(id) {
        const r = await fetch(`/api/chats/${id}`);
        if (!r.ok) throw new Error('Chat no encontrado');
        return r.json();
    },
    async deleteChat(id) {
        const r = await fetch(`/api/chats/${id}`, { method: 'DELETE' });
        if (!r.ok) {
            const data = await r.json().catch(() => ({}));
            throw new Error(data.detail || 'No pude borrar el chat');
        }
        return r.json();
    },
    async getProfile() {
        const r = await fetch('/api/profile');
        if (!r.ok) throw new Error('No pude leer el perfil');
        return r.json();
    },
    async updateProfile(body) {
        const r = await fetch('/api/profile', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!r.ok) {
            const data = await r.json().catch(() => ({}));
            throw new Error(data.detail || 'No pude guardar el perfil');
        }
        return r.json();
    },
    async resetAll() {
        const r = await fetch('/api/admin/reset', { method: 'POST' });
        if (!r.ok) {
            const data = await r.json().catch(() => ({}));
            throw new Error(data.detail || 'No pude resetear');
        }
        return r.json();
    },
};

// -------------------- Helpers --------------------
function escapeHtml(s) {
    if (s == null) return '';
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function relativeTime(iso) {
    const es = state.settings.lang === 'es';
    try {
        const dt = new Date(iso);
        const seconds = Math.floor((Date.now() - dt.getTime()) / 1000);
        if (seconds < 60) return es ? 'hace unos segundos' : 'a few seconds ago';
        if (seconds < 3600) {
            const m = Math.floor(seconds / 60);
            return es ? `hace ${m} min` : `${m} min ago`;
        }
        if (seconds < 86400) {
            const h = Math.floor(seconds / 3600);
            return es ? `hace ${h} h` : `${h} h ago`;
        }
        if (seconds < 604800) {
            const d = Math.floor(seconds / 86400);
            if (es) return `hace ${d} ${d === 1 ? 'día' : 'días'}`;
            return `${d} ${d === 1 ? 'day' : 'days'} ago`;
        }
        return dt.toLocaleDateString(state.settings.lang, { day: '2-digit', month: 'short' });
    } catch {
        return iso;
    }
}

const STATUS_META = {
    ok: { labelKey: null, label: 'OK', cls: 'pill-success' },
    parse_error: { labelKey: 'status.parse', cls: 'pill-error' },
    schema_error: { labelKey: 'status.schema', cls: 'pill-warning' },
    api_error: { labelKey: 'status.api', cls: 'pill-error' },
};

function statusPillHtml(status) {
    const s = STATUS_META[status] || { label: status, cls: 'pill-neutral' };
    const label = s.labelKey ? t(s.labelKey) : s.label;
    return `<span class="pill ${s.cls}">${escapeHtml(label)}</span>`;
}
function neutralPillHtml(text) { return `<span class="pill pill-neutral">${escapeHtml(text)}</span>`; }
function accentPillHtml(text)  { return `<span class="pill pill-accent">${escapeHtml(text)}</span>`; }

function showToast(text) {
    const t = document.getElementById('toast');
    t.textContent = text;
    t.hidden = false;
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => { t.hidden = true; }, 2900);
}

function confirmDialog({ title, message = '', okLabel, cancelLabel } = {}) {
    return new Promise((resolve) => {
        const modal = document.getElementById('confirm-modal');
        const titleEl = document.getElementById('confirm-title');
        const msgEl = document.getElementById('confirm-message');
        const okBtn = document.getElementById('confirm-ok');
        const cancelBtn = document.getElementById('confirm-cancel');
        const overlay = modal.querySelector('[data-confirm-cancel]');

        titleEl.textContent = title || t('common.confirm');
        msgEl.textContent = message;
        okBtn.textContent = okLabel || t('common.confirm');
        cancelBtn.textContent = cancelLabel || t('common.cancel');
        modal.hidden = false;

        const cleanup = (result) => {
            modal.hidden = true;
            okBtn.removeEventListener('click', onOk);
            cancelBtn.removeEventListener('click', onCancel);
            overlay.removeEventListener('click', onCancel);
            document.removeEventListener('keydown', onKey, true);
            resolve(result);
        };
        const onOk = () => cleanup(true);
        const onCancel = () => cleanup(false);
        const onKey = (ev) => {
            if (ev.key === 'Escape') { ev.stopPropagation(); onCancel(); }
            else if (ev.key === 'Enter') { ev.preventDefault(); onOk(); }
        };

        okBtn.addEventListener('click', onOk);
        cancelBtn.addEventListener('click', onCancel);
        overlay.addEventListener('click', onCancel);
        document.addEventListener('keydown', onKey, true);
        setTimeout(() => okBtn.focus(), 50);
    });
}

// -------------------- Router --------------------
const ROUTES = ['/', '/chat', '/agent', '/history'];

const router = {
    init() {
        window.addEventListener('popstate', () => this.handleRoute());
        document.addEventListener('click', (ev) => {
            const a = ev.target.closest('a[data-link]');
            if (!a) return;
            ev.preventDefault();
            const href = a.getAttribute('href');
            if (href && href !== window.location.pathname) {
                this.navigate(href);
            }
        });
    },
    navigate(path) {
        history.pushState({}, '', path);
        this.handleRoute();
    },
    handleRoute() {
        let path = window.location.pathname;
        if (!ROUTES.includes(path)) path = '/';
        state.route = path;
        renderRoute();
    },
};

// -------------------- Compat con el contrato anterior (claves en español) --------------------
// El contrato JSON pasó a claves en inglés ({type, routine, ...}). Los runs y
// rutinas guardados antes del cambio conservan las claves en español en DB;
// estos helpers normalizan SOLO para display (la traza persistida no se toca).
const LEGACY_TYPE = { mensaje: 'message', rutina: 'routine', preguntas: 'questions' };

function envType(parsed) {
    if (!parsed || typeof parsed !== 'object') return null;
    return parsed.type || LEGACY_TYPE[parsed.tipo] || null;
}
function envMessage(parsed) { return parsed.message ?? parsed.mensaje ?? ''; }
function envRoutine(parsed) { return parsed.routine ?? parsed.rutina ?? null; }
function envQuestions(parsed) {
    return (parsed.questions ?? parsed.preguntas ?? []).map(q => ({
        id: q.id,
        question: q.question ?? q.pregunta ?? '',
        options: q.options ?? q.opciones ?? [],
        multiple: Boolean(q.multiple),
    }));
}
function normalizeRoutine(p) {
    if (!p || typeof p !== 'object') return {};
    return {
        goal: p.goal ?? p.objetivo,
        days_per_week: p.days_per_week ?? p.dias_por_semana,
        session_duration: p.session_duration ?? p.duracion_sesion,
        format: p.format ?? p.formato,
        exercises: (p.exercises ?? p.ejercicios ?? []).map(e => ({
            name: e.name ?? e.nombre,
            sets: e.sets ?? e.series,
            reps: e.reps ?? e.repeticiones,
            rest_sec: e.rest_sec ?? e.descanso_seg,
            notes: e.notes ?? e.notas,
        })),
        general_notes: p.general_notes ?? p.notas_generales,
        warning: p.warning ?? p.advertencia,
    };
}

// -------------------- Render: rutina --------------------
function renderRoutineHTML(rawPayload) {
    const payload = normalizeRoutine(rawPayload);
    const goal = escapeHtml(payload.goal || t('routine.noGoal'));
    const days = payload.days_per_week ?? '—';
    const duration = payload.session_duration ?? '—';
    const format = escapeHtml(payload.format || '—');
    const warning = (payload.warning || '').trim();
    const notes = (payload.general_notes || '').trim();

    const exercisesHeader = `
        <div class="exercise-header">
            <span></span>
            <span>${escapeHtml(t('routine.exercise'))}</span>
            <span class="ex-prescription">${escapeHtml(t('routine.setsReps'))}</span>
            <span class="ex-rest">${escapeHtml(t('routine.rest'))}</span>
            <span></span>
        </div>
    `;

    const exercises = (payload.exercises || []).map((ex, i) => {
        const name = escapeHtml(ex.name || t('routine.fallbackName'));
        const sets = ex.sets ?? '?';
        const reps = escapeHtml(String(ex.reps ?? '?'));
        const rest = ex.rest_sec ?? 0;
        const restLabel = rest > 0 ? `${rest}s` : '—';
        const exNotes = (ex.notes || '').trim();
        const num = String(i + 1).padStart(2, '0');
        return `
            <div class="exercise-row">
                <span class="ex-num">${num}</span>
                <span class="ex-name">${name}</span>
                <span class="ex-prescription">${sets} × ${reps}</span>
                <span class="ex-rest">${restLabel}</span>
                ${exNotes ? `<span class="ex-notes-cell">${escapeHtml(exNotes)}</span>` : '<span></span>'}
            </div>
        `;
    }).join('');

    const notesHtml = notes
        ? notes.split(/\n+/).map(l => l.trim()).filter(Boolean).map((line, i) => `
            <div class="nota-line">
                <span class="nota-num">${String(i + 1).padStart(2, '0')}</span>
                <span>${escapeHtml(line)}</span>
            </div>
        `).join('')
        : '';

    return `
        <div class="routine-eyebrow">${escapeHtml(t('routine.goal'))}</div>
        <div class="routine-objetivo">${goal}</div>
        <div class="routine-meta-row">
            <div class="routine-meta-item">
                <div class="label">${escapeHtml(t('routine.frequency'))}</div>
                <div class="value">${days}<span class="unit">${escapeHtml(t('routine.daysUnit'))}</span></div>
            </div>
            <div class="routine-meta-item">
                <div class="label">${escapeHtml(t('routine.perSession'))}</div>
                <div class="value">${duration}<span class="unit">min</span></div>
            </div>
            <div class="routine-meta-item">
                <div class="label">${escapeHtml(t('routine.format'))}</div>
                <div class="value">${format}</div>
            </div>
        </div>
        ${warning ? `
            <div class="advertencia">
                <div class="advertencia-label">${escapeHtml(t('routine.warning'))}</div>
                <div class="txt">${escapeHtml(warning)}</div>
            </div>
        ` : ''}
        <div class="exercises-list">${exercisesHeader}${exercises}</div>
        ${notes ? `
            <div class="section-heading">${escapeHtml(t('routine.generalNotes'))}</div>
            <div class="notas-generales">${notesHtml}</div>
        ` : ''}
    `;
}

// -------------------- Render: lista de chats (sidebar, compartida chat/agent) --------------------
async function reloadChats() {
    state.chats = await api.listChats(convMode());
    renderChatList();
}

function renderChatList() {
    const wrap = document.getElementById('chat-list');
    if (state.chats.length === 0) {
        wrap.innerHTML = `<div class="chat-empty-text">${escapeHtml(t('chats.empty'))}</div>`;
        return;
    }
    wrap.innerHTML = state.chats.map(c => `
        <div class="chat-item ${c.id === activeConv().chatId ? 'active' : ''}" data-chat-id="${c.id}">
            <div class="chat-item-title">${escapeHtml(c.title)}</div>
            <button class="chat-item-delete" data-delete-chat="${c.id}" aria-label="${escapeHtml(t('common.delete'))}">
                <span data-icon="trash" data-size="14"></span>
            </button>
        </div>
    `).join('');
    replaceIcons(wrap);
}

// -------------------- Render: conversación (/chat y /agent) --------------------
function convEmpty(mode) {
    return {
        eyebrow: t(`empty.${mode}.eyebrow`),
        title: t(`empty.${mode}.title`),
        sub: t(`empty.${mode}.sub`),
        examples: [t(`empty.${mode}.ex1`), t(`empty.${mode}.ex2`), t(`empty.${mode}.ex3`)],
    };
}

// ¿El último mensaje es una ronda de preguntas sin responder? En ese caso el
// composer se deshabilita: la única vía es responder las opciones.
function hasPendingQuestions(conv) {
    const last = conv.messages[conv.messages.length - 1];
    return Boolean(
        last && last.role === 'assistant' && last.run
        && envType(last.run.parsed) === 'questions'
    );
}

function updateComposerState(mode) {
    const ui = CONV_UI[mode];
    const pending = hasPendingQuestions(state.conv[mode]);
    const input = document.getElementById(ui.inputId);
    const sendBtn = document.getElementById(ui.sendBtnId);
    input.disabled = pending;
    sendBtn.disabled = pending;
    input.placeholder = pending ? t('composer.answerFirst') : t(ui.placeholderKey);
}

function renderConvMessages(mode) {
    const ui = CONV_UI[mode];
    const conv = state.conv[mode];
    const messages = document.getElementById(ui.messagesId);
    messages.innerHTML = '';
    updateComposerState(mode);

    if (conv.messages.length === 0) {
        const meta = convEmpty(mode);
        const empty = document.createElement('div');
        empty.className = 'chat-empty';
        empty.innerHTML = `
            <div class="view-eyebrow">
                <span class="mono-label">${escapeHtml(meta.eyebrow)}</span>
                <div class="view-eyebrow-rule"></div>
                <span class="mono-label">Routina</span>
            </div>
            <h3>${escapeHtml(meta.title)}</h3>
            <p>${escapeHtml(meta.sub)}</p>
            <div class="examples">
                <div class="examples-label">${escapeHtml(t('empty.tryLabel'))}</div>
                ${meta.examples.map((ex, i) => `
                    <button class="example-chip" data-example="${escapeHtml(ex)}">
                        <span class="example-chip-num">${String(i + 1).padStart(2, '0')}</span>
                        <span>${escapeHtml(ex)}</span>
                    </button>
                `).join('')}
            </div>
        `;
        messages.appendChild(empty);
        return;
    }

    conv.messages.forEach((msg, idx) => {
        const isLast = idx === conv.messages.length - 1;
        if (msg.role === 'user') {
            const node = document.createElement('div');
            node.className = 'msg-user';
            node.innerHTML = `<div class="bubble"></div>`;
            node.querySelector('.bubble').textContent = msg.content;
            messages.appendChild(node);
        } else if (msg.role === 'loading') {
            const node = document.createElement('div');
            node.className = 'msg-assistant';
            node.innerHTML = `
                <div class="assistant-card loading">
                    <div class="dots"><span></span><span></span><span></span></div>
                    <span class="loading-text">${escapeHtml(msg.text || t(ui.loadingKey))}</span>
                </div>
            `;
            messages.appendChild(node);
        } else if (msg.role === 'assistant') {
            messages.appendChild(renderAssistantMessage(msg.run, { isLast }));
        } else if (msg.role === 'error') {
            const node = document.createElement('div');
            node.className = 'msg-assistant';
            node.innerHTML = `
                <div class="assistant-card error-card">
                    <div style="font-weight:600;margin-bottom:6px;">${escapeHtml(t('err.cantGenerate'))}</div>
                    <div style="color:var(--error);font-size:.9rem;">${escapeHtml(msg.content || '')}</div>
                </div>
            `;
            messages.appendChild(node);
        }
    });

    replaceIcons(messages);

    requestAnimationFrame(() => {
        const scroller = document.getElementById(ui.scrollId);
        scroller.scrollTop = scroller.scrollHeight;
    });
}

// Resumen legible de cada tool call para el log inline del agente.
// Acepta también los nombres del contrato anterior en español (runs viejos).
function toolChipHtml(tc) {
    const r = tc.result || {};
    const a = tc.args || {};
    let detail = '';
    if (tc.name === 'search_exercises' || tc.name === 'buscar_ejercicios') {
        const filters = [a.muscle_group ?? a.grupo, a.level ?? a.nivel].filter(Boolean).join(', ');
        detail = `${filters ? filters + ' ' : ''}→ ${r.total ?? '?'}`;
    } else if (tc.name === 'validate_routine' || tc.name === 'validar_rutina') {
        const valid = r.valid ?? r.valida;
        detail = valid ? t('chip.valid') : t('chip.errors', (r.errors || r.errores || []).length);
    } else if (tc.name === 'save_routine' || tc.name === 'guardar_rutina') {
        const saved = r.saved ?? r.guardada;
        detail = saved ? `✓ #${r.routine_id}` : t('chip.invalid');
    } else if (tc.name === 'ask_user' || tc.name === 'preguntar_usuario') {
        detail = t('chip.questions', (a.questions || a.preguntas || []).length);
    } else if (r.error) {
        detail = t('chip.error');
    }
    return `<span class="tool-chip">${icon('wrench', 11)}<span>${escapeHtml(tc.name)}</span>${detail ? `<span class="tool-chip-detail">${escapeHtml(detail)}</span>` : ''}</span>`;
}

// Card de preguntas con opciones (tool ask_user). Si no es interactiva
// (ya respondida o cargada del historial), se muestran las opciones deshabilitadas.
function renderPreguntasHtml(questions, interactive) {
    const blocks = (questions || []).map((q, qi) => `
        <div class="pregunta-block" data-pregunta-id="${escapeHtml(q.id || String(qi))}" data-multiple="${q.multiple ? '1' : '0'}">
            <div class="pregunta-texto">${escapeHtml(q.question || '')}</div>
            <div class="opciones">
                ${(q.options || []).map(op => `
                    <button class="opcion-btn" type="button" data-opcion="${escapeHtml(op)}" ${interactive ? '' : 'disabled'}>${escapeHtml(op)}</button>
                `).join('')}
            </div>
        </div>
    `).join('');
    return `
        <div class="preguntas-card">
            <div class="preguntas-label">${escapeHtml(t('questions.label'))}</div>
            ${blocks}
            ${interactive ? `
                <div class="preguntas-actions">
                    <button class="btn btn-primary" data-responder disabled>${escapeHtml(t('questions.answer'))}</button>
                </div>
            ` : ''}
        </div>
    `;
}

function renderAssistantMessage(run, opts = {}) {
    const wrap = document.createElement('div');
    wrap.className = 'msg-assistant';

    let cardHtml = '';
    let cardClass = 'assistant-card';
    let actionsHtml = '';
    // Log de tools usadas por el agente en este turno (los runs de chat no tienen).
    const toolLogHtml = (run.tool_calls && run.tool_calls.length)
        ? `<div class="tool-log">${run.tool_calls.map(toolChipHtml).join('')}</div>`
        : '';

    if (run.status === 'api_error') {
        cardClass += ' error-card';
        cardHtml = `
            <div style="margin-bottom:6px;">${statusPillHtml('api_error')}</div>
            <div style="font-weight:600;margin-bottom:6px;">${escapeHtml(t('err.apiCall'))}</div>
            <div class="code-block" style="max-height:200px;">${escapeHtml(run.api_error || '')}</div>
        `;
    } else if (run.status === 'parse_error') {
        cardClass += ' error-card';
        cardHtml = `
            <div style="margin-bottom:6px;">${statusPillHtml('parse_error')}</div>
            <div style="font-weight:600;margin-bottom:8px;">${escapeHtml(t('err.noValidJson'))}</div>
            <div style="color:var(--text-muted);font-size:.9rem;margin-bottom:10px;">${escapeHtml(run.parse_error || '')}</div>
            <details><summary style="cursor:pointer;color:var(--accent);font-size:.85rem;">${escapeHtml(t('err.rawResponse'))}</summary>
                <div class="code-block" style="margin-top:10px;">${escapeHtml(run.raw || t('err.rawEmpty'))}</div>
            </details>
        `;
    } else if (run.status === 'schema_error') {
        cardClass += ' warning-card';
        const errs = (run.schema_errors || []).map(e => `<li>${escapeHtml(e)}</li>`).join('');
        cardHtml = `
            <div style="margin-bottom:6px;">${statusPillHtml('schema_error')}</div>
            <div style="font-weight:600;margin-bottom:8px;">${escapeHtml(t('err.schemaMismatch'))}</div>
            <ul class="errors-list">${errs}</ul>
            <details style="margin-top:14px;"><summary style="cursor:pointer;color:var(--accent);font-size:.85rem;">${escapeHtml(t('err.viewJson'))}</summary>
                <div class="code-block" style="margin-top:10px;">${escapeHtml(JSON.stringify(run.parsed, null, 2))}</div>
            </details>
        `;
        // Si a pesar del schema_error hay preguntas (ej. el agente mandó más de las
        // permitidas), se muestran igual para que la conversación pueda continuar.
        if (envType(run.parsed) === 'questions') {
            cardHtml += renderPreguntasHtml(envQuestions(run.parsed), Boolean(opts.isLast));
        }
    } else if (run.status === 'ok') {
        // La respuesta es un sobre { type: "routine"|"message"|"questions", ... }.
        // La telemetría del run (latencia, tokens, modelo) vive en /historial, no acá.
        const parsed = run.parsed || {};
        const type = envType(parsed);
        if (type === 'message') {
            cardHtml = `<div class="assistant-text">${escapeHtml(envMessage(parsed))}</div>`;
        } else if (type === 'questions') {
            cardHtml = renderPreguntasHtml(envQuestions(parsed), Boolean(opts.isLast));
        } else {
            const routine = type === 'routine' ? envRoutine(parsed) : parsed;
            cardHtml = renderRoutineHTML(routine || {});
            const savedAttr = run._saved ? 'disabled' : '';
            const savedLabel = run._saved
                ? `<span>${escapeHtml(t('routine.saved'))}</span>`
                : `<span>${escapeHtml(t('routine.save'))}</span>`;
            actionsHtml = `
                <div class="assistant-card-actions">
                    <button class="btn btn-primary" data-save-run="${run.run_id}" ${savedAttr}>${savedLabel}</button>
                </div>
            `;
        }
    }

    wrap.innerHTML = `${toolLogHtml}<div class="${cardClass}">${cardHtml}${actionsHtml}</div>`;
    return wrap;
}

// -------------------- Render: home (/) --------------------
async function renderHome() {
    const grid = document.getElementById('routines-grid');
    grid.innerHTML = `<div class="empty-state"><p>${escapeHtml(t('common.loading'))}</p></div>`;

    let data;
    try {
        data = await api.listRoutines(state.routinesFilter);
    } catch (e) {
        grid.innerHTML = `<div class="empty-state"><p>Error: ${escapeHtml(e.message)}</p></div>`;
        return;
    }

    document.getElementById('home-filters').hidden = data.formats.length === 0;

    const sel = document.getElementById('filter-format');
    const current = state.routinesFilter.format || '';
    sel.innerHTML = `<option value="">${escapeHtml(t('home.allFormats'))}</option>` +
        data.formats.map(f => `<option value="${escapeHtml(f)}" ${f === current ? 'selected' : ''}>${escapeHtml(f)}</option>`).join('');

    grid.innerHTML = '';
    if (data.routines.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <div class="ico-wrap">
                    <span>${escapeHtml(t('home.emptyLabel'))}</span>
                    <div class="ico-wrap-rule"></div>
                </div>
                <h4>${escapeHtml(t('home.emptyTitle'))}</h4>
                <p>${t('home.emptyBody')}</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = data.routines.map((r, i) => {
        const num = String(i + 1).padStart(2, '0');
        return `
            <div class="routine-summary-card" data-open-routine="${r.id}">
                <span class="index-num">${num}</span>
                <div>
                    <div class="title">${escapeHtml(r.goal || t('routine.noGoal'))}</div>
                    <div class="meta">${escapeHtml(r.format || '—')} · ${relativeTime(r.created_at)}</div>
                </div>
                <span class="summary-stat">${r.days_per_week ?? '—'}× · ${r.session_duration ?? '—'}'</span>
                <span class="summary-tag">${escapeHtml(r.format || '—').slice(0, 20)}</span>
                <button class="routine-delete-btn" data-delete-routine="${r.id}" aria-label="${escapeHtml(t('routine.deleteTitle'))}" type="button">
                    ${icon('trash', 14)}
                </button>
                <span class="summary-arrow">›</span>
            </div>
        `;
    }).join('');
}

async function deleteRoutine(routineId) {
    const ok = await confirmDialog({
        title: t('routine.deleteTitle'),
        message: t('routine.deleteMsg'),
        okLabel: t('common.delete'),
    });
    if (!ok) return;
    try {
        await api.deleteRoutine(routineId);
        showToast(t('toast.routineDeleted'));
        renderHome();
    } catch (e) {
        showToast(t('toast.cantDelete') + e.message);
    }
}

// -------------------- Render: historial (/history) --------------------
async function renderHistorial() {
    const list = document.getElementById('runs-list');
    list.innerHTML = `<div class="empty-state"><p>${escapeHtml(t('common.loading'))}</p></div>`;

    let runs;
    try {
        runs = await api.listRuns(state.runsFilter);
    } catch (e) {
        list.innerHTML = `<div class="empty-state"><p>Error: ${escapeHtml(e.message)}</p></div>`;
        return;
    }

    list.innerHTML = '';
    if (runs.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <div class="ico-wrap">
                    <span>${escapeHtml(t('history.emptyLabel'))}</span>
                    <div class="ico-wrap-rule"></div>
                </div>
                <h4>${escapeHtml(t('history.emptyTitle'))}</h4>
                <p>${escapeHtml(t('history.emptyBody'))}</p>
            </div>
        `;
        return;
    }

    list.innerHTML = runs.map(r => {
        const preview = (r.user_input || '').replace(/\s+/g, ' ').trim();
        const truncated = preview.length > 130 ? preview.slice(0, 130) + '…' : preview;
        return `
            <div class="run-row" data-open-run="${r.id}">
                <div class="top">
                    ${statusPillHtml(r.status)}
                    ${neutralPillHtml(r.provider || 'openai')}
                    ${neutralPillHtml(r.model)}
                    ${neutralPillHtml((r.lang || 'es').toUpperCase())}
                </div>
                <div class="preview">${escapeHtml(truncated || t('history.noInput'))}</div>
                <div class="meta">
                    <span>${relativeTime(r.created_at)}</span>
                    <span class="dot">·</span>
                    <span>${r.latency_ms ?? '—'} ms</span>
                    <span class="dot">·</span>
                    <span>${r.input_tokens ?? '—'} / ${r.output_tokens ?? '—'} tok</span>
                </div>
            </div>
        `;
    }).join('');
}

// -------------------- Render: route dispatcher --------------------
function renderRoute() {
    // mode-nav active highlight
    document.querySelectorAll('[data-route]').forEach(el => {
        el.classList.toggle('active', el.dataset.route === state.route);
    });

    // show/hide chat sidebar section (compartida entre /chat y /agent)
    const isConvRoute = state.route === '/chat' || state.route === '/agent';
    document.getElementById('sidebar-chat-section').hidden = !isConvRoute;

    // toggle views
    const viewMap = {
        '/': 'view-home',
        '/chat': 'view-chat',
        '/agent': 'view-agent',
        '/history': 'view-historial',
    };
    const targetId = viewMap[state.route] || 'view-home';
    document.querySelectorAll('.view').forEach(v => {
        v.classList.toggle('active', v.id === targetId);
    });

    // route-specific render
    if (state.route === '/') {
        renderHome();
    } else if (isConvRoute) {
        renderConvMessages(convMode());
        reloadChats();
    } else if (state.route === '/history') {
        renderHistorial();
    }
}

// -------------------- Modales --------------------
function openModal(title, bodyHtml, panelClass = '', titleBadgeHtml = '') {
    const modal = document.getElementById('modal');
    modal.querySelector('.modal-panel').className = 'modal-panel' + (panelClass ? ' ' + panelClass : '');
    document.getElementById('modal-title').innerHTML = escapeHtml(title) + (titleBadgeHtml || '');
    document.getElementById('modal-body').innerHTML = bodyHtml;
    replaceIcons(document.getElementById('modal-body'));
    modal.hidden = false;
}
function closeModal() { document.getElementById('modal').hidden = true; }

async function openRoutineModal(id) {
    const data = await api.getRoutine(id);
    const goal = data.payload.goal || data.payload.objetivo;
    openModal(goal || `${t('nav.routines')} #${data.id}`, renderRoutineHTML(data.payload));
}

async function openRunModal(id) {
    const data = await api.getRun(id);

    const tabsBar = `
        <div class="run-tabs">
            <button class="run-tab active" data-tab="input">${escapeHtml(t('run.tab.input'))}</button>
            <button class="run-tab" data-tab="prompt">${escapeHtml(t('run.tab.prompt'))}</button>
            <button class="run-tab" data-tab="response">${escapeHtml(t('run.tab.response'))}</button>
            <button class="run-tab" data-tab="errors">${escapeHtml(t('run.tab.errors'))}</button>
            <button class="run-tab" data-tab="trace">${escapeHtml(t('run.tab.trace'))}</button>
            <button class="run-tab" data-tab="details">${escapeHtml(t('run.tab.details'))}</button>
        </div>
    `;
    const inputPane = `<div data-pane="input"><div class="code-block">${escapeHtml(data.user_input || t('run.empty'))}</div></div>`;
    const promptPane = `<div data-pane="prompt" hidden>
        <div style="color:var(--text-muted);font-size:.88rem;margin-bottom:8px;">${escapeHtml(t('run.systemPromptUsed'))}</div>
        <div class="code-block">${escapeHtml(data.system_prompt || '')}</div>
    </div>`;
    const responsePane = `<div data-pane="response" hidden>
        ${data.parsed_json
            ? `<div class="code-block">${escapeHtml(JSON.stringify(data.parsed_json, null, 2))}</div>`
            : `<div class="code-block">${escapeHtml(data.raw_response || t('run.noResponse'))}</div>`}
    </div>`;
    let errorsContent = '';
    if (data.parse_error) errorsContent += `<div class="error-summary"><strong>${escapeHtml(t('run.parseError'))}</strong> ${escapeHtml(data.parse_error)}</div>`;
    if (data.schema_errors && data.schema_errors.length) {
        errorsContent += `<div style="font-weight:600;margin-bottom:6px;">${escapeHtml(t('run.schemaErrors'))}</div>`;
        errorsContent += `<ul class="errors-list">${data.schema_errors.map(e => `<li>${escapeHtml(e)}</li>`).join('')}</ul>`;
    }
    if (!errorsContent) errorsContent = `<div style="color:var(--text-muted);font-size:.92rem;">${escapeHtml(t('run.noErrors'))}</div>`;
    const errorsPane = `<div data-pane="errors" hidden>${errorsContent}</div>`;
    const tracePane = `<div data-pane="trace" hidden>
        <div class="code-block">${escapeHtml(JSON.stringify(data.messages, null, 2))}</div>
    </div>`;
    const detailRows = [
        [t('run.provider'), data.provider || 'openai'],
        [t('run.model'), data.model],
        [t('run.language'), (data.lang || 'es').toUpperCase()],
        [t('run.date'), relativeTime(data.created_at)],
        [t('run.latency'), `${data.latency_ms ?? '—'} ms`],
        [t('run.tokensIn'), data.input_tokens ?? '—'],
        [t('run.tokensOut'), data.output_tokens ?? '—'],
    ];
    const detailsPane = `<div data-pane="details" hidden>
        <div class="run-detail-grid">
            ${detailRows.map(([k, v]) => `
                <div class="run-detail-row">
                    <span class="k">${escapeHtml(k)}</span>
                    <span class="v">${escapeHtml(String(v))}</span>
                </div>
            `).join('')}
        </div>
    </div>`;

    // Alto fijo: al cambiar de pestaña el panel no hace shift según el contenido.
    openModal(
        `Run #${data.id}`,
        tabsBar + inputPane + promptPane + responsePane + errorsPane + tracePane + detailsPane,
        'modal-panel--run',
        statusPillHtml(data.status),
    );
}

// -------------------- Modal one-shot ("+ Nueva rutina") --------------------
function openOneshotModal() {
    document.getElementById('oneshot-input-block').hidden = false;
    document.getElementById('oneshot-result-block').hidden = true;
    document.getElementById('oneshot-result-block').innerHTML = '';
    document.getElementById('oneshot-input').value = '';
    state.oneshot.lastRunId = null;
    state.oneshot.isSaved = false;
    document.getElementById('oneshot-modal').hidden = false;
    setTimeout(() => document.getElementById('oneshot-input').focus(), 50);
}

function closeOneshotModal() {
    document.getElementById('oneshot-modal').hidden = true;
}

// -------------------- Modal "Acerca de" --------------------
function openAboutModal() {
    document.getElementById('about-modal').hidden = false;
}

function closeAboutModal() {
    document.getElementById('about-modal').hidden = true;
}

async function runOneshotGenerate() {
    const input = document.getElementById('oneshot-input');
    const text = input.value.trim();
    if (!text) {
        showToast(t('toast.writeCase'));
        return;
    }
    if (!selectedProviderHasKey()) {
        showToast(t('toast.missingKey', providerForModel(state.settings.model)));
        return;
    }
    const btn = document.getElementById('oneshot-generate-btn');
    btn.disabled = true;
    btn.innerHTML = `<span class="dots"><span></span><span></span><span></span></span><span>${escapeHtml(t('oneshot.generating'))}</span>`;

    const body = {
        user_input: text,
        model: state.settings.model,
        system_prompt: activePrompt('oneshot'),
        lang: state.settings.lang,
    };

    try {
        const result = await api.oneshotGenerate(body);
        state.oneshot.lastRunId = result.run_id;
        state.oneshot.isSaved = false;
        renderOneshotResult(result);
    } catch (e) {
        renderOneshotError(e.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<span data-icon="sparkles" data-size="14"></span><span>${escapeHtml(t('oneshot.generate'))}</span>`;
        replaceIcons(btn);
    }
}

function renderOneshotResult(result) {
    document.getElementById('oneshot-input-block').hidden = true;
    const block = document.getElementById('oneshot-result-block');
    block.hidden = false;

    if (result.status === 'ok') {
        block.innerHTML = `
            ${renderRoutineHTML(result.parsed)}
            <div class="oneshot-result-actions">
                <button class="btn btn-primary" id="oneshot-save-btn">
                    ${icon('save', 14)} <span>${escapeHtml(t('oneshot.saveRoutine'))}</span>
                </button>
                <button class="btn btn-outline" id="oneshot-discard-btn">${escapeHtml(t('oneshot.discard'))}</button>
                <button class="btn btn-ghost" id="oneshot-regenerate-btn">${escapeHtml(t('oneshot.another'))}</button>
            </div>
        `;
    } else if (result.status === 'parse_error') {
        block.innerHTML = `
            <div class="error-summary"><strong>${escapeHtml(t('oneshot.invalidJson'))}</strong> ${escapeHtml(result.parse_error || '')}</div>
            <details style="margin-top:8px;"><summary style="cursor:pointer;color:var(--accent);font-size:.85rem;">${escapeHtml(t('err.rawResponse'))}</summary>
                <div class="code-block" style="margin-top:8px;">${escapeHtml(result.raw || '')}</div>
            </details>
            <div class="oneshot-result-actions">
                <button class="btn btn-outline" id="oneshot-discard-btn">${escapeHtml(t('oneshot.close'))}</button>
                <button class="btn btn-ghost" id="oneshot-regenerate-btn">${escapeHtml(t('oneshot.retry'))}</button>
            </div>
        `;
    } else if (result.status === 'schema_error') {
        const errs = (result.schema_errors || []).map(e => `<li>${escapeHtml(e)}</li>`).join('');
        block.innerHTML = `
            <div class="error-summary"><strong>${escapeHtml(t('oneshot.schemaFail'))}</strong></div>
            <ul class="errors-list">${errs}</ul>
            <details style="margin-top:12px;"><summary style="cursor:pointer;color:var(--accent);font-size:.85rem;">${escapeHtml(t('err.viewJson'))}</summary>
                <div class="code-block" style="margin-top:8px;">${escapeHtml(JSON.stringify(result.parsed, null, 2))}</div>
            </details>
            <div class="oneshot-result-actions">
                <button class="btn btn-outline" id="oneshot-discard-btn">${escapeHtml(t('oneshot.close'))}</button>
                <button class="btn btn-ghost" id="oneshot-regenerate-btn">${escapeHtml(t('oneshot.retry'))}</button>
            </div>
        `;
    } else if (result.status === 'api_error') {
        block.innerHTML = `
            <div class="error-summary"><strong>${escapeHtml(t('oneshot.apiError'))}</strong> ${escapeHtml(result.api_error || '')}</div>
            <div class="oneshot-result-actions">
                <button class="btn btn-outline" id="oneshot-discard-btn">${escapeHtml(t('oneshot.close'))}</button>
                <button class="btn btn-ghost" id="oneshot-regenerate-btn">${escapeHtml(t('oneshot.retry'))}</button>
            </div>
        `;
    }
    replaceIcons(block);
}

function renderOneshotError(msg) {
    document.getElementById('oneshot-input-block').hidden = true;
    const block = document.getElementById('oneshot-result-block');
    block.hidden = false;
    block.innerHTML = `
        <div class="error-summary"><strong>${escapeHtml(t('common.error'))}</strong> ${escapeHtml(msg)}</div>
        <div class="oneshot-result-actions">
            <button class="btn btn-outline" id="oneshot-discard-btn">${escapeHtml(t('oneshot.close'))}</button>
            <button class="btn btn-ghost" id="oneshot-regenerate-btn">${escapeHtml(t('oneshot.retry'))}</button>
        </div>
    `;
}

async function saveOneshotRoutine() {
    if (!state.oneshot.lastRunId || state.oneshot.isSaved) return;
    try {
        await api.saveRoutine(state.oneshot.lastRunId);
        state.oneshot.isSaved = true;
        showToast(t('toast.routineSaved'));
        closeOneshotModal();
        if (state.route === '/') renderHome();
    } catch (e) {
        showToast(t('toast.cantSave') + e.message);
    }
}

// -------------------- Conversación (/chat y /agent) actions --------------------
function newConv() {
    const mode = convMode();
    const conv = state.conv[mode];
    conv.chatId = null;
    conv.messages = [];
    renderChatList();
    renderConvMessages(mode);
    setTimeout(() => document.getElementById(CONV_UI[mode].inputId).focus(), 50);
}

async function loadConv(chatId) {
    const mode = convMode();
    const conv = state.conv[mode];
    conv.chatId = chatId;
    renderChatList();
    document.getElementById(CONV_UI[mode].messagesId).innerHTML = `<div class="empty-state"><p>Cargando…</p></div>`;
    try {
        const data = await api.getChat(chatId);
        conv.messages = [];
        for (const run of data.runs) {
            conv.messages.push({ role: 'user', content: run.user_input });
            conv.messages.push({
                role: 'assistant',
                run: {
                    run_id: run.id,
                    status: run.status,
                    parsed: run.parsed_json,
                    parse_error: run.parse_error,
                    schema_errors: run.schema_errors,
                    raw: run.raw_response,
                    api_error: run.status === 'api_error' ? run.raw_response || 'Error API' : null,
                    latency_ms: run.latency_ms,
                    input_tokens: run.input_tokens,
                    output_tokens: run.output_tokens,
                    model: run.model,
                    tool_calls: run.tool_calls || [],
                    _saved: false,
                }
            });
        }
        renderConvMessages(mode);
    } catch (e) {
        document.getElementById(CONV_UI[mode].messagesId).innerHTML = `<div class="empty-state"><p>${escapeHtml(e.message)}</p></div>`;
    }
}

async function deleteChat(chatId) {
    const ok = await confirmDialog({
        title: t('chat.deleteTitle'),
        message: t('chat.deleteMsg'),
        okLabel: t('common.delete'),
    });
    if (!ok) return;
    try {
        await api.deleteChat(chatId);
        const conv = activeConv();
        if (conv.chatId === chatId) {
            conv.chatId = null;
            conv.messages = [];
            renderConvMessages(convMode());
        }
        await reloadChats();
        showToast(t('toast.chatDeleted'));
    } catch (e) {
        showToast(t('toast.cantDelete') + e.message);
    }
}

// Texto de progreso en vivo por tool (el agente streamea qué está haciendo).
function toolProgressLabel(name) {
    const key = `tool.${name}`;
    const dict = I18N[state.settings.lang] || I18N.es;
    return dict[key] ? t(key) : t('agent.usingTool', name);
}

// `presetText` permite enviar sin pasar por el textarea (respuestas de preguntas).
async function convSend(presetText = null) {
    if (state.isGenerating) return;
    const mode = convMode();
    const ui = CONV_UI[mode];
    const conv = state.conv[mode];
    const input = document.getElementById(ui.inputId);
    const text = (presetText != null ? presetText : input.value).trim();
    if (!text) return;
    if (!selectedProviderHasKey()) {
        showToast(t('toast.missingKey', providerForModel(state.settings.model)));
        return;
    }

    conv.messages.push({ role: 'user', content: text });
    const loadingMsg = { role: 'loading', text: null };
    conv.messages.push(loadingMsg);
    state.isGenerating = true;
    if (presetText == null) {
        input.value = '';
        autoresizeTextarea(input);
    }
    renderConvMessages(mode);

    const body = {
        user_input: text,
        model: state.settings.model,
        system_prompt: activePrompt(mode),
        chat_id: conv.chatId,
        lang: state.settings.lang,
    };

    // Progreso en vivo: cada evento de tool actualiza el texto del indicador.
    const onAgentEvent = (evt) => {
        if (evt.type !== 'tool') return;
        loadingMsg.text = toolProgressLabel(evt.name);
        const el = document.querySelector(`#${ui.messagesId} .assistant-card.loading .loading-text`);
        if (el) el.textContent = loadingMsg.text;
    };

    try {
        const result = mode === 'agent'
            ? await api.agentGenerate(body, onAgentEvent)
            : await api.chatGenerate(body);
        conv.messages = conv.messages.filter(m => m.role !== 'loading');
        conv.messages.push({ role: 'assistant', run: result });
        if (conv.chatId == null && result.chat_id) {
            conv.chatId = result.chat_id;
        }
        await reloadChats();
    } catch (e) {
        conv.messages = conv.messages.filter(m => m.role !== 'loading');
        conv.messages.push({ role: 'error', content: e.message });
    } finally {
        state.isGenerating = false;
        renderConvMessages(mode);
    }
}

async function resetAll() {
    const ok = await confirmDialog({
        title: t('reset.title'),
        message: t('reset.msg'),
        okLabel: t('reset.ok'),
    });
    if (!ok) return;
    try {
        await api.resetAll();
        state.chats = [];
        state.conv.chat = { chatId: null, messages: [] };
        state.conv.agent = { chatId: null, messages: [] };
        showToast(t('toast.allDeleted'));
        renderChatList();
        renderRoute();
    } catch (e) {
        showToast(t('toast.cantDelete') + e.message);
    }
}

async function saveRunFromChat(runId) {
    try {
        await api.saveRoutine(runId);
        for (const m of activeConv().messages) {
            if (m.role === 'assistant' && m.run && m.run.run_id === runId) {
                m.run._saved = true;
            }
        }
        renderConvMessages(convMode());
        showToast(t('toast.routineSaved'));
    } catch (e) {
        showToast(t('toast.cantSave') + e.message);
    }
}

// -------------------- Settings drawer --------------------
function openDrawer() {
    state.drawerOpen = true;
    document.getElementById('settings-drawer').hidden = false;

    // El <select> se agrupa por proveedor con <optgroup>.
    const byProvider = {};
    (state.config.available_models || []).forEach(m => {
        (byProvider[m.provider] = byProvider[m.provider] || []).push(m.id);
    });
    const modelSel = document.getElementById('model-select');
    modelSel.innerHTML = Object.entries(byProvider)
        .map(([provider, ids]) => `<optgroup label="${escapeHtml(provider)}">${ids
            .map(id => `<option value="${escapeHtml(id)}" ${id === state.settings.model ? 'selected' : ''}>${escapeHtml(id)}</option>`)
            .join('')}</optgroup>`)
        .join('');

    refreshApiKeyStatus();
    applyLangLabel();

    document.getElementById('schema-path-oneshot').textContent = state.config.schema_paths?.oneshot || '…';
    document.getElementById('schema-path-chat').textContent = state.config.schema_paths?.chat || '…';
    document.getElementById('schema-path-agent').textContent = state.config.schema_paths?.agent || '…';
    document.getElementById('prompt-lang-hint').textContent = t('settings.promptLangHint');
}
// El estado de la API key es el del proveedor del modelo seleccionado.
function refreshApiKeyStatus() {
    const apiStatus = document.getElementById('api-key-status');
    if (!apiStatus) return;
    const has = selectedProviderHasKey();
    apiStatus.className = 'api-key-status ' + (has ? 'ok' : 'missing');
    apiStatus.innerHTML = has
        ? `${icon('check', 14)} <span>${escapeHtml(t('settings.keyOk'))}</span>`
        : `${icon('alert-triangle', 14)} <span>${escapeHtml(t('settings.keyMissing'))}</span>`;

    const hint = document.getElementById('api-key-hint');
    if (!hint) return;
    if (has) {
        hint.hidden = true;
    } else {
        const provider = providerForModel(state.settings.model);
        const envVar = state.config?.provider_envs?.[provider] || 'API key';
        hint.hidden = false;
        hint.innerHTML = t('settings.keyHint', escapeHtml(provider), escapeHtml(envVar));
    }
}
function closeDrawer() { state.drawerOpen = false; document.getElementById('settings-drawer').hidden = true; }
function commitSettingsFromDOM() {
    state.settings.model = document.getElementById('model-select').value;
    saveSettings();
}

// -------------------- Modal editor de system prompt --------------------
// Se edita el prompt del modo indicado EN el idioma activo (un prompt por modo y
// por idioma). El título indica modo + idioma para que sea evidente cuál se toca.
const PROMPT_MODES = ['oneshot', 'chat', 'agent'];

function promptModalTitle(mode) {
    return `${t(`prompt.${mode}`)} · ${state.settings.lang.toUpperCase()}`;
}

function openPromptModal(mode) {
    if (!PROMPT_MODES.includes(mode)) return;
    state.promptModalMode = mode;
    document.getElementById('prompt-modal-title').textContent = promptModalTitle(mode);
    const ta = document.getElementById('prompt-modal-textarea');
    ta.value = activePrompt(mode);
    document.getElementById('prompt-modal').hidden = false;
    setTimeout(() => {
        ta.focus();
        ta.setSelectionRange(0, 0);
        ta.scrollTop = 0;
    }, 50);
}

function hidePromptModal() {
    state.promptModalMode = null;
    document.getElementById('prompt-modal').hidden = true;
}

// El textarea es un borrador: no toca settings hasta "Guardar". Cerrar/cancelar descarta,
// con confirmación si hay cambios sin guardar.
async function cancelPromptModal() {
    const mode = state.promptModalMode;
    if (!PROMPT_MODES.includes(mode)) return;
    const draft = document.getElementById('prompt-modal-textarea').value;
    if (draft !== activePrompt(mode)) {
        const ok = await confirmDialog({
            title: t('discard.title'),
            message: t('discard.promptMsg'),
            okLabel: t('discard.ok'),
            cancelLabel: t('discard.keep'),
        });
        if (!ok) return;
    }
    hidePromptModal();
}

function savePromptModal() {
    const mode = state.promptModalMode;
    if (!PROMPT_MODES.includes(mode)) return;
    state.settings.prompts[state.settings.lang][mode] = document.getElementById('prompt-modal-textarea').value;
    saveSettings();
    hidePromptModal();
    showToast(t('toast.promptSaved'));
}

// -------------------- Modal perfil del usuario --------------------
// Igual que el editor de prompts: los checkboxes son un borrador que se persiste
// (vía PUT /api/profile) recién al apretar Guardar.
let profileSnapshot = null;   // JSON del perfil cargado, para detectar cambios sin guardar

function renderCheckGrid(containerId, options, checkedIds) {
    const checked = new Set(checkedIds);
    // Los labels del vocabulario son bilingües ({es, en}); se muestra el del idioma activo.
    const lang = state.settings.lang;
    document.getElementById(containerId).innerHTML = options.map(o => `
        <label class="check-item">
            <input type="checkbox" value="${escapeHtml(o.id)}" ${checked.has(o.id) ? 'checked' : ''}>
            <span>${escapeHtml(o.label[lang] || o.label.es || o.label)}</span>
        </label>
    `).join('');
}

function collectProfileDraft() {
    const collect = (id) => Array.from(
        document.querySelectorAll(`#${id} input:checked`)
    ).map(i => i.value);
    return {
        equipment: collect('profile-equipment'),
        injuries: collect('profile-injuries'),
        notes: document.getElementById('profile-notes').value.trim(),
    };
}

async function openProfileModal() {
    let data;
    try {
        data = await api.getProfile();
    } catch (e) {
        showToast(e.message);
        return;
    }
    renderCheckGrid('profile-equipment', data.vocab.equipment, data.profile.equipment);
    renderCheckGrid('profile-injuries', data.vocab.injuries, data.profile.injuries);
    document.getElementById('profile-notes').value = data.profile.notes || '';
    document.getElementById('profile-modal').hidden = false;
    profileSnapshot = JSON.stringify(collectProfileDraft());
}

function hideProfileModal() {
    profileSnapshot = null;
    document.getElementById('profile-modal').hidden = true;
}

async function cancelProfileModal() {
    if (profileSnapshot !== null && JSON.stringify(collectProfileDraft()) !== profileSnapshot) {
        const ok = await confirmDialog({
            title: t('discard.title'),
            message: t('discard.profileMsg'),
            okLabel: t('discard.ok'),
            cancelLabel: t('discard.keep'),
        });
        if (!ok) return;
    }
    hideProfileModal();
}

async function saveProfileModal() {
    try {
        await api.updateProfile(collectProfileDraft());
        hideProfileModal();
        showToast(t('toast.profileSaved'));
    } catch (e) {
        showToast(t('toast.cantSave') + e.message);
    }
}

async function restorePromptDefault() {
    const mode = state.promptModalMode;
    if (!PROMPT_MODES.includes(mode)) return;
    const ok = await confirmDialog({
        title: t('prompt.restoreTitle'),
        message: t('prompt.restoreMsg'),
        okLabel: t('prompt.restoreOk'),
    });
    if (!ok) return;
    const prompts = await api.getSystemPrompts();
    document.getElementById('prompt-modal-textarea').value = prompts[mode]?.[state.settings.lang] || '';
}

// -------------------- Sidebar collapse --------------------
function applySidebarCollapse() {
    document.getElementById('app').classList.toggle('sidebar-collapsed', state.sidebarCollapsed);
    localStorage.setItem('routina:sidebar-collapsed', state.sidebarCollapsed ? '1' : '0');
}
function toggleSidebar() { state.sidebarCollapsed = !state.sidebarCollapsed; applySidebarCollapse(); }

// -------------------- Theme --------------------
function applyTheme() {
    document.documentElement.setAttribute('data-theme', state.theme);
    const iconEl = document.getElementById('theme-icon');
    const labelEl = document.getElementById('theme-label');
    if (iconEl) {
        iconEl.dataset.icon = state.theme === 'dark' ? 'moon' : 'sun';
        iconEl.innerHTML = icon(iconEl.dataset.icon, 16);
    }
    if (labelEl) labelEl.textContent = state.theme === 'dark' ? t('theme.dark') : t('theme.light');
    localStorage.setItem(THEME_KEY, state.theme);
}
function toggleTheme() {
    state.theme = state.theme === 'dark' ? 'light' : 'dark';
    applyTheme();
}

// -------------------- Idioma --------------------
function applyLangLabel() {
    const labelEl = document.getElementById('lang-label');
    if (labelEl) labelEl.textContent = state.settings.lang === 'es' ? 'Español' : 'English';
    const hint = document.getElementById('prompt-lang-hint');
    if (hint) hint.textContent = t('settings.promptLangHint');
}

// Cambiar el idioma re-renderiza toda la UI y cambia el prompt default activo.
function toggleLang() {
    state.settings.lang = state.settings.lang === 'es' ? 'en' : 'es';
    saveSettings();
    applyI18n();
    applyLangLabel();
    applyTheme();          // refresca el label del tema en el idioma nuevo
    refreshApiKeyStatus();
    renderChatList();
    renderRoute();
}

// -------------------- Textarea autoresize --------------------
function autoresizeTextarea(ta) {
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 220) + 'px';
}

// -------------------- Event delegation --------------------
function bindEvents() {
    // Sidebar
    document.querySelector('.sidebar').addEventListener('click', (ev) => {
        if (ev.target.closest('#collapse-sidebar')) { toggleSidebar(); return; }
        if (ev.target.closest('#new-chat-btn')) { newConv(); return; }
        if (ev.target.closest('#open-profile')) { openProfileModal(); return; }
        if (ev.target.closest('#open-settings')) { openDrawer(); return; }
        const delBtn = ev.target.closest('[data-delete-chat]');
        if (delBtn) {
            ev.stopPropagation();
            deleteChat(parseInt(delBtn.dataset.deleteChat, 10));
            return;
        }
        const chatBtn = ev.target.closest('[data-chat-id]');
        if (chatBtn) loadConv(parseInt(chatBtn.dataset.chatId, 10));
    });

    document.getElementById('show-sidebar').addEventListener('click', toggleSidebar);

    // Drawer
    document.getElementById('settings-drawer').addEventListener('click', (ev) => {
        if (ev.target.matches('[data-close-drawer]') || ev.target.closest('[data-close-drawer]')) {
            commitSettingsFromDOM();
            closeDrawer();
        } else if (ev.target.closest('#toggle-theme')) {
            toggleTheme();
        } else if (ev.target.closest('#toggle-lang')) {
            toggleLang();
        } else if (ev.target.closest('#reset-all-btn')) {
            resetAll();
        } else {
            const promptBtn = ev.target.closest('[data-open-prompt]');
            if (promptBtn) openPromptModal(promptBtn.dataset.openPrompt);
        }
    });
    document.getElementById('model-select').addEventListener('change', (ev) => {
        state.settings.model = ev.target.value;
        saveSettings();
        refreshApiKeyStatus();
    });

    // Modal perfil del usuario
    document.getElementById('profile-modal').addEventListener('click', (ev) => {
        if (ev.target.matches('[data-close-profile]') || ev.target.closest('[data-close-profile]')
            || ev.target.closest('#profile-cancel')) {
            cancelProfileModal();
        } else if (ev.target.closest('#profile-save')) {
            saveProfileModal();
        }
    });

    // Modal editor de system prompt
    document.getElementById('prompt-modal').addEventListener('click', (ev) => {
        if (ev.target.matches('[data-close-prompt-modal]') || ev.target.closest('[data-close-prompt-modal]')
            || ev.target.closest('#prompt-modal-cancel')) {
            cancelPromptModal();
        } else if (ev.target.closest('#prompt-modal-save')) {
            savePromptModal();
        } else if (ev.target.id === 'prompt-modal-restore') {
            restorePromptDefault();
        }
    });

    // Composers (/chat y /agent)
    for (const mode of ['chat', 'agent']) {
        const ui = CONV_UI[mode];
        const input = document.getElementById(ui.inputId);
        input.addEventListener('input', () => autoresizeTextarea(input));
        input.addEventListener('keydown', (ev) => {
            if (ev.key === 'Enter' && !ev.shiftKey) {
                ev.preventDefault();
                convSend();
            }
        });
    }
    document.getElementById('send-btn').addEventListener('click', () => convSend());
    document.getElementById('agent-send-btn').addEventListener('click', () => convSend());

    // Click handlers compartidos de los mensajes (/chat y /agent)
    const handleConvClick = (ev) => {
        const saveBtn = ev.target.closest('[data-save-run]');
        if (saveBtn && !saveBtn.disabled) {
            saveRunFromChat(parseInt(saveBtn.dataset.saveRun, 10));
            return;
        }
        const exampleBtn = ev.target.closest('[data-example]');
        if (exampleBtn) {
            const ta = document.getElementById(CONV_UI[convMode()].inputId);
            ta.value = exampleBtn.dataset.example;
            autoresizeTextarea(ta);
            ta.focus();
            return;
        }
        // Preguntas del agente: toggle de opciones + responder
        const opcionBtn = ev.target.closest('.opcion-btn');
        if (opcionBtn && !opcionBtn.disabled) {
            const block = opcionBtn.closest('.pregunta-block');
            if (block.dataset.multiple !== '1') {
                block.querySelectorAll('.opcion-btn.selected').forEach(b => {
                    if (b !== opcionBtn) b.classList.remove('selected');
                });
            }
            opcionBtn.classList.toggle('selected');
            const card = opcionBtn.closest('.preguntas-card');
            const responder = card.querySelector('[data-responder]');
            if (responder) {
                const completo = Array.from(card.querySelectorAll('.pregunta-block'))
                    .every(b => b.querySelector('.opcion-btn.selected'));
                responder.disabled = !completo;
            }
            return;
        }
        const responderBtn = ev.target.closest('[data-responder]');
        if (responderBtn && !responderBtn.disabled) {
            const card = responderBtn.closest('.preguntas-card');
            const lines = Array.from(card.querySelectorAll('.pregunta-block')).map(b => {
                const pregunta = b.querySelector('.pregunta-texto').textContent;
                const elegidas = Array.from(b.querySelectorAll('.opcion-btn.selected'))
                    .map(x => x.dataset.opcion);
                return `${pregunta} ${elegidas.join(', ')}`;
            });
            convSend(lines.join('\n'));
        }
    };
    document.getElementById('chat-messages').addEventListener('click', handleConvClick);
    document.getElementById('agent-messages').addEventListener('click', handleConvClick);

    // Home (/)
    document.getElementById('btn-new-routine').addEventListener('click', openOneshotModal);
    document.getElementById('routines-grid').addEventListener('click', (ev) => {
        const delBtn = ev.target.closest('[data-delete-routine]');
        if (delBtn) {
            ev.stopPropagation();
            deleteRoutine(parseInt(delBtn.dataset.deleteRoutine, 10));
            return;
        }
        const card = ev.target.closest('[data-open-routine]');
        if (card) openRoutineModal(parseInt(card.dataset.openRoutine, 10));
    });
    document.getElementById('filter-goal').addEventListener('input', (ev) => {
        state.routinesFilter.goal = ev.target.value;
        renderHome();
    });
    document.getElementById('filter-format').addEventListener('change', (ev) => {
        state.routinesFilter.format = ev.target.value;
        renderHome();
    });

    // Oneshot modal
    document.getElementById('oneshot-modal').addEventListener('click', (ev) => {
        if (ev.target.matches('[data-close-oneshot]') || ev.target.closest('[data-close-oneshot]')) {
            closeOneshotModal();
            return;
        }
        if (ev.target.closest('#oneshot-generate-btn')) { runOneshotGenerate(); return; }
        if (ev.target.closest('#oneshot-save-btn')) { saveOneshotRoutine(); return; }
        if (ev.target.closest('#oneshot-discard-btn')) { closeOneshotModal(); return; }
        if (ev.target.closest('#oneshot-regenerate-btn')) {
            document.getElementById('oneshot-input-block').hidden = false;
            document.getElementById('oneshot-result-block').hidden = true;
            document.getElementById('oneshot-input').focus();
            return;
        }
    });
    document.getElementById('oneshot-input').addEventListener('keydown', (ev) => {
        if (ev.key === 'Enter' && (ev.metaKey || ev.ctrlKey)) {
            ev.preventDefault();
            runOneshotGenerate();
        }
    });

    // About modal
    document.getElementById('open-about').addEventListener('click', openAboutModal);
    document.getElementById('about-modal').addEventListener('click', (ev) => {
        if (ev.target.matches('[data-close-about]') || ev.target.closest('[data-close-about]')) {
            closeAboutModal();
        }
    });

    // Historial
    document.getElementById('status-pills').addEventListener('click', (ev) => {
        const btn = ev.target.closest('.pill-btn');
        if (!btn) return;
        document.querySelectorAll('#status-pills .pill-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.runsFilter.status = btn.dataset.status;
        renderHistorial();
    });
    document.getElementById('runs-list').addEventListener('click', (ev) => {
        const card = ev.target.closest('[data-open-run]');
        if (card) openRunModal(parseInt(card.dataset.openRun, 10));
    });

    // Modal genérico
    document.getElementById('modal').addEventListener('click', (ev) => {
        if (ev.target.matches('[data-close-modal]') || ev.target.closest('[data-close-modal]')) {
            closeModal();
            return;
        }
        const tab = ev.target.closest('.run-tab');
        if (tab) {
            const modalBody = document.getElementById('modal-body');
            modalBody.querySelectorAll('.run-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            modalBody.querySelectorAll('[data-pane]').forEach(p => {
                p.hidden = p.dataset.pane !== tab.dataset.tab;
            });
        }
    });

    // Escape
    document.addEventListener('keydown', (ev) => {
        if (ev.key === 'Escape') {
            if (!document.getElementById('prompt-modal').hidden) cancelPromptModal();
            else if (!document.getElementById('profile-modal').hidden) cancelProfileModal();
            else if (!document.getElementById('about-modal').hidden) closeAboutModal();
            else if (!document.getElementById('oneshot-modal').hidden) closeOneshotModal();
            else if (!document.getElementById('modal').hidden) closeModal();
            else if (state.drawerOpen) { commitSettingsFromDOM(); closeDrawer(); }
        }
    });
}

// -------------------- Init --------------------
async function init() {
    applyTheme();
    replaceIcons(document);
    applySidebarCollapse();

    try {
        state.config = await api.getConfig();
        const saved = loadSettings();
        const defaultPrompts = await api.getSystemPrompts();   // {mode: {es, en}}
        const availableIds = (state.config.available_models || []).map(m => m.id);
        const langs = state.config.langs || ['es', 'en'];

        state.settings.model = saved && availableIds.includes(saved.model)
            ? saved.model
            : state.config.default_model;
        state.settings.lang = saved && langs.includes(saved.lang)
            ? saved.lang
            : (state.config.default_lang || 'es');
        // Prompts guardados por idioma y modo; lo que falte cae al default del server.
        // Nota: los prompts editados con el contrato anterior (settings viejos
        // systemPromptOneshot/Chat/Agent, claves JSON en español) NO se migran:
        // instruirían al modelo a responder con el contrato viejo y todo caería
        // en schema_error. Se parte de los defaults nuevos.
        for (const lang of ['es', 'en']) {
            for (const mode of PROMPT_MODES) {
                state.settings.prompts[lang][mode] =
                    saved?.prompts?.[lang]?.[mode] || defaultPrompts[mode]?.[lang] || '';
            }
        }
        saveSettings();
    } catch (e) {
        document.body.innerHTML = `<div style="padding:32px;font-family:'Helvetica Neue',sans-serif;"><h2>Error al cargar la app</h2><p>${escapeHtml(e.message)}</p></div>`;
        return;
    }

    applyI18n();
    applyLangLabel();
    applyTheme();   // el label del tema depende del idioma cargado
    bindEvents();
    router.init();
    await reloadChats();
    router.handleRoute();
}

document.addEventListener('DOMContentLoaded', init);
