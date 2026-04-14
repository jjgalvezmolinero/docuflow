import os
from pathlib import Path

# Directorios que nunca se leen
IGNORE_DIRS = {
    "node_modules", "vendor", ".git", "__pycache__", ".idea",
    "dist", "build", "coverage", ".next", "cache", "tmp", "temp",
}

# Ficheros que nunca se leen
IGNORE_FILES = {
    "package-lock.json", "yarn.lock", "composer.lock", ".DS_Store",
}

MAX_FILE_SIZE = 200 * 1024  # 200 KB por fichero


def read_project(path: str, extensions: list[str]) -> dict:
    """
    Lee un proyecto local y devuelve:
    - structure: árbol de directorios/ficheros
    - files: lista de {path, content}
    - summary: estadísticas básicas
    """
    root = Path(path)
    if not root.exists() or not root.is_dir():
        raise ValueError(f"La ruta no existe o no es un directorio: {path}")

    ext_set = {e.lstrip(".").lower() for e in extensions}
    files = []
    skipped = []

    for filepath in sorted(root.rglob("*")):
        # ignorar directorios bloqueados
        if any(part in IGNORE_DIRS for part in filepath.parts):
            continue
        if not filepath.is_file():
            continue
        if filepath.name in IGNORE_FILES:
            continue
        if filepath.suffix.lstrip(".").lower() not in ext_set:
            continue

        size = filepath.stat().st_size
        if size > MAX_FILE_SIZE:
            skipped.append(str(filepath.relative_to(root)))
            continue

        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
            files.append({
                "path": str(filepath.relative_to(root)),
                "content": content,
                "size": size,
            })
        except Exception:
            skipped.append(str(filepath.relative_to(root)))

    structure = _build_tree(root, ext_set)

    return {
        "root": str(root),
        "structure": structure,
        "files": files,
        "summary": {
            "total_files": len(files),
            "skipped_files": len(skipped),
            "total_chars": sum(len(f["content"]) for f in files),
        },
    }


# Límite de caracteres de contexto por proveedor/modelo (aprox. 1 token ≈ 4 chars)
# Se resta espacio para el prompt base y la respuesta
CONTEXT_LIMITS = {
    "claude":  400_000,
    "gemini":  400_000,
    "ollama":  120_000,
    # Groq free tier: máx 12.000 tokens/min totales (entrada + salida)
    # Reservamos ~2.500 tokens para respuesta + instrucciones → ~9.500 tokens entrada = ~28.000 chars
    "groq":    28_000,
}


def build_context(project_data: dict, provider: str = "claude", model: str = "") -> str:
    """
    Construye el bloque de contexto de código para mandarlo al AI.
    Trunca ficheros si el total supera el límite del proveedor/modelo.
    """
    key = f"{provider}:{model}" if model else provider
    max_chars = CONTEXT_LIMITS.get(key) or CONTEXT_LIMITS.get(provider, 20_000)
    # Reservar espacio para el prompt base (~2000 chars)
    max_code_chars = max_chars - 2_000

    structure = project_data["structure"]
    header = f"# Estructura del proyecto\n{structure}\n\n# Código fuente\n"
    available = max_code_chars - len(header)

    file_blocks = []
    used = 0
    truncated = 0

    for f in project_data["files"]:
        block = f"## {f['path']}\n```\n{f['content']}\n```\n"
        if used + len(block) > available:
            # Intentar incluir el fichero recortado
            remaining = available - used
            if remaining > 200:
                snippet = f['content'][:remaining - 150]
                block = f"## {f['path']}\n```\n{snippet}\n... [truncado]\n```\n"
                file_blocks.append(block)
                used += len(block)
            truncated += 1
            break
        file_blocks.append(block)
        used += len(block)

    context = header + "\n".join(file_blocks)
    if truncated:
        context += f"\n\n[Nota: {truncated} fichero(s) omitidos por límite de contexto del proveedor]"
    return context


def _build_tree(root: Path, ext_set: set, prefix: str = "") -> str:
    lines = []
    try:
        entries = sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name))
    except PermissionError:
        return ""

    for entry in entries:
        if entry.name in IGNORE_DIRS or entry.name.startswith("."):
            continue
        if entry.is_dir():
            lines.append(f"{prefix}📁 {entry.name}/")
            lines.append(_build_tree(entry, ext_set, prefix + "  "))
        elif entry.suffix.lstrip(".").lower() in ext_set:
            lines.append(f"{prefix}📄 {entry.name}")

    return "\n".join(lines)
