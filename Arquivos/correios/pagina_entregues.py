"""Página "Entregues": as entregas da semana atual e da anterior, lidas do histórico local.

As funções de histórico vêm de `historico_entregas`. Esta função só monta o HTML; a gravação
fica em `gerar_pagina_entregues`.
"""

import os
import time
from datetime import datetime, timedelta
from html import escape

from correios.historico_entregas import _inicio_semana, dias_ate_entrega, entregas_da_semana, resumo
from correios.icons import ICON_SPRITE

ARQUIVO_ENTREGUES = "entregues_semana.html"

# Acima deste número de dias, o tempo de entrega recebe o tom de aviso (o mesmo de atrasados)
LIMITE_DIAS_AVISO = 7


def _intervalo_semana(agora: datetime, deslocamento: int):
    """Segunda e domingo da semana de `agora`, deslocada em semanas."""
    segunda = _inicio_semana(agora, deslocamento)
    return segunda, segunda + timedelta(days=6)


def _texto(valor: str | None) -> str:
    """Texto escapado; vazio vira traço."""
    return escape(valor) if valor else "—"


def _fmt_data(iso: str | None) -> str:
    if not iso:
        return "—"
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return escape(iso)


def _fmt_dias(valor: float) -> str:
    return f"{valor:.1f}".replace(".", ",")


def _celula_dias(item: dict) -> str:
    dias = dias_ate_entrega(item)
    if dias is None:
        return "—"
    texto = f"{_fmt_dias(dias)} dias"
    if dias > LIMITE_DIAS_AVISO:
        return f'<span class="dias-badge urgencia-baixa">{texto}</span>'
    return texto


def _resumo_html(itens: list[dict]) -> str:
    info = resumo(itens)
    media = "—" if info["media_dias"] is None else _fmt_dias(info["media_dias"])
    mais = info["mais_demorado"]
    if mais is None:
        numero_mais, rotulo_mais = "—", "Mais demorado"
    else:
        numero_mais = f"#{escape(mais['pedido'])}"
        rotulo_mais = f"Mais demorado · {_fmt_dias(dias_ate_entrega(mais))} dias"
    return f"""
            <div class="summary">
                <div class="summary-card">
                    <div class="summary-number">{info["total"]}</div>
                    <div class="summary-label">Entregues</div>
                </div>
                <div class="summary-card">
                    <div class="summary-number">{media}</div>
                    <div class="summary-label">Média de dias</div>
                </div>
                <div class="summary-card">
                    <div class="summary-number">{numero_mais}</div>
                    <div class="summary-label">{rotulo_mais}</div>
                </div>
            </div>"""


def _linhas_html(itens: list[dict]) -> str:
    linhas = ""
    for item in itens:
        rastreio = escape(item["rastreio"], quote=True)
        linhas += f"""
                    <tr role="row">
                        <td role="cell" data-label="Pedido"><strong>#{escape(item["pedido"])}</strong></td>
                        <td role="cell" data-label="Cliente">{_texto(item.get("cliente"))}</td>
                        <td role="cell" data-label="Rastreio"><code>{rastreio}</code> <button type="button" class="btn-copy" data-copy="{rastreio}" aria-label="Copiar código de rastreio {rastreio}">Copiar rastreio</button></td>
                        <td role="cell" data-label="Cidade">{_texto(item.get("cidade"))}</td>
                        <td role="cell" data-label="Postado em">{_fmt_data(item.get("postado_em"))}</td>
                        <td role="cell" data-label="Entregue em">{_fmt_data(item.get("entregue_em"))}</td>
                        <td role="cell" data-label="Dias">{_celula_dias(item)}</td>
                    </tr>"""
    return linhas


def _secao_html(indice: int, titulo: str, itens: list[dict]) -> str:
    """Uma semana: resumo e tabela, ou o estado vazio. Só a semana escolhida fica visível."""
    oculta = "" if indice == 0 else " hidden"
    # Texto que o leitor de tela anuncia ao trocar de semana
    quantidade = "nenhuma entrega" if not itens else ("1 entrega" if len(itens) == 1 else f"{len(itens)} entregas")
    anuncio = f"{'Esta semana' if indice == 0 else 'Semana anterior'}: {quantidade}"
    if not itens:
        corpo = """
            <div class="table-wrapper">
                <div class="empty-state">
                    <div class="emoji"><svg class="icon icon-check-circle" aria-hidden="true" focusable="false"><use href="#i-check-circle"></use></svg></div>
                    <h2>Nenhuma entrega nesta semana</h2>
                </div>
            </div>"""
    else:
        corpo = f"""{_resumo_html(itens)}
            <div class="table-wrapper">
                <table role="table">
                    <caption class="sr-only">{titulo}</caption>
                    <thead role="rowgroup">
                        <tr role="row">
                            <th role="columnheader" scope="col">Pedido</th>
                            <th role="columnheader" scope="col">Cliente</th>
                            <th role="columnheader" scope="col">Rastreio</th>
                            <th role="columnheader" scope="col">Cidade</th>
                            <th role="columnheader" scope="col">Postado em</th>
                            <th role="columnheader" scope="col">Entregue em</th>
                            <th role="columnheader" scope="col">Dias</th>
                        </tr>
                    </thead>
                    <tbody role="rowgroup">{_linhas_html(itens)}
                    </tbody>
                </table>
            </div>"""
    return f"""
        <section class="entregues-painel" data-painel-semana="{indice}" data-anuncio="{escape(anuncio, quote=True)}" aria-labelledby="titulo-semana-{indice}"{oculta}>
            <h2 id="titulo-semana-{indice}" class="sr-only">{titulo}</h2>{corpo}
        </section>"""


def montar_html_entregues(historico: dict, agora: datetime) -> str:
    """HTML completo da página Entregues, com as semanas atual e anterior. Não faz I/O."""
    semana_atual = entregas_da_semana(historico, agora, 0)
    semana_anterior = entregas_da_semana(historico, agora, -1)

    seg_atual, dom_atual = _intervalo_semana(agora, 0)
    seg_anterior, dom_anterior = _intervalo_semana(agora, -1)
    rotulo_atual = f"Esta semana ({seg_atual:%d/%m}–{dom_atual:%d/%m})"
    titulo_atual = f"Entregas desta semana ({seg_atual:%d/%m}–{dom_atual:%d/%m})"
    titulo_anterior = f"Entregas da semana anterior ({seg_anterior:%d/%m}–{dom_anterior:%d/%m})"
    versao = int(time.time())

    return f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Entregues — Rastreio Correios</title>
    <link rel="stylesheet" href="web/css/main.css?v={versao}">
    <link rel="stylesheet" href="web/css/components.css?v={versao}">
</head>
<body>
    {ICON_SPRITE}
    <a class="skip-link" href="#conteudo">Pular para as entregas</a>
    <div id="toast" class="toast" role="status" aria-live="polite"></div>
    <div class="container">
        <header>
            <div class="header-tools">
                <button id="btnTheme" class="btn-theme">
            <svg class="icon icon-sun" aria-hidden="true" focusable="false"><use href="#i-sun"></use></svg><svg class="icon icon-moon" aria-hidden="true" focusable="false"><use href="#i-moon"></use></svg><span id="btnThemeText">Escuro</span>
        </button>
            </div>
            <div class="header-main">
                <h1><svg class="icon icon-check-circle" aria-hidden="true" focusable="false"><use href="#i-check-circle"></use></svg> Entregues</h1>
                <div class="meta">Pedidos entregues por semana — Gerado em: {agora:%d/%m/%Y %H:%M}</div>
            </div>
        </header>
        <nav class="nav-tabs" aria-label="Navegação do painel">
            <a href="relatorio_rastreio.html" class="nav-tab"><svg class="icon icon-bar-chart" aria-hidden="true" focusable="false"><use href="#i-bar-chart"></use></svg> Painel</a>
            <a href="pedidos_atrasados.html" class="nav-tab"><svg class="icon icon-clock" aria-hidden="true" focusable="false"><use href="#i-clock"></use></svg> Atrasados</a>
            <a href="entregues_semana.html" class="nav-tab active" aria-current="page"><svg class="icon icon-check-circle" aria-hidden="true" focusable="false"><use href="#i-check-circle"></use></svg> Entregues</a>
            <a href="opcoes_frete.html" class="nav-tab"><svg class="icon icon-package" aria-hidden="true" focusable="false"><use href="#i-package"></use></svg> Opções de Frete</a>
        </nav>

        <main id="conteudo" tabindex="-1">
            <div class="entregues-seletor" role="group" aria-label="Escolher semana">
                <button type="button" data-semana="0" aria-pressed="true">{rotulo_atual}</button>
                <button type="button" data-semana="1" aria-pressed="false">Semana anterior</button>
            </div>
            <p id="entregues-anuncio" class="sr-only" role="status" aria-live="polite"></p>
            {_secao_html(0, titulo_atual, semana_atual)}
            {_secao_html(1, titulo_anterior, semana_anterior)}
        </main>
    </div>

    <script src="web/js/app.js?v={versao}"></script>
    <script src="web/js/entregues.js?v={versao}"></script>
</body>
</html>"""


def gerar_pagina_entregues(historico: dict, agora: datetime, destino: str) -> str:
    """Grava `entregues_semana.html` na pasta `destino` e devolve o caminho do arquivo."""
    caminho = os.path.join(destino, ARQUIVO_ENTREGUES)
    with open(caminho, mode="w", encoding="utf-8") as f:
        f.write(montar_html_entregues(historico, agora))
    return caminho
