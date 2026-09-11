"""Módulo de consulta de frete dos Correios."""
from .client import FreteClient
from .config import FreteConfig
from .exceptions import (
    FreteAPIError,
    FreteConnectionError,
    FreteError,
    FreteServicoIndisponivelError,
    FreteTimeoutError,
)
from .models import OpcaoFrete, normalizar_cep, validar_cep, validar_dimensoes
from .report import FreteReportGenerator
from .service import FreteService

__all__ = [
    "FreteConfig",
    "FreteError",
    "FreteAPIError",
    "FreteConnectionError",
    "FreteTimeoutError",
    "FreteServicoIndisponivelError",
    "OpcaoFrete",
    "validar_cep",
    "normalizar_cep",
    "validar_dimensoes",
    "FreteClient",
    "FreteService",
    "FreteReportGenerator",
]
