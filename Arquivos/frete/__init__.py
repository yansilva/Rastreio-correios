"""Módulo de consulta de frete dos Correios."""
from .config import FreteConfig
from .exceptions import (
    FreteAPIError,
    FreteConnectionError,
    FreteError,
    FreteServicoIndisponivelError,
    FreteTimeoutError,
)
from .models import OpcaoFrete, validar_cep, normalizar_cep, validar_dimensoes
from .client import FreteClient
from .service import FreteService
from .report import FreteReportGenerator

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
