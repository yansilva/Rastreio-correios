"""Modelos de dados para eventos e status de rastreamento dos Correios."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class EventoRastreio:
    """Representa um evento individual no ciclo de vida de uma encomenda."""
    dt_hr_criado: str
    descricao: str
    detalhe: str = ""
    cidade: str = ""
    uf: str = ""
    codigo: str = ""
    tipo: str = ""

    @property
    def local(self) -> str:
        """Formata 'Cidade/UF' de forma consistente."""
        return f"{self.cidade}/{self.uf}".strip("/")

    @classmethod
    def de_dicionario(cls, dados: dict[str, Any]) -> "EventoRastreio":
        """Cria uma instância a partir do payload de evento da API dos Correios."""
        unidade = dados.get("unidade", {})
        endereco = unidade.get("endereco", {})
        return cls(
            dt_hr_criado=dados.get("dtHrCriado", ""),
            descricao=dados.get("descricao", ""),
            detalhe=dados.get("detalhe", ""),
            cidade=endereco.get("cidade", ""),
            uf=endereco.get("uf", ""),
            codigo=dados.get("codigo", ""),
            tipo=dados.get("tipo", ""),
        )


@dataclass
class ObjetoRastreio:
    """Resultado estruturado e classificado do rastreamento de um objeto."""
    codigo: str
    eventos: list[EventoRastreio] = field(default_factory=list)
    status_categoria: str = "nao_enviado"  # 'entregue', 'devolvido', 'em_transito', 'nao_enviado'
    is_entregue: bool = False
    is_devolvido: bool = False
    is_postado: bool = False
    is_retirada: bool = False
    data_postagem_dt: datetime | None = None
    data_entrega_dt: datetime | None = None
    data_devolucao_dt: datetime | None = None
    ultimo_evento_desc: str = ""
    ultimo_local: str = ""


@dataclass
class PedidoAtrasado:
    """Representa um pedido em trânsito com dias decorridos acima do limite."""
    pedido: str
    rastreio: str
    situacao_tiny: str
    data_postagem: str
    dias_transito: int
    urgencia_label: str  # 'CRÍTICO', 'ALTO', 'ATENÇÃO'
    urgencia_class: str  # 'urgencia-alta', 'urgencia-media', 'urgencia-baixa'
    ultimo_evento: str
    ultimo_local: str
    status: str
