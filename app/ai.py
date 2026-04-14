import anthropic
import google.generativeai as genai
from groq import Groq
import httpx
import subprocess
import tempfile
import os
from models import AIProvider

CLAUDE_MODELS = [
    "claude-sonnet-4-5",
    "claude-opus-4-5",
    "claude-haiku-4-5-20251001",
]

GEMINI_MODELS = [
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-2.0-flash",
]

GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]

CLAUDE_CODE_MODELS = [
    "claude-sonnet-4-5",
    "claude-opus-4-5",
    "claude-haiku-4-5-20251001",
]

OLLAMA_MODELS = [
    "llama3.1",
    "llama3.2",
    "mistral",
    "codellama",
    "phi3",
    "qwen2.5-coder:1.5b",
    "qwen2.5-coder:7b",
    "qwen2.5-coder:14b",
    "qwen2.5-coder:32b",
]


def _build_prompt(section_title: str, context: str, project_description: str) -> str:
    extra = f"\nDescripción adicional del proyecto: {project_description}" if project_description else ""
    return f"""Eres un experto técnico redactando documentación profesional en español.

Se te proporciona el código fuente completo de un proyecto PHP/JavaScript.{extra}

Tu tarea es redactar el contenido para la sección titulada: **{section_title}**

Instrucciones:
- Escribe en español técnico, claro y profesional
- No incluyas el título de la sección, solo el contenido
- No uses markdown (sin asteriscos, sin #, sin backticks)
- Usa párrafos bien estructurados
- Si la sección requiere una lista, usa guiones simples (-)
- Basa el contenido exclusivamente en el código analizado
- Sé preciso y conciso

Código fuente del proyecto:
{context}

Redacta ahora el contenido para la sección "{section_title}":"""


async def generate_section_claude(
    api_key: str, model: str, section_title: str, context: str, project_description: str = ""
) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    prompt = _build_prompt(section_title, context, project_description)
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


async def generate_section_gemini(
    api_key: str, model: str, section_title: str, context: str, project_description: str = ""
) -> str:
    genai.configure(api_key=api_key)
    gemini_model = genai.GenerativeModel(model)
    prompt = _build_prompt(section_title, context, project_description)
    response = gemini_model.generate_content(prompt)
    return response.text


async def generate_section_groq(
    api_key: str, model: str, section_title: str, context: str, project_description: str = ""
) -> str:
    client = Groq(api_key=api_key)
    prompt = _build_prompt(section_title, context, project_description)
    # Groq free tier: dejar margen amplio para no superar los 12.000 TPM
    max_tokens = 1_500
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


async def generate_section_ollama(
    base_url: str, model: str, section_title: str, context: str, project_description: str = ""
) -> str:
    prompt = _build_prompt(section_title, context, project_description)
    url = base_url.rstrip("/") + "/api/generate"
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, json={
            "model": model,
            "prompt": prompt,
            "stream": False,
        })
        response.raise_for_status()
        return response.json()["response"]


async def generate_section_claude_code(
    model: str, section_title: str, context: str, project_description: str = ""
) -> str:
    prompt = _build_prompt(section_title, context, project_description)
    claude_bin = "/home/jjgalvez/.local/share/claude/versions/2.1.97"

    result = subprocess.run(
        [claude_bin, "-p", "--model", model],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=300,
        env={**os.environ, "HOME": "/home/jjgalvez"},
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "Error al ejecutar claude CLI")
    return result.stdout.strip()


async def generate_section(
    provider: AIProvider,
    api_key: str,
    model: str,
    section_title: str,
    context: str,
    project_description: str = "",
    ollama_url: str = "http://localhost:11434",
) -> str:
    if provider == AIProvider.claude:
        return await generate_section_claude(api_key, model, section_title, context, project_description)
    elif provider == AIProvider.gemini:
        return await generate_section_gemini(api_key, model, section_title, context, project_description)
    elif provider == AIProvider.groq:
        return await generate_section_groq(api_key, model, section_title, context, project_description)
    elif provider == AIProvider.ollama:
        return await generate_section_ollama(ollama_url, model, section_title, context, project_description)
    elif provider == AIProvider.claude_code:
        return await generate_section_claude_code(model, section_title, context, project_description)
    raise ValueError(f"Proveedor desconocido: {provider}")
