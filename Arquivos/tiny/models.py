"""Modelos de dados para a integração com o Tiny ERP."""
from dataclasses import dataclass
from typing import Any


@dataclass
class PedidoTiny:
    """Representação simplificada de um pedido retornado pela API do Tiny ERP."""
    id: str
    numero: str
    situacao: str
    codigo_rastreamento: str | None = None

    @classmethod
    def de_dicionario(cls, item: dict[str, Any]) -> "PedidoTiny":
        """
        Cria uma instância de PedidoTiny a partir do dicionário retornado pela API.
        
        A API do Tiny normalmente encapsula o pedido em {"pedido": {...}}.
        Este método suporta tanto o formato aninhado quanto o formato plano.
        """
        dados = item.get("pedido", item)
        return cls(
            id=str(dados.get("id", "")),
            numero=str(dados.get("numero", "")),
            situacao=str(dados.get("situacao", "")),
            codigo_rastreamento=dados.get("codigo_rastreamento")
        )
