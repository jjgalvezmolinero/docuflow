from pydantic import BaseModel, Field
from typing import Optional
from enum import StrEnum
from datetime import datetime
import uuid


class AIProvider(StrEnum):
    claude = "claude"
    gemini = "gemini"
    groq = "groq"
    ollama = "ollama"
    claude_code = "claude_code"


class TemplateType(StrEnum):
    docx = "docx"
    odt = "odt"


class SectionStatus(StrEnum):
    pending = "pending"
    generated = "generated"
    approved = "approved"


class Template(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    filename: str
    type: TemplateType
    sections: list[str] = []  # títulos extraídos de la plantilla
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    path: str                          # ruta al proyecto en el host
    template_id: Optional[str] = None
    ai_provider: AIProvider = AIProvider.claude
    ai_model: str = "claude-sonnet-4-5"
    description: Optional[str] = None  # descripcion extra para el AI
    extensions: list[str] = ["php", "js", "ts", "json"]  # extensiones a leer
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class Section(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str = ""
    status: SectionStatus = SectionStatus.pending
    order: int = 0


class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    template_id: str
    sections: list[Section] = []
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
