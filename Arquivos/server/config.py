"""Configurações do servidor web local do painel de rastreio."""
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ServerConfig:
    """Configuração centralizada do servidor HTTP."""

    host: str = "127.0.0.1"
    port: int = 8000
    base_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    html_file: str = "relatorio_rastreio.html"
    cooldown_seconds: int = 150  # 2.5 minutos
    auto_update_interval: int = 2700  # 45 minutos em segundos
    allowed_extensions: set[str] = field(
        default_factory=lambda: {
            ".html",
            ".htm",
            ".css",
            ".js",
            ".json",
            ".png",
            ".jpg",
            ".jpeg",
            ".svg",
            ".ico",
            ".webp",
        }
    )

    @classmethod
    def from_env(cls, base_dir: Path | None = None) -> "ServerConfig":
        """Cria configuração lendo variáveis de ambiente se disponíveis."""
        host = os.environ.get("SERVER_HOST", "127.0.0.1").strip()

        porta_str = os.environ.get("SERVER_PORT", "8000").strip()
        try:
            port = int(porta_str)
        except ValueError:
            port = 8000

        resolved_base = base_dir or Path(__file__).resolve().parent.parent.parent
        return cls(host=host, port=port, base_dir=resolved_base)

    @property
    def url(self) -> str:
        """URL base de acesso ao servidor."""
        display_host = "localhost" if self.host in ("127.0.0.1", "0.0.0.0", "") else self.host
        return f"http://{display_host}:{self.port}"
