"""Serviço de normalização, classificação de status e regras de atraso de encomendas."""
import logging
import re
from datetime import datetime
from typing import Any

from .cards import urgencia_atraso
from .models import EventoRastreio, ObjetoRastreio, PedidoAtrasado

logger = logging.getLogger("correios.tracking")

# Textos reais de retirada na agência
_RETIRADA_REAL = re.compile(r"AGUARDANDO RETIRADA|PARA RETIRADA")
# "Objeto não entregue - ..." contém ENTREGUE, mas não é entrega
_NAO_ENTREGUE = re.compile(r"N[ÃA]O ENTREGUE")

# Eventos que avisam sem mudar o status. Lista explícita, vinda do cache atual:
# - "Sua entrega ou retirada nos Correios pode levar mais tempo do que o previsto" (FC/08)
# - "Inconsistências no endereçamento do objeto." (BDE/19; diz que pode haver atraso ou devolução)
# "Favor desconsiderar a informação anterior" (EST/11) ficou de fora: sozinho não informa nada (decisão do coordenador)
AVISOS_CORREIOS = (
    "PODE LEVAR MAIS TEMPO",
    "INCONSISTÊNCIAS NO ENDEREÇAMENTO",
)

# Marcas de cada evento pelo código "codigo/tipo" (ex.: "BDE/01"), conforme o cache atual.
# Conjunto vazio = evento de status sem marca (transferência, correção de rota, etiqueta).
_MARCAS_POR_CODIGO: dict[str, frozenset[str]] = {
    "BDE/01": frozenset({"entregue"}),  # entregue ao destinatário
    "BDE/23": frozenset({"devolvido"}),  # entregue ao remetente
    "OEC/09": frozenset({"devolvido"}),  # saiu para entrega ao remetente: caminho de devolução
    "BDE/02": frozenset({"nao_entregue"}),
    "BDE/04": frozenset({"nao_entregue"}),
    "BDE/06": frozenset({"nao_entregue"}),
    "BDE/20": frozenset({"nao_entregue"}),
    "BDE/98": frozenset({"nao_entregue"}),
    "BDI/26": frozenset({"nao_entregue"}),  # não entregue: prazo de retirada encerrado
    "BDE/19": frozenset({"aviso"}),  # inconsistências no endereçamento
    "FC/08": frozenset({"aviso"}),  # pode levar mais tempo
    "OEC/01": frozenset({"saiu_para_entrega"}),  # saiu para entrega ao destinatário
    "LDI/01": frozenset({"retirada"}),  # aguardando retirada
    "LDI/03": frozenset({"retirada"}),  # aguardando retirada
    "PO/01": frozenset({"postado"}),
    "DO/01": frozenset(),  # transferência
    "RO/01": frozenset(),  # transferência
    "EST/11": frozenset({"desconsiderar"}),  # favor desconsiderar: desfaz o evento seguinte na lista
    "FC/03": frozenset(),  # correção de rota
    "FC/82": frozenset(),  # etiqueta
}


def _marcas_pelo_texto(descricao: str, detalhe: str) -> frozenset[str]:
    """Reserva para evento sem código conhecido: as regras de antes, aplicadas ao texto."""
    desc = descricao.upper()
    det = detalhe.upper()
    marcas: set[str] = set()
    if "REMETENTE" in desc or "DEVOLVIDO" in desc or "DEVOLUÇÃO" in desc:
        marcas.add("devolvido")
    if _NAO_ENTREGUE.search(desc):
        marcas.add("nao_entregue")
    elif "ENTREGUE" in desc:
        marcas.add("entregue")
    if any(trecho in desc for trecho in AVISOS_CORREIOS):
        marcas.add("aviso")
    if "SAIU PARA ENTREGA" in desc and "devolvido" not in marcas:
        marcas.add("saiu_para_entrega")
    if _RETIRADA_REAL.search(desc) or _RETIRADA_REAL.search(det):
        marcas.add("retirada")
    if "POSTADO" in desc:
        marcas.add("postado")
    if "FAVOR DESCONSIDERAR" in desc:
        marcas.add("desconsiderar")
    return frozenset(marcas)


def marcas_do_evento(evento: EventoRastreio) -> frozenset[str]:
    """Marcas do evento: pelo código (codigo/tipo) quando ele é conhecido; sem código conhecido, pelo texto."""
    if evento.codigo and evento.tipo:
        chave = f"{evento.codigo.strip().upper()}/{evento.tipo.strip().upper()}"
        if chave in _MARCAS_POR_CODIGO:
            return _MARCAS_POR_CODIGO[chave]
    return _marcas_pelo_texto(evento.descricao, evento.detalhe)


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
        saiu_decidido: bool | None = None
        eventos = [EventoRastreio.de_dicionario(ev_data) for ev_data in eventos_raw]
        marcas_da_lista = [marcas_do_evento(evento) for evento in eventos]
        # "Favor desconsiderar a informação anterior" (EST/11) desfaz o evento imediatamente anterior no tempo,
        # que é o seguinte na lista (a API vem do mais novo para o mais antigo). O próprio EST/11 não tem marca:
        # conta como o status mais recente, então desfaz também a retirada ou a saída logo antes dele.
        desconsiderados = {i + 1 for i in range(len(eventos) - 1) if "desconsiderar" in marcas_da_lista[i]}
        for i, evento in enumerate(eventos):
            objeto.eventos.append(evento)

            # Captura informação do evento mais recente (primeiro da lista da API)
            if i == 0:
                objeto.ultimo_evento_desc = evento.descricao
                objeto.ultimo_local = evento.local

            # Evento desfeito por um EST/11 seguinte: fica na lista, mas não decide nada
            if i in desconsiderados:
                evento.desconsiderado = True
                continue
            marcas = marcas_da_lista[i]

            # Retirada vale só pelo evento de status mais recente: avisos não contam (aviso nunca decide status),
            # e uma transferência ou saída para entrega depois da retirada a desfaz
            if "aviso" not in marcas and retirada_decidida is None:
                retirada_decidida = "retirada" in marcas

            # Saiu para entrega vale pelo evento de status mais recente, ignorando avisos;
            # um "não entregue", transferência ou "favor desconsiderar" depois dele desfaz
            if "aviso" not in marcas and saiu_decidido is None:
                saiu_decidido = "saiu_para_entrega" in marcas

            # Aviso mais recente (a lista vem do mais novo para o mais antigo)
            if not objeto.aviso_texto and "aviso" in marcas:
                objeto.aviso_texto = evento.descricao
                objeto.aviso_data = evento.dt_hr_criado

            # Detecta devolução ao remetente
            if "devolvido" in marcas:
                objeto.is_devolvido = True
                if objeto.data_devolucao_dt is None and evento.dt_hr_criado:
                    try:
                        objeto.data_devolucao_dt = datetime.fromisoformat(evento.dt_hr_criado)
                    except Exception:
                        pass

            # Detecta entrega
            elif "entregue" in marcas:
                objeto.is_entregue = True
                if objeto.data_entrega_dt is None and evento.dt_hr_criado:
                    try:
                        objeto.data_entrega_dt = datetime.fromisoformat(evento.dt_hr_criado)
                    except Exception:
                        pass

            # Detecta postagem inicial
            if "postado" in marcas:
                objeto.is_postado = True
                if objeto.data_postagem_dt is None and evento.dt_hr_criado:
                    try:
                        objeto.data_postagem_dt = datetime.fromisoformat(evento.dt_hr_criado)
                    except Exception:
                        pass

        objeto.is_retirada = bool(retirada_decidida)
        # Saiu para entrega nunca vale para entregue nem devolvido
        objeto.saiu_para_entrega = bool(saiu_decidido) and not objeto.is_entregue and not objeto.is_devolvido

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
                if evento.desconsiderado:
                    continue
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
