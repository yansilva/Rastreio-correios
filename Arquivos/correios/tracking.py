"""Serviço de normalização, classificação de status e regras de atraso de encomendas."""
import logging
from datetime import datetime
from typing import Any

from .models import EventoRastreio, ObjetoRastreio, PedidoAtrasado

logger = logging.getLogger("correios.tracking")


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
        for i, ev_data in enumerate(eventos_raw):
            evento = EventoRastreio.de_dicionario(ev_data)
            objeto.eventos.append(evento)

            desc_upper = evento.descricao.upper()
            det_upper = evento.detalhe.upper()

            # Captura informação do evento mais recente (primeiro da lista da API)
            if i == 0:
                objeto.ultimo_evento_desc = evento.descricao
                objeto.ultimo_local = evento.local

            # Detecta aguardando retirada
            if "RETIRADA" in desc_upper or "RETIRADA" in det_upper:
                objeto.is_retirada = True

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
        if dias_transito >= 7:
            urgencia_label = "CRÍTICO"
            urgencia_class = "urgencia-alta"
        elif dias_transito >= 5:
            urgencia_label = "ALTO"
            urgencia_class = "urgencia-media"
        else:
            urgencia_label = "ATENÇÃO"
            urgencia_class = "urgencia-baixa"

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
    def deve_ocultar_card(objeto: ObjetoRastreio, data_referencia: datetime | None = None) -> bool:
        """
        Aplica as regras de visibilidade no dashboard:
        - Devolvidos: ocultar se decorridas mais de 24 horas desde o evento de devolução.
        - Entregues: ocultar se entregue em semana anterior, ou na semana atual após sexta-feira 18:00.
        """
        now = data_referencia or datetime.now()

        if objeto.status_categoria == "devolvido":
            if objeto.data_devolucao_dt:
                return (now - objeto.data_devolucao_dt).total_seconds() > 24 * 3600
            return False

        if objeto.status_categoria == "entregue":
            if not objeto.data_entrega_dt:
                return True
            entregue_nesta_semana = objeto.data_entrega_dt.isocalendar()[:2] == now.isocalendar()[:2]
            if entregue_nesta_semana:
                apos_sexta_18h = (now.weekday() == 4 and now.hour >= 18) or (now.weekday() > 4)
                return apos_sexta_18h
            return True

        return False
