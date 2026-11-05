"""Validação de segurança de caminhos e proteção contra Path Traversal."""
import ipaddress
import re
import urllib.parse
from pathlib import Path

# Formato aceito do cabeçalho Host: nome ou IP (ou [IPv6]) com porta opcional, nada mais.
_FORMATO_HOST = re.compile(r"(?:\[[0-9A-Fa-f:.]+\]|[A-Za-z0-9.\-]+)(?::\d{1,5})?")

# Redes que podem falar com o servidor: esta máquina e a rede privada de casa (Wi-Fi).
REDES_LOCAIS = (
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
)

# Lista de permissão da raiz: só as páginas HTML e este script, que as páginas carregam.
ARQUIVOS_RAIZ_PERMITIDOS = {"alert_frete.js"}

# Única pasta do projeto servida além da raiz (CSS, JS e fontes do painel).
PASTA_PUBLICA = "web"

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
    allowed_extensions: set[str] | None = None,
) -> Path | None:
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

    # Remove query string e fragmento e decodifica uma única vez
    parsed = urllib.parse.urlsplit(requested_url_path)
    clean_path = urllib.parse.unquote(parsed.path).strip()
    return _resolver_caminho_decodificado(base_dir, clean_path, allowed_extensions)


def _resolver_caminho_decodificado(
    base_dir: Path,
    clean_path: str,
    allowed_extensions: set[str] | None,
) -> Path | None:
    """Valida um caminho já decodificado (sem nova decodificação) e devolve o Path ou None."""
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


def resolve_public_path(
    base_dir: Path,
    requested_url_path: str,
    allowed_extensions: set[str],
) -> Path | None:
    """Resolve um caminho de URL só se ele estiver na lista de permissão do painel.

    Liberado: páginas HTML da raiz, ARQUIVOS_RAIZ_PERMITIDOS e tudo dentro de web/.
    Todo o resto (Arquivos/, tests/, .env, .git, caches JSON etc.) devolve None.
    """
    if not requested_url_path:
        return None

    # Decodificação única: a validação abaixo e a resolução usam o mesmo texto.
    clean_path = urllib.parse.unquote(urllib.parse.urlsplit(requested_url_path).path)
    clean_path = clean_path.replace("\\", "/").lstrip("/")
    if not clean_path:
        return None

    segmentos = clean_path.split("/")
    if len(segmentos) == 1:
        nome = segmentos[0]
        raiz_permitida = nome in ARQUIVOS_RAIZ_PERMITIDOS or nome.lower().endswith(".html")
        if not raiz_permitida:
            return None
    elif segmentos[0] != PASTA_PUBLICA:
        return None

    # Validação final: contenção em base_dir, nomes bloqueados, extensões e existência.
    return _resolver_caminho_decodificado(base_dir, "/" + clean_path, allowed_extensions)


def ip_na_rede_local(endereco: str) -> bool:
    """Diz se o IP do cliente é loopback ou de rede privada (10/8, 172.16/12, 192.168/16)."""
    try:
        ip = ipaddress.ip_address(endereco.split("%")[0])
    except (ValueError, AttributeError):
        return False
    if ip.version == 6 and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return any(ip in rede for rede in REDES_LOCAIS)


def origem_confiavel(host: str, origin: str | None, referer: str | None) -> bool:
    """Confere se Origin (ou Referer) aponta para o próprio host do servidor.

    Navegadores enviam Origin em todo POST de outro site, então um site externo
    aberto no celular não consegue disparar /atualizar nem /regerar.
    Sem Origin nem Referer (cliente não navegador), a checagem de IP ainda vale.
    """
    host = (host or "").strip().lower()
    if origin is not None:
        return urllib.parse.urlsplit(origin).netloc.lower() == host
    if referer is not None:
        return urllib.parse.urlsplit(referer).netloc.lower() == host
    return True


def host_permitido(host: str | None, porta: int | None, ip_servidor: str | None = None) -> bool:
    """Confere se o cabeçalho Host aponta para este servidor (anti DNS rebinding).

    Aceita localhost, 127.0.0.1, ::1, qualquer IP privado/loopback (10/8, 172.16/12,
    192.168/16) e o IP configurado do servidor. Com ou sem porta; se houver porta,
    ela tem de ser a porta do servidor. Qualquer nome de domínio é recusado, mesmo
    que o DNS o aponte para 127.0.0.1.
    """
    if not host:
        return False
    host = host.strip()
    # Formato estrito antes de qualquer parsing: sem @, /, ?, # nem espaços.
    if not _FORMATO_HOST.fullmatch(host):
        return False
    try:
        partes = urllib.parse.urlsplit("//" + host)
        nome = (partes.hostname or "").lower()
        porta_host = partes.port
    except ValueError:
        return False
    if not nome:
        return False
    if porta_host is not None and porta is not None and porta_host != porta:
        return False
    if nome in ("localhost", "127.0.0.1", "::1"):
        return True
    if ip_na_rede_local(nome):
        return True
    if ip_servidor and ip_servidor not in ("0.0.0.0", "::") and nome == ip_servidor.lower():
        return True
    return False
