# DocuFlow

> **Proyecto construido con vibe coding usando [Claude Code](https://claude.ai/code).** El código no fue escrito manualmente — fue generado de forma iterativa mediante prompts conversacionales con IA.

DocuFlow es una aplicación web que genera documentación técnica de proyectos de software de forma automática usando IA. Sube una plantilla de documento, apunta al directorio de tu proyecto, y deja que el modelo rellene cada sección leyendo el código fuente.

---

## Funcionalidades

- **Plantillas personalizadas** — sube ficheros `.docx` o `.odt` con marcadores de sección; DocuFlow los detecta automáticamente.
- **Multiples proveedores de IA** — compatible con Claude (Anthropic), Gemini (Google), Groq, Ollama (local) y Claude Code CLI.
- **Generación por secciones** — genera sección a sección o todas de golpe con un solo clic.
- **Editor inline** — revisa y edita el contenido generado antes de exportar.
- **Exportación** — descarga el documento final en `.docx`, `.odt` o `.pdf`.
- **Montaje de proyectos locales** — el contenedor tiene acceso al `/home` del host para apuntar a cualquier proyecto sin copiar ficheros.

---

## Tecnologías

| Capa | Tecnología |
|------|-----------|
| Backend | FastAPI + Uvicorn |
| Frontend | Jinja2 + HTMX |
| IA | Anthropic SDK, google-generativeai, Groq, Ollama |
| Documentos | python-docx, odfpy |
| Contenedor | Docker + Docker Compose |

---

## Puesta en marcha

### Requisitos

- Docker y Docker Compose instalados.
- API key del proveedor de IA que vayas a usar (Claude, Gemini o Groq), o Ollama corriendo localmente.

### Arrancar

```bash
docker compose up -d
```

La aplicación queda disponible en `http://localhost:9100`.

### Configuración de API keys

Accede a **Settings** (`/settings`) desde la interfaz y añade las API keys de los proveedores que vayas a utilizar. No se guardan en variables de entorno ni en el repositorio.

---

## Datos y persistencia

Los datos (base de datos, plantillas, proyectos generados y outputs) se almacenan en el directorio `data/` del host, montado como volumen en `/data` dentro del contenedor.

El fichero `data/db.json` (base de datos JSON) está excluido del repositorio via `.gitignore`.

---

## Uso básico

1. Ve a **Templates** y sube un fichero `.docx` o `.odt` con las secciones que quieres documentar.
2. Crea un **Project** indicando la ruta local al código fuente y selecciona plantilla y proveedor de IA.
3. Pulsa **Analizar** para leer el proyecto y preparar las secciones.
4. Genera el contenido sección a sección o con **Generar todo**.
5. Revisa, edita si hace falta, y **Exporta** el documento final.

---

## Estructura del proyecto

```
docuflow/
├── app/
│   ├── main.py            # Rutas FastAPI
│   ├── ai.py              # Integración con proveedores de IA
│   ├── reader.py          # Lectura y contexto del proyecto
│   ├── template_parser.py # Extracción de secciones de plantillas
│   ├── exporter.py        # Exportación docx/odt/pdf
│   ├── store.py           # Persistencia JSON
│   └── models.py          # Modelos Pydantic
├── data/                  # Volumen de datos (ignorado en git)
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```
