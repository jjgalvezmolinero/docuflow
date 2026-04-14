import os
import uuid
import asyncio
import traceback
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)

from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import store
import reader
import template_parser
import exporter
import ai as ai_module
from models import (
    Template, TemplateType, Project, AIProvider,
    Document, Section, SectionStatus,
)

app = FastAPI(title="DocuFlow")
templates = Jinja2Templates(directory="templates")

DATA_DIR = os.environ.get("DATA_DIR", "../data")


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    projects = store.get_projects()
    tmpl_list = store.get_templates()
    tmpl_map = {t.id: t for t in tmpl_list}
    return templates.TemplateResponse("index.html", {
        "request": request,
        "projects": projects,
        "tmpl_map": tmpl_map,
    })


# ---------------------------------------------------------------------------
# Plantillas
# ---------------------------------------------------------------------------

@app.get("/templates", response_class=HTMLResponse)
async def templates_page(request: Request):
    tmpl_list = store.get_templates()
    return templates.TemplateResponse("templates.html", {
        "request": request,
        "templates": tmpl_list,
    })


@app.post("/templates/upload")
async def upload_template(
    request: Request,
    name: str = Form(...),
    file: UploadFile = File(...),
):
    content = await file.read()
    filename = file.filename or "template"
    ext = Path(filename).suffix.lstrip(".").lower()

    if ext not in ("docx", "odt"):
        return JSONResponse({"ok": False, "error": "Solo se admiten ficheros .docx y .odt"}, status_code=400)

    # Nombre único para el fichero
    unique_filename = f"{uuid.uuid4()}.{ext}"
    template_parser.save_template_file(unique_filename, content)

    # Extraer secciones
    sections = template_parser.extract_sections(unique_filename, ext)

    tmpl = Template(
        name=name,
        filename=unique_filename,
        type=TemplateType(ext),
        sections=sections,
    )
    store.save_template(tmpl)

    return JSONResponse({"ok": True, "id": tmpl.id, "sections": sections})


@app.post("/templates/{template_id}/delete")
async def delete_template(template_id: str):
    tmpl = store.get_template(template_id)
    if not tmpl:
        raise HTTPException(404)
    template_parser.delete_template_file(tmpl.filename)
    store.delete_template(template_id)
    return JSONResponse({"ok": True})


# ---------------------------------------------------------------------------
# Proyectos
# ---------------------------------------------------------------------------

@app.get("/projects/new", response_class=HTMLResponse)
async def project_new(request: Request):
    tmpl_list = store.get_templates()
    return templates.TemplateResponse("project_form.html", {
        "request": request,
        "templates": tmpl_list,
        "project": None,
        "ai_providers": list(AIProvider),
        "claude_models": ai_module.CLAUDE_MODELS,
        "gemini_models": ai_module.GEMINI_MODELS,
        "groq_models": ai_module.GROQ_MODELS,
        "ollama_models": ai_module.OLLAMA_MODELS,
        "claude_code_models": ai_module.CLAUDE_CODE_MODELS,
    })


@app.post("/projects")
async def create_project(
    name: str = Form(...),
    path: str = Form(...),
    template_id: str = Form(""),
    ai_provider: str = Form("claude"),
    ai_model: str = Form("claude-sonnet-4-5"),
    description: str = Form(""),
    extensions: str = Form("php,js,ts,json"),
):
    exts = [e.strip().lstrip(".") for e in extensions.split(",") if e.strip()]
    project = Project(
        name=name,
        path=path,
        template_id=template_id or None,
        ai_provider=AIProvider(ai_provider),
        ai_model=ai_model,
        description=description or None,
        extensions=exts,
    )
    store.save_project(project)
    return RedirectResponse(f"/projects/{project.id}", status_code=303)


@app.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_detail(request: Request, project_id: str):
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(404)
    tmpl = store.get_template(project.template_id) if project.template_id else None
    document = store.get_document(project_id)
    settings = store.get_settings()
    return templates.TemplateResponse("project.html", {
        "request": request,
        "project": project,
        "template": tmpl,
        "document": document,
        "settings": settings,
    })


@app.get("/projects/{project_id}/edit", response_class=HTMLResponse)
async def project_edit(request: Request, project_id: str):
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(404)
    tmpl_list = store.get_templates()
    return templates.TemplateResponse("project_form.html", {
        "request": request,
        "project": project,
        "templates": tmpl_list,
        "ai_providers": list(AIProvider),
        "claude_models": ai_module.CLAUDE_MODELS,
        "gemini_models": ai_module.GEMINI_MODELS,
        "groq_models": ai_module.GROQ_MODELS,
        "ollama_models": ai_module.OLLAMA_MODELS,
        "claude_code_models": ai_module.CLAUDE_CODE_MODELS,
    })


@app.post("/projects/{project_id}/edit")
async def update_project(
    project_id: str,
    name: str = Form(...),
    path: str = Form(...),
    template_id: str = Form(""),
    ai_provider: str = Form("claude"),
    ai_model: str = Form("claude-sonnet-4-5"),
    description: str = Form(""),
    extensions: str = Form("php,js,ts,json"),
):
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(404)
    exts = [e.strip().lstrip(".") for e in extensions.split(",") if e.strip()]
    project.name = name
    project.path = path
    project.template_id = template_id or None
    project.ai_provider = AIProvider(ai_provider)
    project.ai_model = ai_model
    project.description = description or None
    project.extensions = exts
    project.updated_at = datetime.now().isoformat()
    store.save_project(project)
    return RedirectResponse(f"/projects/{project_id}", status_code=303)


@app.post("/projects/{project_id}/delete")
async def delete_project(project_id: str):
    store.delete_project(project_id)
    return JSONResponse({"ok": True})


# ---------------------------------------------------------------------------
# Análisis y generación
# ---------------------------------------------------------------------------

@app.post("/projects/{project_id}/analyze")
async def analyze_project(project_id: str):
    """Lee el proyecto y crea el documento con secciones vacías listas para generar."""
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(404)
    if not project.template_id:
        return JSONResponse({"ok": False, "error": "El proyecto no tiene plantilla asignada"}, status_code=400)

    tmpl = store.get_template(project.template_id)
    if not tmpl:
        return JSONResponse({"ok": False, "error": "Plantilla no encontrada"}, status_code=404)

    try:
        project_data = reader.read_project(project.path, project.extensions)
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)

    sections = [
        Section(title=title, order=i)
        for i, title in enumerate(tmpl.sections)
    ]

    document = Document(
        project_id=project_id,
        template_id=project.template_id,
        sections=sections,
    )
    store.save_document(document)

    return JSONResponse({
        "ok": True,
        "sections": len(sections),
        "files_read": project_data["summary"]["total_files"],
    })


@app.post("/projects/{project_id}/sections/{section_id}/generate")
async def generate_section(project_id: str, section_id: str):
    """Genera el contenido de una sección usando IA."""
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(404)

    document = store.get_document(project_id)
    if not document:
        return JSONResponse({"ok": False, "error": "Ejecuta el análisis primero"}, status_code=400)

    section = next((s for s in document.sections if s.id == section_id), None)
    if not section:
        raise HTTPException(404)

    settings = store.get_settings()
    api_key = settings.get(f"{project.ai_provider}_api_key", "")
    if not api_key and project.ai_provider not in ("ollama", "claude_code"):
        return JSONResponse({"ok": False, "error": f"Falta la API key de {project.ai_provider}"}, status_code=400)

    try:
        project_data = reader.read_project(project.path, project.extensions)
        context = reader.build_context(project_data, provider=project.ai_provider, model=project.ai_model)
        content = await ai_module.generate_section(
            provider=project.ai_provider,
            api_key=api_key,
            model=project.ai_model,
            section_title=section.title,
            context=context,
            project_description=project.description or "",
            ollama_url=settings.get("ollama_url", "http://localhost:11434"),
        )
        section.content = content
        section.status = SectionStatus.generated
        document.updated_at = datetime.now().isoformat()
        store.save_document(document)
        return JSONResponse({"ok": True, "content": content})
    except Exception as e:
        logging.error(traceback.format_exc())
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@app.post("/projects/{project_id}/sections/{section_id}/approve")
async def approve_section(project_id: str, section_id: str):
    document = store.get_document(project_id)
    if not document:
        raise HTTPException(404)
    section = next((s for s in document.sections if s.id == section_id), None)
    if not section:
        raise HTTPException(404)
    section.status = SectionStatus.approved
    document.updated_at = datetime.now().isoformat()
    store.save_document(document)
    return JSONResponse({"ok": True})


@app.post("/projects/{project_id}/sections/{section_id}/update")
async def update_section(project_id: str, section_id: str, content: str = Form(...)):
    document = store.get_document(project_id)
    if not document:
        raise HTTPException(404)
    section = next((s for s in document.sections if s.id == section_id), None)
    if not section:
        raise HTTPException(404)
    section.content = content
    if section.status == SectionStatus.pending:
        section.status = SectionStatus.generated
    document.updated_at = datetime.now().isoformat()
    store.save_document(document)
    return JSONResponse({"ok": True})


@app.post("/projects/{project_id}/sections/generate-all")
async def generate_all_sections(project_id: str):
    """Genera todas las secciones pendientes en secuencia."""
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(404)
    document = store.get_document(project_id)
    if not document:
        return JSONResponse({"ok": False, "error": "Ejecuta el análisis primero"}, status_code=400)

    settings = store.get_settings()
    api_key = settings.get(f"{project.ai_provider}_api_key", "")
    if not api_key and project.ai_provider not in ("ollama", "claude_code"):
        return JSONResponse({"ok": False, "error": f"Falta la API key de {project.ai_provider}"}, status_code=400)

    try:
        project_data = reader.read_project(project.path, project.extensions)
        context = reader.build_context(project_data)
        generated = 0
        for section in document.sections:
            if section.status == SectionStatus.pending:
                content = await ai_module.generate_section(
                    provider=project.ai_provider,
                    api_key=api_key,
                    model=project.ai_model,
                    section_title=section.title,
                    context=context,
                    project_description=project.description or "",
                    ollama_url=settings.get("ollama_url", "http://localhost:11434"),
                )
                section.content = content
                section.status = SectionStatus.generated
                generated += 1
        document.updated_at = datetime.now().isoformat()
        store.save_document(document)
        return JSONResponse({"ok": True, "generated": generated})
    except Exception as e:
        logging.error(traceback.format_exc())
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


# ---------------------------------------------------------------------------
# Exportación
# ---------------------------------------------------------------------------

@app.get("/projects/{project_id}/export/{fmt}")
async def export_document(project_id: str, fmt: str):
    if fmt not in ("docx", "odt", "pdf"):
        raise HTTPException(400, "Formato no soportado")

    project = store.get_project(project_id)
    if not project:
        raise HTTPException(404)
    document = store.get_document(project_id)
    if not document:
        return JSONResponse({"ok": False, "error": "No hay documento generado"}, status_code=400)
    tmpl = store.get_template(document.template_id)
    if not tmpl:
        return JSONResponse({"ok": False, "error": "Plantilla no encontrada"}, status_code=404)

    try:
        if fmt == "docx":
            path = exporter.export_docx(document, tmpl.filename, project.name)
        elif fmt == "odt":
            path = exporter.export_odt(document, tmpl.filename, project.name)
        else:
            path = exporter.export_pdf(document, tmpl.filename, project.name)

        media_types = {
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "odt": "application/vnd.oasis.opendocument.text",
            "pdf": "application/pdf",
        }
        return FileResponse(
            path,
            media_type=media_types[fmt],
            filename=f"{project.name}.{fmt}",
        )
    except Exception as e:
        logging.error(traceback.format_exc())
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


# ---------------------------------------------------------------------------
# Editor de sección (fragmento HTMX)
# ---------------------------------------------------------------------------

@app.get("/projects/{project_id}/sections/{section_id}/editor", response_class=HTMLResponse)
async def section_editor(request: Request, project_id: str, section_id: str):
    document = store.get_document(project_id)
    if not document:
        raise HTTPException(404)
    section = next((s for s in document.sections if s.id == section_id), None)
    if not section:
        raise HTTPException(404)
    project = store.get_project(project_id)
    return templates.TemplateResponse("fragments/section_editor.html", {
        "request": request,
        "section": section,
        "project": project,
    })


# ---------------------------------------------------------------------------
# Validación de ruta
# ---------------------------------------------------------------------------

@app.get("/check-path")
async def check_path(path: str):
    exists = os.path.isdir(path)
    return JSONResponse({"ok": exists})


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    settings = store.get_settings()
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "settings": settings,
        "claude_models": ai_module.CLAUDE_MODELS,
        "gemini_models": ai_module.GEMINI_MODELS,
    })


@app.post("/settings")
async def save_settings(
    claude_api_key: str = Form(""),
    gemini_api_key: str = Form(""),
    groq_api_key: str = Form(""),
    ollama_url: str = Form(""),
):
    settings = store.get_settings()
    if claude_api_key:
        settings["claude_api_key"] = claude_api_key
    if gemini_api_key:
        settings["gemini_api_key"] = gemini_api_key
    if groq_api_key:
        settings["groq_api_key"] = groq_api_key
    if ollama_url:
        settings["ollama_url"] = ollama_url
    store.save_settings(settings)
    return JSONResponse({"ok": True})


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}
