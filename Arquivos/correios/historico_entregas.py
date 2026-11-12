"""Histórico local dos pedidos entregues, para a aba "Entregues" (semana atual e anterior).

Funções sem rede: o `processar()` é quem decide quando consultar os Correios e chama estas funções.
Semana = segunda a domingo (calendário), igual à semana ISO.
"""
import json
import logging
import math
import os
from datetime import date, datetime, timedelta
from typing import Any

from .models import ObjetoRastreio

ARQUIVO = "entregas_historico.json"

logger = logging.getLogger("correios.historico")


def _estrutura_vazia() -> dict[str, Any]:
    return {"versao": 1, "acompanhados": {}, "entregas": {}}


def _data(valor: Any) -> datetime | None:
    """Data ISO válida ou None. Nunca levanta exceção."""
    if not isinstance(valor, str):
        return None
    try:
        return datetime.fromisoformat(valor)
    except ValueError:
        return None


def carregar(caminho: str) -> dict[str, Any]:
    """Lê o histórico; devolve a estrutura vazia quando o arquivo não existe ou está inválido.

    Entradas de `entregas` sem uma data de entrega válida são descartadas, com aviso no log.
    """
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except FileNotFoundError:
        return _estrutura_vazia()
    except (OSError, ValueError) as exc:
        logger.warning("Histórico de entregas ilegível (%s); começando vazio.", exc)
        return _estrutura_vazia()

    if not isinstance(dados, dict) or not isinstance(dados.get("entregas"), dict):
        logger.warning("Histórico de entregas com formato inesperado; começando vazio.")
        return _estrutura_vazia()
    if not isinstance(dados.get("acompanhados"), dict):
        dados["acompanhados"] = {}

    validas = {
        rastreio: item
        for rastreio, item in dados["entregas"].items()
        if isinstance(item, dict) and _data(item.get("entregue_em")) is not None
    }
    descartadas = len(dados["entregas"]) - len(validas)
    if descartadas:
        logger.warning("Histórico de entregas: %d entrada(s) sem data de entrega válida descartada(s).", descartadas)
    dados["entregas"] = validas
    return dados


def salvar(caminho: str, dados: dict[str, Any]) -> None:
    """Grava o histórico de forma atômica (`.tmp` + `os.replace`), como `correios/cache.py`."""
    temporario = f"{caminho}.tmp"
    try:
        with open(temporario, mode="w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
        os.replace(temporario, caminho)
    except Exception:
        if os.path.exists(temporario):
            os.remove(temporario)
        raise


def _cidade_entrega(objeto: ObjetoRastreio) -> str:
    """Cidade/UF do evento de entrega; sem ele, a cidade do último evento."""
    for evento in objeto.eventos:
        if "ENTREGUE" in evento.descricao.upper():
            return evento.local
    return objeto.ultimo_local


def registrar_entrega(
    dados: dict[str, Any], objeto: ObjetoRastreio, pedido: str, cliente: str, agora: datetime
) -> bool:
    """Registra o objeto se ele estiver entregue e ainda não estiver no histórico.

    Devolve True só quando registra uma entrega nova. Sem data de entrega, não registra (não há como
    pôr o pedido numa semana).
    """
    if objeto.status_categoria != "entregue" or objeto.data_entrega_dt is None:
        return False
    rastreio = objeto.codigo
    if rastreio in dados["entregas"]:
        return False

    dados["entregas"][rastreio] = {
        "pedido": str(pedido),
        "cliente": cliente or "",
        "rastreio": rastreio,
        "cidade": _cidade_entrega(objeto),
        "postado_em": objeto.data_postagem_dt.isoformat(timespec="seconds") if objeto.data_postagem_dt else None,
        "entregue_em": objeto.data_entrega_dt.isoformat(timespec="seconds"),
        "registrado_em": agora.isoformat(timespec="seconds"),
    }
    return True


def _inicio_semana(agora: datetime, deslocamento: int = 0) -> date:
    """Segunda-feira da semana de `agora`, deslocada em semanas (0 = atual, -1 = anterior)."""
    hoje = agora.date()
    return hoje - timedelta(days=hoje.weekday()) + timedelta(weeks=deslocamento)


def _data_entrega(item: dict[str, Any]) -> date | None:
    data = _data(item.get("entregue_em"))
    return data.date() if data else None


def podar(dados: dict[str, Any], agora: datetime) -> None:
    """Mantém só as entregas da semana atual e da anterior. Entradas sem data válida saem."""
    inicio_anterior = _inicio_semana(agora, -1)
    fim_atual = _inicio_semana(agora, 0) + timedelta(days=6)
    dados["entregas"] = {
        rastreio: item
        for rastreio, item in dados["entregas"].items()
        if (dia := _data_entrega(item)) is not None and inicio_anterior <= dia <= fim_atual
    }


def entregas_da_semana(dados: dict[str, Any], agora: datetime, deslocamento: int = 0) -> list[dict[str, Any]]:
    """Entregas da semana atual (0) ou da anterior (-1), da mais recente para a mais antiga."""
    inicio = _inicio_semana(agora, deslocamento)
    fim = inicio + timedelta(days=6)
    validas = [
        (_data(item["entregue_em"]), item)
        for item in dados["entregas"].values()
        if isinstance(item, dict) and (dia := _data_entrega(item)) is not None and inicio <= dia <= fim
    ]
    validas.sort(key=lambda par: par[0], reverse=True)
    return [dict(item) for _, item in validas]


def _uma_casa(valor: float) -> float:
    """Arredonda para uma casa decimal, metade para cima (2,25 vira 2,3)."""
    return math.floor(valor * 10 + 0.5) / 10


def dias_ate_entrega(item: dict[str, Any]) -> float | None:
    """Dias corridos da postagem até a entrega, com uma casa decimal. None sem data de postagem."""
    postado = _data(item.get("postado_em"))
    entregue = _data(item.get("entregue_em"))
    if postado is None or entregue is None:
        return None
    return _uma_casa((entregue - postado).total_seconds() / 86400)


def resumo(lista: list[dict[str, Any]]) -> dict[str, Any]:
    """Total de entregas, média de dias (sem os que não têm postagem) e o pedido mais demorado."""
    com_dias = [(dias_ate_entrega(item), item) for item in lista]
    com_dias = [(dias, item) for dias, item in com_dias if dias is not None]
    if not com_dias:
        return {"total": len(lista), "media_dias": None, "mais_demorado": None}

    media = _uma_casa(sum(dias for dias, _ in com_dias) / len(com_dias))
    _, mais_demorado = max(com_dias, key=lambda par: par[0])
    return {"total": len(lista), "media_dias": media, "mais_demorado": dict(mais_demorado)}
