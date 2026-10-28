"""Geração do relatório HTML de opções de frete.

Responsabilidade exclusiva: montar e salvar os arquivos de saída.
NÃO consulta APIs, NÃO decide qual frete recomendar.

O visual segue o DESIGN.md (tokens, rampa de fontes, ícones SVG do sprite) e
mantém compatibilidade com o painel e alert_frete.js.
"""
import html
import logging
import os
import time
from typing import Any

from correios.icons import ICON_SPRITE, icone

from .config import FreteConfig

logger = logging.getLogger("frete.report")

_MOTIVO_PADRAO = "Indisponível para este destino"


def _fmt_prazo(prazo: Any) -> str:
    """Prazo em dias úteis, com plural correto ('1 dia útil', 'N dias úteis')."""
    if not prazo:
        return "—"
    return f"{prazo} dia útil" if prazo == 1 else f"{prazo} dias úteis"


def _motivo_indisponivel(info: dict[str, Any]) -> str:
    """Motivo curto de indisponibilidade; ignora textos vazios, genéricos ou longos (erros técnicos)."""
    for chave in ("motivo", "erro"):
        texto = str(info.get(chave) or "").strip()
        if texto and texto.lower() != "indisponível" and len(texto) <= 60:
            return html.escape(texto)
    return _MOTIVO_PADRAO


def _destaques(servicos: dict[str, Any], codigos: Any) -> tuple[set[str], set[str]]:
    """Códigos do serviço mais barato e do mais rápido (empates incluídos).

    Só destaca quando há pelo menos duas opções comparáveis; com uma só, o selo seria ruído.
    """
    precos: dict[str, float] = {}
    prazos: dict[str, float] = {}
    for cod in codigos:
        info = servicos.get(cod) or {}
        if not info.get("disponivel"):
            continue
        if isinstance(info.get("preco"), (int, float)):
            precos[cod] = info["preco"]
        if isinstance(info.get("prazo"), (int, float)) and info["prazo"] > 0:
            prazos[cod] = info["prazo"]

    def minimos(valores: dict[str, float]) -> set[str]:
        if len(valores) < 2:
            return set()
        menor = min(valores.values())
        return {c for c, v in valores.items() if v == menor}

    return minimos(precos), minimos(prazos)


class FreteReportGenerator:
    """Gera o HTML de opções de frete e o script de alertas."""

    def __init__(self, config: FreteConfig | None = None):
        self.config = config or FreteConfig()

    def gerar_html(
        self,
        pedidos_com_frete: list[dict[str, Any]],
        alertas_extras: list[str] | None = None,
    ) -> str:
        """Gera e salva a página HTML premium com opções de frete.

        Args:
            pedidos_com_frete: Lista de dicts com dados do pedido e servicos (formato legado).
            alertas_extras: Lista de números de pedidos para alerta extra.

        Returns:
            Caminho absoluto do arquivo HTML gerado.
        """
        config = self.config

        data_geracao = time.strftime('%d/%m/%Y %H:%M:%S')
        total_pedidos = len(pedidos_com_frete)

        # Conta pedidos com pelo menos 1 serviço disponível
        com_opcoes = sum(
            1 for p in pedidos_com_frete
            if any(s["disponivel"] for s in p.get("servicos", {}).values())
        )

        pedidos_com_prazo_longo = []

        # Inclui alertas de pedidos Motoboy/Retirada com prazo longo (não exibidos nos cards)
        if alertas_extras:
            pedidos_com_prazo_longo.extend(alertas_extras)

        # Monta os cards de pedido
        cards_html = ""
        for pedido in pedidos_com_frete:
            try:
                valor_float = float(pedido.get('valor', 0))
                valor_fmt = f"R$ {valor_float:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            except Exception:
                valor_float = 0.0
                valor_fmt = "R$ 0,00"

            servicos_pedido = pedido.get("servicos", {})
            codigos_barato, codigos_rapido = _destaques(servicos_pedido, config.servicos.keys())

            servicos_html = ""
            for cod in config.servicos.keys():
                nome = config.servicos[cod]
                info = servicos_pedido.get(cod, {"disponivel": False})

                if info["disponivel"]:
                    preco_display = info.get("preco_fmt") or "—"
                    prazo_display = _fmt_prazo(info.get("prazo"))
                    if info.get("prazo") and info["prazo"] > 3:
                        if str(pedido['numero']) not in pedidos_com_prazo_longo:
                            pedidos_com_prazo_longo.append(str(pedido['numero']))

                    msg_prazo_html = ""
                    if info.get("msg_prazo"):
                        msg = html.escape(str(info["msg_prazo"]))
                        msg_prazo_html = f'\n                    <div class="servico-msg-prazo" title="{msg}">{icone("alert-triangle")} {msg}</div>'

                    selos = ""
                    if cod in codigos_barato:
                        selos += '<span class="servico-selo">Mais barato</span>'
                    if cod in codigos_rapido:
                        selos += '<span class="servico-selo">Mais rápido</span>'
                    selos_html = f'\n                    <div class="servico-selos">{selos}</div>' if selos else ""

                    servicos_html += f"""
                <div class="servico-card disponivel">
                    <div class="servico-nome">{nome}</div>
                    <div class="servico-preco">{preco_display}</div>
                    <div class="servico-prazo">{icone("clock")} {prazo_display}</div>{msg_prazo_html}{selos_html}
                </div>"""
                else:
                    motivo = _motivo_indisponivel(info)
                    servicos_html += f"""
                <div class="servico-card indisponivel">
                    <div class="servico-nome">{nome}</div>
                    <div class="servico-status">Indisponível</div>
                    <div class="servico-motivo">{motivo}</div>
                </div>"""

            cards_html += f"""
        <div class="pedido-card" data-valor="{valor_float}">
            <div class="pedido-header">
                <div class="pedido-left">
                    <span class="pedido-numero">Pedido #{pedido['numero']} <span class="pedido-valor">{valor_fmt}</span></span>
                    <span class="pedido-cliente">{pedido.get('nome_cliente', '—')}</span>
                </div>
                <div class="pedido-right">
                    <span class="pedido-badge">{pedido['situacao']}</span>
                    <span class="pedido-destino">{icone("map-pin")} {pedido.get('destino_label', '—')} — CEP {pedido.get('cep_destino', '—')}</span>
                </div>
            </div>
            <div class="servicos-grid">
                {servicos_html}
            </div>
        </div>"""

        # Estado vazio
        if not pedidos_com_frete:
            cards_html = f"""
        <div class="empty-state">
            <div class="empty-icon">{icone("inbox")}</div>
            <h2>Nenhum pedido em aberto</h2>
            <p>Todos os pedidos do período já foram enviados ou não possuem CEP de destino.</p>
        </div>"""

        html_page = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Opções de Frete — Correios</title>
    <style>
        :root {{
            --color-primary: #2563eb;
            --color-primary-hover: #1d4ed8;
            --color-primary-light: #eff6ff;
            --color-link: #2563eb;
            --color-bg: #f8fafc;
            --color-surface: #ffffff;
            --color-surface-hover: #f1f5f9;
            --color-header-bg: #f1f5f9;
            --color-border: #e2e8f0;
            --color-text-main: #0f172a;
            --color-text-muted: #475569;
            --color-text-subtle: #64748b;
            --color-success: #15803d;
            --color-success-bg: #dcfce7;
            --color-success-border: #bbf7d0;
            --color-warning: #b45309;
            --color-warning-bg: #fef3c7;
            --color-warning-border: #fde68a;
            --color-success-text: #166534;
            --color-warning-text: #92400e;
            --color-border-strong: #64748b;
            --color-badge-fg: #1d4ed8;
            --color-badge-bg: #eff6ff;
            --color-badge-border: #bfdbfe;
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 16px;
            --radius-full: 9999px;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        [data-theme="dark"] {{
            --color-bg: #0b0f19;
            --color-surface: #151c2c;
            --color-surface-hover: #1e283d;
            --color-header-bg: #192237;
            --color-border: #26334d;
            --color-text-main: #f8fafc;
            --color-text-muted: #b6c2d2;
            --color-text-subtle: #94a3b8;
            --color-primary-light: #1e293b;
            --color-link: #93c5fd;
            --color-success: #4ade80;
            --color-success-bg: rgba(22, 163, 74, 0.15);
            --color-success-border: rgba(74, 222, 128, 0.35);
            --color-warning: #fbbf24;
            --color-warning-bg: rgba(217, 119, 6, 0.15);
            --color-warning-border: rgba(251, 191, 36, 0.35);
            --color-success-text: #4ade80;
            --color-warning-text: #fbbf24;
            --color-badge-fg: #93c5fd;
            --color-badge-bg: rgba(37, 99, 235, 0.18);
            --color-badge-border: rgba(147, 197, 253, 0.35);
        }}
        *, *::before, *::after {{ box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: var(--color-bg);
            color: var(--color-text-main);
            margin: 0;
            padding: 24px 20px 48px;
            line-height: 1.6;
            transition: background-color 0.3s ease, color 0.3s ease;
        }}
        .container {{ max-width: 1040px; margin: 0 auto; }}
        header {{ position: relative; text-align: center; margin-bottom: 30px; }}
        h1 {{
            margin: 0;
            font-size: 1.75rem;
            font-weight: 800;
            letter-spacing: -0.025em;
            color: var(--color-primary);
        }}
        [data-theme="dark"] h1 {{ color: var(--color-link); }}
        .meta {{ color: var(--color-text-muted); margin-top: 8px; font-size: 0.875rem; }}
        .config-info {{
            display: inline-block;
            margin-top: 10px;
            padding: 6px 16px;
            background: var(--color-header-bg);
            border: 1px solid var(--color-border);
            border-radius: var(--radius-md);
            font-size: 0.875rem;
            color: var(--color-text-muted);
        }}

        /* Ícones SVG (sprite inline): traço fino, cor herdada do texto */
        .icon {{
            width: 1.1em;
            height: 1.1em;
            flex-shrink: 0;
            fill: none;
            stroke: currentColor;
            stroke-width: 1.75;
            stroke-linecap: round;
            stroke-linejoin: round;
            vertical-align: -0.18em;
        }}
        h1 .icon {{ width: 0.95em; height: 0.95em; margin-right: 4px; }}

        /* Navegação por abas: mesmo markup e estilo do painel (.nav-tabs/.nav-tab) */
        .nav-tabs {{
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 18px 0 0 0;
            flex-wrap: wrap;
        }}
        .nav-tab {{
            padding: 9px 18px;
            min-height: 44px;
            border-radius: var(--radius-full);
            text-decoration: none;
            font-weight: 600;
            font-size: 0.875rem;
            color: var(--color-text-muted);
            background: var(--color-surface);
            border: 1px solid var(--color-border);
            transition: var(--transition);
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}
        .nav-tab:hover {{ color: var(--color-link); border-color: var(--color-primary); }}
        .nav-tab.active {{
            background: var(--color-primary);
            color: #ffffff;
            border-color: var(--color-primary);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
        }}
        .nav-tab.active:hover {{ color: #ffffff; }}

        /* Ferramentas do cabeçalho: o tema fica no topo, fora do conteúdo */
        .header-tools {{ position: absolute; top: 0; right: 0; }}
        .btn-theme, .btn-limpar {{
            background: var(--color-surface);
            color: var(--color-text-main);
            border: 1px solid var(--color-border-strong);
            padding: 10px 18px;
            min-height: 44px;
            font: inherit;
            font-weight: 600;
            font-size: 0.875rem;
            border-radius: var(--radius-full);
            cursor: pointer;
            box-shadow: var(--shadow-sm);
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: var(--transition);
        }}
        .btn-theme:hover, .btn-limpar:hover {{
            background: var(--color-surface-hover);
            border-color: var(--color-primary);
            color: var(--color-primary);
        }}
        [data-theme="dark"] .btn-theme:hover, [data-theme="dark"] .btn-limpar:hover {{ color: var(--color-link); }}
        .btn-theme:active, .btn-limpar:active {{ transform: scale(0.97); }}
        /* Mostra o tema de destino: lua/"Escuro" no claro, sol/"Claro" no escuro */
        .btn-theme .icon-sun, .btn-theme .tema-claro {{ display: none; }}
        [data-theme="dark"] .btn-theme .icon-sun, [data-theme="dark"] .btn-theme .tema-claro {{ display: inline-block; }}
        [data-theme="dark"] .btn-theme .icon-moon, [data-theme="dark"] .btn-theme .tema-escuro {{ display: none; }}

        .nav-tab:focus-visible, .btn-theme:focus-visible, .btn-limpar:focus-visible {{
            outline: 2px solid var(--color-primary);
            outline-offset: 3px;
        }}
        [data-theme="dark"] .nav-tab:focus-visible, [data-theme="dark"] .btn-theme:focus-visible,
        [data-theme="dark"] .btn-limpar:focus-visible {{ outline-color: var(--color-link); }}

        /* Filter Bar */
        .filter-bar {{
            display: flex;
            align-items: center;
            gap: 16px;
            background: var(--color-surface);
            padding: 16px 24px;
            border-radius: var(--radius-lg);
            border: 1px solid var(--color-border);
            margin-bottom: 24px;
            box-shadow: var(--shadow-sm);
            flex-wrap: wrap;
        }}
        .filter-group {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .filter-group label {{
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--color-text-muted);
        }}
        .filter-group input {{
            padding: 8px 12px;
            border: 1px solid var(--color-border-strong);
            border-radius: var(--radius-md);
            background: var(--color-bg);
            color: var(--color-text-main);
            font: inherit;
            font-size: 1rem;
            min-height: 44px;
            width: 120px;
            transition: border-color 0.2s, box-shadow 0.2s;
        }}
        .filter-group input::placeholder {{ color: var(--color-text-subtle); }}
        .filter-group input:focus-visible {{
            outline: none;
            border-color: var(--color-primary);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.25);
        }}
        .filter-count {{
            margin-left: auto;
            font-size: 0.875rem;
            color: var(--color-text-muted);
            font-weight: 600;
        }}
        .filter-aviso {{
            flex-basis: 100%;
            margin: 0;
            padding: 6px 12px;
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--color-warning-text);
            background: var(--color-warning-bg);
            border: 1px solid var(--color-warning-border);
            border-radius: var(--radius-sm);
        }}
        .filter-aviso:empty {{ display: none; }}

        /* Summary Cards */
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: var(--color-surface);
            border: 1px solid var(--color-border);
            border-radius: var(--radius-lg);
            padding: 18px 20px;
            box-shadow: var(--shadow-sm);
            text-align: center;
            animation: fadeIn 0.4s ease forwards;
        }}
        .summary-card:nth-child(2) {{ animation-delay: 0.1s; }}
        .summary-number {{ font-size: 1.75rem; font-weight: 800; line-height: 1.1; }}
        .summary-label {{ font-size: 0.75rem; color: var(--color-text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 6px; }}
        .num-blue {{ color: var(--color-primary); }}
        [data-theme="dark"] .num-blue {{ color: var(--color-link); }}
        .num-neutral {{ color: var(--color-text-main); }}

        /* Pedido Cards */
        .pedido-card {{
            background: var(--color-surface);
            border: 1px solid var(--color-border);
            border-radius: var(--radius-lg);
            margin-bottom: 20px;
            overflow: hidden;
            box-shadow: var(--shadow-md);
            animation: fadeIn 0.4s ease forwards;
        }}
        .pedido-header {{
            padding: 16px 24px;
            background: var(--color-header-bg);
            border-bottom: 1px solid var(--color-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .pedido-left {{ display: flex; flex-direction: column; gap: 4px; }}
        .pedido-numero {{ font-weight: 700; font-size: 1.25rem; }}
        .pedido-valor {{ font-size: 0.875rem; font-weight: 600; color: var(--color-text-muted); margin-left: 8px; }}
        .pedido-cliente {{ color: var(--color-text-muted); font-size: 0.875rem; }}
        .pedido-right {{ display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }}
        .pedido-badge {{
            background: var(--color-badge-bg);
            color: var(--color-badge-fg);
            border: 1px solid var(--color-badge-border);
            padding: 2px 10px;
            border-radius: var(--radius-full);
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .pedido-destino {{
            color: var(--color-text-muted);
            font-size: 0.875rem;
        }}

        /* Serviços Grid */
        .servicos-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            padding: 18px 24px;
        }}
        .servico-card {{
            border: 1px solid var(--color-border);
            border-radius: var(--radius-md);
            padding: 16px;
            text-align: center;
            transition: var(--transition);
        }}
        .servico-card.disponivel {{
            background: var(--color-surface);
            border-color: var(--color-border);
        }}
        .servico-card.indisponivel {{
            background: var(--color-header-bg);
        }}
        .servico-nome {{
            font-weight: 800;
            font-size: 1rem;
            margin-bottom: 8px;
            color: var(--color-text-main);
        }}
        .servico-preco {{
            font-size: 1.25rem;
            font-weight: 800;
            color: var(--color-text-main);
            margin-bottom: 4px;
        }}
        .servico-selos {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 6px;
            margin-top: 10px;
        }}
        .servico-selo {{
            background: var(--color-badge-bg);
            color: var(--color-badge-fg);
            border: 1px solid var(--color-badge-border);
            padding: 2px 10px;
            border-radius: var(--radius-full);
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .servico-prazo {{
            font-size: 0.875rem;
            color: var(--color-text-muted);
            font-weight: 500;
        }}
        .servico-status {{
            color: var(--color-text-muted);
            font-size: 0.875rem;
            font-weight: 600;
        }}
        .servico-motivo {{
            color: var(--color-text-muted);
            font-size: 0.8125rem;
            margin-top: 2px;
        }}
        .servico-msg-prazo {{
            font-size: 0.8125rem;
            color: var(--color-warning-text);
            margin-top: 8px;
            padding: 6px 10px;
            background: var(--color-warning-bg);
            border: 1px solid var(--color-warning-border);
            border-radius: var(--radius-sm);
            text-align: left;
            word-break: break-word;
            line-height: 1.4;
        }}

        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: var(--color-text-muted);
            background: var(--color-surface);
            border: 1px solid var(--color-border);
            border-radius: var(--radius-lg);
        }}
        .empty-state .empty-icon {{ font-size: 2.25rem; margin-bottom: 10px; line-height: 1; }}
        .empty-state h2 {{ margin: 0 0 6px; font-size: 1.25rem; color: var(--color-text-main); }}
        .empty-state p {{ margin: 0 0 16px; }}
        .empty-state.filtro-vazio {{ padding: 32px 20px; }}
        .empty-state.filtro-vazio p {{ margin: 0 0 16px; font-size: 1rem; color: var(--color-text-main); }}
        .empty-state .empty-icon .icon {{ width: 1em; height: 1em; color: var(--color-text-subtle); }}

        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}

        @media (prefers-reduced-motion: reduce) {{
            *, *::before, *::after {{
                animation-duration: 0.01ms !important;
                transition-duration: 0.01ms !important;
            }}
            .btn-theme:active, .btn-limpar:active {{ transform: none; }}
        }}

        @media (max-width: 640px) {{
            body {{ padding: 12px 12px 32px; }}
            header {{ margin-bottom: 14px; }}
            .header-tools {{ position: static; display: flex; justify-content: flex-end; margin-bottom: 4px; }}
            .meta {{ margin-top: 4px; }}
            .config-info {{ margin-top: 6px; padding: 4px 12px; }}
            .nav-tabs {{ margin-top: 10px; gap: 8px; }}
            .nav-tab {{ padding: 9px 14px; }}
            .summary {{ grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px; }}
            .summary-card {{ padding: 10px 12px; }}
            .summary-number {{ font-size: 1.25rem; }}
            .summary-label {{ margin-top: 2px; }}
            .filter-bar {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px 10px;
                padding: 12px;
                margin-bottom: 14px;
            }}
            .filter-group {{ flex-direction: column; align-items: stretch; gap: 2px; min-width: 0; }}
            .filter-group label {{ font-size: 0.8125rem; line-height: 1.3; }}
            .filter-group input {{ width: 100%; min-width: 0; }}
            .filter-count, .filter-aviso {{ grid-column: 1 / -1; margin-left: 0; text-align: center; }}
            .filter-count:empty {{ display: none; }}
            .pedido-card {{ margin-bottom: 14px; }}
            .pedido-header {{ flex-direction: column; align-items: flex-start; padding: 12px 16px; gap: 6px; }}
            .pedido-right {{ align-items: flex-start; }}
            .servicos-grid {{ grid-template-columns: 1fr; padding: 12px 16px; gap: 8px; }}
            .servico-card {{ padding: 12px; }}
            .servico-nome {{ margin-bottom: 4px; }}
        }}
    </style>
</head>
<body>
    {ICON_SPRITE}
    <div class="container">
        <header>
            <div class="header-tools">
                <button type="button" class="btn-theme" onclick="toggleTheme()" aria-label="Alternar tema claro/escuro">
                    {icone("moon")}{icone("sun")}
                    <span class="tema-escuro">Escuro</span><span class="tema-claro">Claro</span>
                </button>
            </div>
            <h1>{icone("package")} Opções de Frete Correios</h1>
            <div class="meta">Consulta de serviços disponíveis para pedidos em aberto — Gerado em: {data_geracao}</div>
            <div class="config-info">{icone("package")} Pacote padrão: {config.peso_gramas/1000:.1f}kg — {config.comprimento}x{config.largura}x{config.altura} cm — Origem CEP: {config.cep_origem}</div>
            <nav class="nav-tabs" aria-label="Navegação do painel">
                <a href="relatorio_rastreio.html" class="nav-tab">{icone("bar-chart")} Painel Geral</a>
                <a href="opcoes_frete.html" class="nav-tab active" aria-current="page">{icone("package")} Opções de Frete</a>
            </nav>
        </header>

        <div class="summary">
            <div class="summary-card">
                <div class="summary-number num-blue">{total_pedidos}</div>
                <div class="summary-label">Pedidos em Aberto</div>
            </div>
            <div class="summary-card">
                <div class="summary-number num-neutral">{com_opcoes}</div>
                <div class="summary-label">Com Opções Disponíveis</div>
            </div>
        </div>

        <div class="filter-bar">
            <div class="filter-group">
                <label for="valMin">Valor mínimo do pedido (R$)</label>
                <input type="number" id="valMin" min="0" step="any" inputmode="decimal" placeholder="Sem mínimo" oninput="filtrarPorValor()">
            </div>
            <div class="filter-group">
                <label for="valMax">Valor máximo do pedido (R$)</label>
                <input type="number" id="valMax" min="0" step="any" inputmode="decimal" placeholder="Sem limite" oninput="filtrarPorValor()">
            </div>
            <span class="filter-count" id="filterCount" aria-live="polite"></span>
            <p class="filter-aviso" id="filterAviso" aria-live="polite"></p>
        </div>

        {cards_html}
        <div id="filtroVazio" role="status"></div>
    </div>

    <script>
        // Lógica de Tema
        function lerTema() {{
            try {{ return localStorage.getItem('theme') || 'light'; }} catch (e) {{ return 'light'; }}
        }}
        function setTheme(theme) {{
            document.documentElement.setAttribute('data-theme', theme);
            try {{ localStorage.setItem('theme', theme); }} catch (e) {{ /* sem persistência */ }}
        }}
        function toggleTheme() {{
            setTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
        }}
        setTheme(lerTema());

        // Lógica de Filtro
        function filtrarPorValor() {{
            const minVal = parseFloat(document.getElementById('valMin').value) || 0;
            const maxInput = document.getElementById('valMax').value;
            const maxVal = maxInput ? parseFloat(maxInput) : Infinity;
            const aviso = document.getElementById('filterAviso');
            const vazio = document.getElementById('filtroVazio');
            const countSpan = document.getElementById('filterCount');

            const cards = document.querySelectorAll('.pedido-card');
            const invertido = minVal > maxVal;
            let visiveis = 0;

            cards.forEach(card => {{
                const val = parseFloat(card.getAttribute('data-valor')) || 0;
                // Intervalo invertido: não filtra, só avisa
                if (invertido || (val >= minVal && val <= maxVal)) {{
                    card.style.display = '';
                    visiveis++;
                }} else {{
                    card.style.display = 'none';
                }}
            }});

            aviso.textContent = invertido ? 'O mínimo é maior que o máximo.' : '';

            if ((minVal > 0 || maxInput) && !invertido) {{
                countSpan.textContent = `Mostrando ${{visiveis}} de ${{cards.length}}`;
            }} else {{
                countSpan.textContent = '';
            }}

            if (cards.length > 0 && visiveis === 0) {{
                vazio.innerHTML = '<div class="empty-state filtro-vazio">' +
                    '<p>Nenhum pedido neste intervalo de valor.</p>' +
                    '<button type="button" class="btn-limpar" onclick="limparFiltro()">Limpar filtro</button>' +
                    '</div>';
            }} else {{
                vazio.innerHTML = '';
            }}
        }}
        function limparFiltro() {{
            document.getElementById('valMin').value = '';
            document.getElementById('valMax').value = '';
            filtrarPorValor();
            document.getElementById('valMin').focus();
        }}
    </script>
    <script src="alert_frete.js?v={int(time.time())}"></script>
</body>
</html>"""

        # Salva o HTML
        pasta_projeto = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        caminho_html = os.path.join(pasta_projeto, config.relatorio_html)

        with open(caminho_html, mode='w', encoding='utf-8') as f:
            f.write(html_page)

        # Gera o alert_frete.js
        self._gerar_alert_js(pasta_projeto, pedidos_com_prazo_longo)

        logger.info("Relatório de frete salvo em '%s'", caminho_html)
        print(f"\nSucesso! Página de opções de frete salva em '{caminho_html}'.")

        return caminho_html

    def _gerar_alert_js(self, pasta_projeto: str, pedidos_com_prazo_longo: list[str]) -> None:
        """Gera o arquivo alert_frete.js com alertas de prazo longo.

        O modal segue o DESIGN.md (tokens, ícone SVG de traço fino, tema claro/escuro)
        e é injetado por JS em qualquer página, por isso carrega seus próprios estilos.
        """
        js_content = _ALERT_JS_TEMPLATE.replace("__PEDIDOS__", str(pedidos_com_prazo_longo))

        caminho_js = os.path.join(pasta_projeto, "alert_frete.js")
        with open(caminho_js, mode='w', encoding='utf-8') as f:
            f.write(js_content)


# Modal de aviso de prazo longo (alert_frete.js). Texto bruto: sem f-string, o marcador
# __PEDIDOS__ é trocado pela lista de pedidos. Cores = tokens do DESIGN.md, redefinidos
# localmente porque o script roda em qualquer página.
_ALERT_JS_TEMPLATE = r"""(function() {
    const pedidosComPrazo = __PEDIDOS__;
    if (pedidosComPrazo.length === 0) { return; }

    const cacheKey = "alerta_prazo_v2_" + pedidosComPrazo.join("_");
    let jaAvisado = false;
    try { jaAvisado = !!localStorage.getItem(cacheKey); } catch (e) { jaAvisado = false; }
    if (jaAvisado) { return; }

    const mensagem = "Os pedidos " + pedidosComPrazo.join(", ") +
        " possuem prazos de entrega superiores a 3 dias úteis.";

    // 1. Modal visual (tema atual da pagina, com prefers-color-scheme como reserva)
    let temaEscuro = false;
    try {
        const tema = document.documentElement.getAttribute('data-theme');
        temaEscuro = tema ? tema === 'dark'
            : !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
    } catch (e) { temaEscuro = false; }

    const estilo = document.createElement('style');
    estilo.textContent = [
        '.af-overlay{--af-surface:#ffffff;--af-border:#64748b;--af-text:#0f172a;--af-muted:#475569;',
        '--af-warn:#92400e;--af-warn-bg:#fef3c7;--af-primary:#2563eb;--af-primary-hover:#1d4ed8;',
        '--af-on-primary:#ffffff;--af-hover:#f1f5f9;',
        'position:fixed;inset:0;z-index:99999;display:flex;align-items:center;justify-content:center;',
        'padding:16px;background:rgba(15,23,42,0.55);backdrop-filter:blur(4px);',
        'font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}',
        '.af-overlay.af-dark{--af-surface:#151c2c;--af-border:#64748b;--af-text:#f8fafc;--af-muted:#b6c2d2;',
        '--af-warn:#fbbf24;--af-warn-bg:rgba(251,191,36,0.15);--af-hover:#192237;}',
        '.af-modal{box-sizing:border-box;width:100%;max-width:420px;max-height:100%;overflow:auto;',
        'padding:28px 24px 24px;text-align:center;background:var(--af-surface);color:var(--af-text);',
        'border:1px solid var(--af-border);border-radius:16px;',
        'box-shadow:0 10px 15px -3px rgba(0,0,0,0.3),0 4px 6px -4px rgba(0,0,0,0.2);}',
        '.af-icon{display:inline-flex;align-items:center;justify-content:center;width:56px;height:56px;',
        'margin-bottom:14px;border-radius:9999px;background:var(--af-warn-bg);color:var(--af-warn);}',
        '.af-icon svg{width:28px;height:28px;fill:none;stroke:currentColor;stroke-width:1.75;',
        'stroke-linecap:round;stroke-linejoin:round;}',
        '.af-title{margin:0 0 8px;font-size:1.25rem;font-weight:700;line-height:1.6;color:var(--af-text);}',
        '.af-text{margin:0 0 22px;font-size:1rem;line-height:1.6;color:var(--af-muted);}',
        '.af-actions{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;}',
        '.af-btn{box-sizing:border-box;min-height:44px;min-width:44px;padding:10px 22px;',
        'border-radius:9999px;font:inherit;font-size:0.875rem;font-weight:700;cursor:pointer;',
        'border:1px solid var(--af-border);background:transparent;color:var(--af-text);}',
        '.af-btn:hover{background:var(--af-hover);}',
        '.af-btn-primary{border-color:var(--af-primary);background:var(--af-primary);color:var(--af-on-primary);}',
        '.af-btn-primary:hover{background:var(--af-primary-hover);border-color:var(--af-primary-hover);}',
        '.af-btn:focus-visible{outline:2px solid var(--af-primary);outline-offset:3px;}',
        '.af-dark .af-btn:focus-visible{outline-color:#93c5fd;}',
        '@media (prefers-reduced-motion:no-preference){',
        '.af-overlay{animation:af-fade 0.18s ease-out;}',
        '.af-modal{animation:af-pop 0.18s ease-out;}}',
        '@keyframes af-fade{from{opacity:0}to{opacity:1}}',
        '@keyframes af-pop{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}'
    ].join('');
    document.head.appendChild(estilo);

    const elementoAnterior = document.activeElement;

    const overlay = document.createElement('div');
    overlay.className = 'af-overlay' + (temaEscuro ? ' af-dark' : '');

    const modal = document.createElement('div');
    modal.className = 'af-modal';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', 'af-titulo');
    modal.setAttribute('aria-describedby', 'af-texto');

    const icon = document.createElement('div');
    icon.className = 'af-icon';
    icon.setAttribute('aria-hidden', 'true');
    icon.innerHTML = '<svg viewBox="0 0 24 24" focusable="false" aria-hidden="true">' +
        '<path d="M12 3.5L2.5 20h19L12 3.5z"/><path d="M12 10v4M12 17h.01"/></svg>';

    const title = document.createElement('h2');
    title.id = 'af-titulo';
    title.className = 'af-title';
    title.textContent = 'Atenção aos prazos';

    const text = document.createElement('p');
    text.id = 'af-texto';
    text.className = 'af-text';
    text.textContent = mensagem;

    const btnWrap = document.createElement('div');
    btnWrap.className = 'af-actions';

    const btnFechar = document.createElement('button');
    btnFechar.type = 'button';
    btnFechar.className = 'af-btn';
    btnFechar.textContent = 'Fechar';

    const btnIr = document.createElement('button');
    btnIr.type = 'button';
    btnIr.className = 'af-btn af-btn-primary';
    btnIr.textContent = 'Ver opções de frete';

    function fechar() {
        document.removeEventListener('keydown', aoTeclar, true);
        if (overlay.parentNode) { overlay.parentNode.removeChild(overlay); }
        if (estilo.parentNode) { estilo.parentNode.removeChild(estilo); }
        if (elementoAnterior && typeof elementoAnterior.focus === 'function' &&
            document.contains(elementoAnterior)) {
            elementoAnterior.focus();
        }
    }

    function aoTeclar(ev) {
        if (ev.key === 'Escape') {
            ev.preventDefault();
            fechar();
        } else if (ev.key === 'Tab') {
            // mantem o foco dentro do dialogo
            const alvos = [btnFechar, btnIr];
            const i = alvos.indexOf(document.activeElement);
            ev.preventDefault();
            if (ev.shiftKey) {
                alvos[i <= 0 ? alvos.length - 1 : i - 1].focus();
            } else {
                alvos[i === -1 || i === alvos.length - 1 ? 0 : i + 1].focus();
            }
        }
    }

    btnFechar.addEventListener('click', fechar);
    btnIr.addEventListener('click', function() {
        window.location.href = 'opcoes_frete.html';
    });

    btnWrap.appendChild(btnFechar);
    btnWrap.appendChild(btnIr);
    modal.appendChild(icon);
    modal.appendChild(title);
    modal.appendChild(text);
    modal.appendChild(btnWrap);
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    document.addEventListener('keydown', aoTeclar, true);
    btnFechar.focus();

    // 2. Mostrar a Notificacao do Windows / Navegador
    if ("Notification" in window) {
        function showNotif() {
            let n = new Notification("Alerta de Frete: Prazo Longo (>3 dias)", {
                body: mensagem
            });
            n.onclick = function() {
                window.location.href = "opcoes_frete.html";
            };
        }

        try {
            if (Notification.permission === "granted") {
                showNotif();
            } else if (Notification.permission !== "denied") {
                Notification.requestPermission().then(function(p) {
                    if (p === "granted") showNotif();
                });
            }
        } catch (e) { /* notificacao indisponivel */ }
    }

    // Registrar que ja avisamos sobre esse grupo de pedidos
    try { localStorage.setItem(cacheKey, "true"); } catch (e) { /* sem persistencia */ }
})();
"""
