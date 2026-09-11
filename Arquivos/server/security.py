"""Validação de segurança de caminhos e proteção contra Path Traversal."""
import os
from pathlib import Path
from typing import Optional, Set
import urllib.parse

# Nomes de arquivos e diretórios expressamente bloqueados
BLOCKED_NAMES = {
    ".env",
    ".env.example",
    ".gitignore",
    ".git",
    "venv",
    ".pytest_cache",
    "__pycache__",
    "tests",
}

BLOCKED_EXTENSIONS = {
    ".py",
    ".pyc",
    ".pyo",
    ".pyd",
    ".bat",
    ".sh",
    ".ps1",
    ".cmd",
    ".exe",
}


def resolve_safe_path(
    base_dir: Path,
    requested_url_path: str,
    allowed_extensions: Optional[Set[str]] = None,
) -> Optional[Path]:
    """Valida e resolve com segurança um caminho requisitado via URL.

    Retorna o Path absoluto se for seguro e pertencer a base_dir, ou None caso contrário.
    Protege contra:
    - Path Traversal (../ ou ..\\)
    - Acesso a arquivos ocultos ou sensíveis (.env, .git, etc.)
    - Acesso a scripts executáveis ou código-fonte (.py, .bat, etc.)
    - Arquivos fora do diretório base
    """
    if not requested_url_path:
        return None

    # Remove query string e fragmento
    parsed = urllib.parse.urlsplit(requested_url_path)
    clean_path = urllib.parse.unquote(parsed.path).strip()

    # Normaliza barras e remove barras iniciais
    clean_path = clean_path.replace("\\", "/").lstrip("/")
    if not clean_path:
        return None

    # Rejeita explicitamente se houver '..' em qualquer segmento
    segments = clean_path.split("/")
    for segment in segments:
        if segment in ("..", ".", ""):
            if segment == "..":
                return None
            continue
        # Rejeita nomes bloqueados
        if segment.lower() in BLOCKED_NAMES or segment.startswith("."):
            return None

    try:
        base_resolved = base_dir.resolve()
        candidate = (base_resolved / clean_path).resolve()
    except (ValueError, RuntimeError, OSError):
        return None

    # Verifica se o candidato está estritamente contido em base_dir
    try:
        candidate.relative_to(base_resolved)
    except ValueError:
        # Está fora de base_dir
        return None

    # Bloqueia extensões proibidas
    ext = candidate.suffix.lower()
    if ext in BLOCKED_EXTENSIONS:
        return None

    # Se uma whitelist de extensões for exigida, valida
    if allowed_extensions is not None and ext not in allowed_extensions:
        return None

    # Verifica se o arquivo existe e é arquivo regular
    if not candidate.is_file():
        return None

    return candidate
