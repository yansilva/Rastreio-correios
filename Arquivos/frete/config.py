"""Configurações da consulta de frete dos Correios."""
import os
from dataclasses import dataclass, field
from typing import Dict

from dotenv import load_dotenv

# Carrega .env da raiz do projeto e de Arquivos/
_raiz_projeto = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_pasta_arquivos = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_raiz_projeto, ".env"))
load_dotenv(os.path.join(_pasta_arquivos, ".env"))

# Serviços padrão — mesmos valores do consulta_frete.py original
_SERVICOS_PADRAO: Dict[str, str] = {
    "03220": "SEDEX",
    "03158": "SEDEX 10",
    "03140": "SEDEX 12",
}


@dataclass
class FreteConfig:
    """Parâmetros para consulta de preço e prazo de frete nos Correios.

    Não armazena credenciais — estas pertencem a CorreiosConfig.
    """

    # Endereço de origem
    cep_origem: str = ""

    # Dimensões e peso do pacote padrão
    peso_gramas: int = 1000
    comprimento: int = 30
    largura: int = 20
    altura: int = 10
    tipo_objeto: int = 2  # 2 = Pacote

    # Serviços consultados (código → nome legível)
    servicos: Dict[str, str] = field(default_factory=lambda: dict(_SERVICOS_PADRAO))

    # URLs da API de preço/prazo
    url_preco: str = "https://api.correios.com.br/preco/v1/nacional/{coProduto}"
    url_prazo: str = "https://api.correios.com.br/prazo/v1/nacional/{coProduto}"

    # Rede
    timeout_segundos: float = 15.0

    # Saída
    relatorio_html: str = "opcoes_frete.html"
    dias_atras: int = 30

    def __post_init__(self):
        if not self.cep_origem:
            self.cep_origem = os.environ.get("CEP_ORIGEM", "05617010")

    def __repr__(self) -> str:
        return (
            f"FreteConfig(cep_origem='{self.cep_origem}', "
            f"peso={self.peso_gramas}g, "
            f"{self.comprimento}x{self.largura}x{self.altura}cm, "
            f"servicos={list(self.servicos.keys())})"
        )
