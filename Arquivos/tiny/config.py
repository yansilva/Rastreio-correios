"""Configurações da integração com o Tiny ERP."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Carrega variáveis de ambiente procurando na raiz do projeto e em Arquivos/
_raiz_projeto = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_pasta_arquivos = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_raiz_projeto, ".env"))
load_dotenv(os.path.join(_pasta_arquivos, ".env"))


@dataclass
class TinyConfig:
    """Configurações e parâmetros para conexão à API do Tiny ERP."""
    token: str = ""
    url_pesquisa: str = "https://api.tiny.com.br/api2/pedidos.pesquisa.php"
    url_obter: str = "https://api.tiny.com.br/api2/pedido.obter.php"
    formato: str = "json"
    timeout_segundos: float = 30.0
    delay_paginacao_segundos: float = 0.5
    dias_atras_padrao: int = 30

    def __post_init__(self):
        if not self.token:
            self.token = os.getenv("TOKEN_TINY", "").strip()

    def __repr__(self) -> str:
        # Mascara o token para evitar vazamento acidental em logs e depuração
        token_mascarado = f"{self.token[:4]}...{self.token[-4:]}" if len(self.token) >= 8 else "***"
        return (
            f"TinyConfig(token='{token_mascarado}', "
            f"url_pesquisa='{self.url_pesquisa}', "
            f"timeout={self.timeout_segundos}s)"
        )
