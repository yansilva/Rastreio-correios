"""Cache em disco das últimas respostas dos Correios, para regerar o relatório sem chamar as APIs."""
import json
import os
from datetime import datetime
from typing import Any


def salvar_cache(caminho: str, objetos: dict[str, Any], quando: datetime | None = None) -> None:
    """Grava o retorno bruto de cada objeto e o momento da consulta (escrita atômica)."""
    dados = {"gerado_em": (quando or datetime.now()).isoformat(timespec="seconds"), "objetos": objetos}
    temporario = f"{caminho}.tmp"
    with open(temporario, mode="w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False)
    os.replace(temporario, caminho)


def carregar_cache(caminho: str) -> tuple[dict[str, Any], datetime] | None:
    """Lê o cache; devolve None quando o arquivo não existe ou está inválido."""
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, ValueError):
        return None

    objetos = dados.get("objetos") if isinstance(dados, dict) else None
    if not isinstance(objetos, dict):
        return None

    try:
        quando = datetime.fromisoformat(dados.get("gerado_em", ""))
    except (TypeError, ValueError):
        quando = datetime.fromtimestamp(os.path.getmtime(caminho))
    return objetos, quando
