"""Serviço de normalização, classificação de status e regras de atraso de encomendas."""
import logging
import re
from datetime import datetime
from typing import Any

from .cards import urgencia_atraso
from .models import EventoRastreio, ObjetoRastreio, PedidoAtrasado

logger = logging.getLogger("correios.tracking")

# Aviso dos Correios sobre prazo: não é status, então não decide retirada
_AVISO_DE_PRAZO = "PODE LEVAR MAIS TEMPO"
# Textos reais de retirada na agência
_RETIRADA_REAL = re.compile(r"AGUARDANDO RETIRADA|PARA RETIRADA")

# Eventos que avisam sem mudar o status. Lista explícita, vinda do cache atual:
# - "Sua entrega ou retirada nos Correios pode levar mais tempo do que o previsto"
# - "Inconsistências no endereçamento do objeto." (diz que pode haver atraso ou devolução)
# "Favor desconsiderar a informação anterior" ficou de fora: sozinho não informa nada (decisão do coordenador)
AVISOS_CORREIOS = (
    "PODE LEVAR MAIS TEMPO",
    "INCONSISTÊNCIAS NO ENDEREÇAMENTO",
)


def eh_aviso(descricao: str) -> bool:
    """True quando o evento é um dos avisos conhecidos dos Correios (não é status)."""
    texto = descricao.upper()
    return any(trecho in texto for trecho in AVISOS_CORREIOS)


class TrackingService:
    """Aplica as regras de negócio para análise de status e prazos das encomendas."""

    @staticmethod
    def processar_objeto(codigo: str, dados_brutos: dict[str, Any] | None) -> ObjetoRastreio:
        """
        Transforma o payload bruto retornado pela API dos Correios em um ObjetoRastreio tipado
        e aplica a classificação de status de acordo com o histórico de eventos.
        """
        objeto = ObjetoRastreio(codigo=codigo)
        if not dados_brutos or "eventos" not in dados_brutos:
            logger.debug("Objeto %s sem eventos nos Correios.", codigo)
            return objeto

        eventos_raw = dados_brutos.get("eventos", [])
        retirada_decidida: bool | None = None
        for i, ev_data in enumerate(eventos_raw):
            evento = EventoRastreio.de_dicionario(ev_data)
            objeto.eventos.append(evento)

            desc_upper = evento.descricao.upper()
            det_upper = evento.detalhe.upper()

            # Captura informação do evento mais recente (primeiro da lista da API)
            if i == 0:
                objeto.ultimo_evento_desc = evento.descricao
                objeto.ultimo_local = evento.local

            # Retirada vale só pelo evento de status mais recente: avisos de prazo não contam,
            # e uma transferência ou saída para entrega depois da retirada a desfaz
            if _AVISO_DE_PRAZO not in desc_upper and retirada_decidida is None:
                retirada_decidida = bool(_RETIRADA_REAL.search(desc_upper) or _RETIRADA_REAL.search(det_upper))

            # Aviso mais recente (a lista vem do mais novo para o mais antigo)
            if not objeto.aviso_texto and eh_aviso(evento.descricao):
                objeto.aviso_texto = evento.descricao
                objeto.aviso_data = evento.dt_hr_criado

            # Detecta devolução ao remetente
            if "REMETENTE" in desc_upper or "DEVOLVIDO" in desc_upper or "DEVOLUÇÃO" in desc_upper:
                objeto.is_devolvido = True
                if objeto.data_devolucao_dt is None and evento.dt_hr_criado:
                    try:
                        objeto.data_devolucao_dt = datetime.fromisoformat(evento.dt_hr_criado)
                    except Exception:
                        pass

            # Detecta entrega
            elif "ENTREGUE" in desc_upper:
                objeto.is_entregue = True
                if objeto.data_entrega_dt is None and evento.dt_hr_criado:
                    try:
                        objeto.data_entrega_dt = datetime.fromisoformat(evento.dt_hr_criado)
                    except Exception:
                        pass

            # Detecta postagem inicial
            if "POSTADO" in desc_upper:
                objeto.is_postado = True
                if objeto.data_postagem_dt is None and evento.dt_hr_criado:
                    try:
                        objeto.data_postagem_dt = datetime.fromisoformat(evento.dt_hr_criado)
                    except Exception:
                        pass

        objeto.is_retirada = bool(retirada_decidida)

        # Determina a categoria principal do status
        if objeto.is_devolvido:
            objeto.status_categoria = "devolvido"
        elif objeto.is_entregue:
            objeto.status_categoria = "entregue"
        elif objeto.is_postado:
            objeto.status_categoria = "em_transito"
        else:
            objeto.status_categoria = "nao_enviado"

        return objeto

    @staticmethod
    def verificar_atraso(
        objeto: ObjetoRastreio,
        numero_pedido: str,
        situacao_tiny: str,
        dias_limite: int = 3,
        data_referencia: datetime | None = None,
    ) -> PedidoAtrasado | None:
        """
        Calcula os dias decorridos desde a postagem e retorna um PedidoAtrasado
        caso o prazo ultrapasse o limite (padrão 3 dias).
        """
        now = data_referencia or datetime.now()

        # Devolvidos já têm status próprio: não contam como atraso de entrega
        if objeto.is_devolvido:
            return None

        # Condições: deve ter data de postagem e estar em status elegível
        if not objeto.data_postagem_dt or objeto.status_categoria not in ("em_transito", "entregue", "devolvido"):
            return None

        # Pedidos entregues com sucesso e sem devolução não contam como atrasados
        if objeto.is_entregue and not objeto.is_devolvido:
            return None

        dias_transito = (now - objeto.data_postagem_dt).days
        if dias_transito <= dias_limite:
            return None

        # Classifica nível de urgência
        urgencia_class, rotulo = urgencia_atraso(dias_transito)
        urgencia_label = rotulo.upper()

        return PedidoAtrasado(
            pedido=numero_pedido,
            rastreio=objeto.codigo,
            situacao_tiny=situacao_tiny,
            data_postagem=objeto.data_postagem_dt.strftime("%d/%m/%Y"),
            dias_transito=dias_transito,
            urgencia_label=urgencia_label,
            urgencia_class=urgencia_class,
            ultimo_evento=objeto.ultimo_evento_desc,
            ultimo_local=objeto.ultimo_local,
            status=objeto.status_categoria,
        )

    @staticmethod
    def aviso_do_objeto(objeto: ObjetoRastreio) -> str:
        """Texto do aviso mais recente, enquanto o objeto está em andamento ('' se entregue ou devolvido)."""
        if objeto.status_categoria in ("entregue", "devolvido"):
            return ""
        return objeto.aviso_texto

    @staticmethod
    def deve_ocultar_card(objeto: ObjetoRastreio, data_referencia: datetime | None = None) -> bool:
        """
        Aplica as regras de visibilidade no dashboard:
        - Devolvidos: ocultar assim que o objeto é entregue de volta ao remetente (a loja); enquanto ainda
          está voltando, ocultar se decorridas mais de 24 horas desde o evento de devolução.
        - Entregues: ocultar, salvo se foram entregues hoje. Sem data de entrega, ocultar.
          A aba "Entregues" (histórico local) é que guarda a semana.
        """
        now = data_referencia or datetime.now()

        if objeto.status_categoria == "devolvido":
            for evento in objeto.eventos:
                desc = evento.descricao.upper()
                if "ENTREGUE" in desc and "REMETENTE" in desc:
                    return True
            if objeto.data_devolucao_dt:
                return (now - objeto.data_devolucao_dt).total_seconds() > 24 * 3600
            return False

        if objeto.status_categoria == "entregue":
            if not objeto.data_entrega_dt:
                return True
            return objeto.data_entrega_dt.date() != now.date()

        return False
