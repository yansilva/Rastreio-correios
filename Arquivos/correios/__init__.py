"""Módulo de integração com as APIs dos Correios."""
from .client import CorreiosClient
from .config import CorreiosConfig
from .exceptions import (
    CorreiosAPIError,
    CorreiosAuthError,
    CorreiosConnectionError,
    CorreiosError,
    CorreiosTimeoutError,
)
from .models import EventoRastreio, ObjetoRastreio, PedidoAtrasado
from .tracking import TrackingService

__all__ = [
    "CorreiosConfig",
    "CorreiosError",
    "CorreiosAuthError",
    "CorreiosAPIError",
    "CorreiosConnectionError",
    "CorreiosTimeoutError",
    "EventoRastreio",
    "ObjetoRastreio",
    "PedidoAtrasado",
    "CorreiosClient",
    "TrackingService",
]
