<div align="center">

# DocuFlow

**Automatic technical documentation generator for software projects using AI.**

Upload a template, point to your codebase, and let the model fill in every section.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-required-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![HTMX](https://img.shields.io/badge/HTMX-2.0-3D72D7?style=flat-square)](https://htmx.org)
[![Vibe Coded](https://img.shields.io/badge/vibe%20coded-Claude%20Sonnet-blueviolet?style=flat-square)](https://anthropic.com)
[![License](https://img.shields.io/badge/license-AGPL--3.0-green?style=flat-square)](LICENSE)

</div>

---

> **Vibe coding disclosure** — This project was built with [Claude Code](https://claude.ai/code) (Anthropic) using a vibe coding approach: the architecture, features and code were developed through a conversational flow with an AI assistant. The codebase is fully readable and maintained by humans, but I want to be transparent about how it was created.

---

## What is this?

DocuFlow is a web application that reads your project's source code and generates technical documentation automatically using AI. You define the structure through a template file (`.docx` or `.odt`) with section markers, and DocuFlow fills in each section by analyzing the codebase.

It supports multiple AI providers — cloud or local — so you can choose the model that best fits your needs or privacy requirements.

---

## Features

| Category | Feature |
|---|---|
| **Templates** | Upload `.docx` or `.odt` files with section markers — DocuFlow detects them automatically |
| **AI providers** | Claude (Anthropic), Gemini (Google), Groq, Ollama (local), Claude Code CLI |
| **Generation** | Generate sections one by one or all at once with a single click |
| **Inline editor** | Review and edit generated content before exporting |
| **Export** | Download the final document as `.docx`, `.odt` or `.pdf` |
| **Local projects** | The container mounts the host `/home` directory to point at any project without copying files |

---

## Tech stack

```
Backend    →  Python 3.12 + FastAPI + Uvicorn
Frontend   →  HTMX 2.0 + Jinja2 + Tailwind CSS
AI         →  Anthropic SDK, google-generativeai, Groq, Ollama
Documents  →  python-docx, odfpy
Data       →  JSON (data/db.json)
```

---

## Requirements

- **Docker** with the Compose v2 plugin
- An API key for the AI provider you want to use (Claude, Gemini or Groq), or Ollama running locally

---

## Quick start

```bash
# 1. Clone this repository
git clone https://github.com/jjgalvezmolinero/docuflow.git
cd docuflow

# 2. Start the app
docker compose up -d --build

# 3. Open in the browser
open http://localhost:9100
```

Then go to **Settings** and add the API keys for the providers you want to use.

---

## Basic usage

1. Go to **Templates** and upload a `.docx` or `.odt` file with the sections you want to document.
2. Create a **Project** with the path to your source code, and select a template and AI provider.
3. Click **Analyze** to read the project and prepare the sections.
4. Generate content section by section or use **Generate all**.
5. Review, edit if needed, and **Export** the final document.

---

## How it works

```
┌─────────────────────────────────────────┐
│               DocuFlow                  │
│           (Docker container)            │
│                                         │
│  FastAPI ──► reader.py ──► codebase     │
│      │                                  │
│      └──► ai.py ──► AI provider         │
│               │                         │
│               └──► exporter.py ──► file │
└─────────────────────────────────────────┘
```

The container mounts `/home` from the host, so DocuFlow can read any local project directly by its path — no file copying needed.

---

## Project structure

```
docuflow/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── data/                   # Data volume (gitignored)
│   └── db.json             # Projects, templates and settings
└── app/
    ├── main.py             # FastAPI routes
    ├── ai.py               # AI provider integrations
    ├── reader.py           # Project reading and context building
    ├── template_parser.py  # Section extraction from templates
    ├── exporter.py         # docx / odt / pdf export
    ├── store.py            # JSON persistence
    ├── models.py           # Pydantic models
    └── templates/          # Jinja2 HTML templates
```

---

## Data and persistence

All data (database, uploaded templates, generated outputs) is stored in the `data/` directory on the host, mounted as a volume at `/data` inside the container.

`data/db.json` is excluded from the repository via `.gitignore`.

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATA_DIR` | `/data` | Directory where `db.json` and uploads are persisted |

---

## Roadmap

- [ ] **Version history** — Keep previous generations per section
- [ ] **Diff view** — Compare AI output against previous version before accepting
- [ ] **Custom prompts per section** — Override the default prompt for specific sections
- [ ] **Git integration** — Auto-detect project language and structure from the repo
- [ ] **Team sharing** — Share projects and templates across users

---

## License

AGPL-3.0 — see [LICENSE](LICENSE) for details.
