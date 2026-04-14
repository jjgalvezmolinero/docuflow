import json
import os
from models import Template, Project, Document, Section

DATA_DIR = os.environ.get("DATA_DIR", "../data")
DB_PATH = os.path.join(DATA_DIR, "db.json")


def _load() -> dict:
    if not os.path.exists(DB_PATH):
        return {"templates": [], "projects": [], "documents": [], "settings": {}}
    with open(DB_PATH) as f:
        return json.load(f)


def _save(data: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# --- Templates ---

def get_templates() -> list[Template]:
    return [Template(**t) for t in _load()["templates"]]


def get_template(template_id: str) -> Template | None:
    for t in _load()["templates"]:
        if t["id"] == template_id:
            return Template(**t)
    return None


def save_template(template: Template):
    data = _load()
    data["templates"] = [t for t in data["templates"] if t["id"] != template.id]
    data["templates"].append(template.model_dump())
    _save(data)


def delete_template(template_id: str):
    data = _load()
    data["templates"] = [t for t in data["templates"] if t["id"] != template_id]
    _save(data)


# --- Projects ---

def get_projects() -> list[Project]:
    return [Project(**p) for p in _load()["projects"]]


def get_project(project_id: str) -> Project | None:
    for p in _load()["projects"]:
        if p["id"] == project_id:
            return Project(**p)
    return None


def save_project(project: Project):
    data = _load()
    data["projects"] = [p for p in data["projects"] if p["id"] != project.id]
    data["projects"].append(project.model_dump())
    _save(data)


def delete_project(project_id: str):
    data = _load()
    data["projects"] = [p for p in data["projects"] if p["id"] != project_id]
    # eliminar documento asociado
    data["documents"] = [d for d in data["documents"] if d["project_id"] != project_id]
    _save(data)


# --- Documents ---

def get_document(project_id: str) -> Document | None:
    for d in _load()["documents"]:
        if d["project_id"] == project_id:
            return Document(**d)
    return None


def save_document(document: Document):
    data = _load()
    data["documents"] = [d for d in data["documents"] if d["project_id"] != document.project_id]
    data["documents"].append(document.model_dump())
    _save(data)


def delete_document(project_id: str):
    data = _load()
    data["documents"] = [d for d in data["documents"] if d["project_id"] != project_id]
    _save(data)


# --- Settings ---

def get_settings() -> dict:
    return _load().get("settings", {})


def save_settings(settings: dict):
    data = _load()
    data["settings"] = settings
    _save(data)
