"""Configurações da integração com a API dos Correios."""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Carrega variáveis procurando na raiz do projeto e em Arquivos/
_raiz_projeto = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_pasta_arquivos = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_raiz_projeto, ".env"))
load_dotenv(os.path.join(_pasta_arquivos, ".env"))


@dataclass
class CorreiosConfig:
    """Parâmetros e configurações para autenticação e consulta às APIs dos Correios."""
    id_correios: str = ""
    contrato: str = ""
    codigo_acesso: str = ""
    url_token: str = "https://api.correios.com.br/token/v1/autentica/contrato"
    url_rastreio: str = "https://api.correios.com.br/srorastro/v1/objetos/{objeto}?resultado=T"
    timeout_segundos: float = 30.0
    dias_limite_atraso: int = 3

    def __post_init__(self):
        if not self.id_correios:
            self.id_correios = os.getenv("ID_CORREIOS", "").strip()
        if not self.contrato:
            self.contrato = os.getenv("CONTRATO", "").strip()
        if not self.codigo_acesso:
            self.codigo_acesso = os.getenv("CODIGO_ACESSO", "").strip()

    def credenciais_preenchidas(self) -> bool:
        """Verifica se todas as credenciais necessárias foram fornecidas."""
        return bool(self.id_correios and self.contrato and self.codigo_acesso)

    def __repr__(self) -> str:
        id_masc = f"{self.id_correios[:3]}...{self.id_correios[-2:]}" if len(self.id_correios) >= 5 else "***"
        contrato_masc = f"{self.contrato[:2]}...{self.contrato[-2:]}" if len(self.contrato) >= 4 else "***"
        return (
            f"CorreiosConfig(id_correios='{id_masc}', "
            f"contrato='{contrato_masc}', "
            f"timeout={self.timeout_segundos}s)"
        )
