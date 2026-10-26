"""Geração do relatório HTML de opções de frete.

Responsabilidade exclusiva: montar e salvar os arquivos de saída.
NÃO consulta APIs, NÃO decide qual frete recomendar.

O HTML e CSS são idênticos ao gerado anteriormente por consulta_frete.py
para manter compatibilidade com o painel e alert_frete.js.
"""
import logging
import os
import time
from typing import Any

from correios.icons import ICON_SPRITE, icone

from .config import FreteConfig

logger = logging.getLogger("frete.report")


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

            servicos_html = ""
            for cod in config.servicos.keys():
                nome = config.servicos[cod]
                info = pedido.get("servicos", {}).get(cod, {"disponivel": False})

                if info["disponivel"]:
                    preco_display = info.get("preco_fmt", "—")
                    prazo_display = f'{info["prazo"]} dias úteis' if info.get("prazo") else "—"
                    if info.get("prazo") and info["prazo"] > 3:
                        if str(pedido['numero']) not in pedidos_com_prazo_longo:
                            pedidos_com_prazo_longo.append(str(pedido['numero']))

                    msg_prazo_html = ""
                    if info.get("msg_prazo"):
                        msg_prazo_html = f'\n                    <div class="servico-msg-prazo" title="{info["msg_prazo"]}">{icone("alert-triangle")} {info["msg_prazo"]}</div>'

                    servicos_html += f"""
                <div class="servico-card disponivel">
                    <div class="servico-nome">{nome}</div>
                    <div class="servico-preco">{preco_display}</div>
                    <div class="servico-prazo">{icone("clock")} {prazo_display}</div>{msg_prazo_html}
                </div>"""
                else:
                    servicos_html += f"""
                <div class="servico-card indisponivel">
                    <div class="servico-nome">{nome}</div>
                    <div class="servico-status">Indisponível</div>
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
            <div class="emoji">{icone("inbox")}</div>
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
            --color-badge-fg: #1d4ed8;
            --color-badge-bg: #eff6ff;
            --color-badge-border: #bfdbfe;
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
            font-size: 2.25rem;
            font-weight: 800;
            letter-spacing: -0.025em;
            color: var(--color-primary);
        }}
        [data-theme="dark"] h1 {{ color: var(--color-link); }}
        .meta {{ color: var(--color-text-muted); margin-top: 8px; font-size: 0.9rem; }}
        .config-info {{
            display: inline-block;
            margin-top: 10px;
            padding: 6px 16px;
            background: var(--color-header-bg);
            border: 1px solid var(--color-border);
            border-radius: var(--radius-md);
            font-size: 0.85rem;
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

        .back-link {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 22px;
            background: var(--color-primary);
            color: #ffffff;
            text-decoration: none;
            border-radius: var(--radius-full);
            font-weight: 700;
            font-size: 0.9rem;
            margin-top: 16px;
            min-height: 44px;
            box-shadow: var(--shadow-sm);
            transition: var(--transition);
        }}
        .back-link:hover {{ background: var(--color-primary-hover); transform: translateY(-2px); box-shadow: var(--shadow-md); }}

        /* Ferramentas do cabeçalho: o tema fica no topo, fora do conteúdo */
        .header-tools {{ position: absolute; top: 0; right: 0; }}
        .btn-theme {{
            background: var(--color-surface);
            color: var(--color-text-main);
            border: 1px solid var(--color-border);
            padding: 10px 18px;
            min-height: 44px;
            font: inherit;
            font-weight: 600;
            font-size: 0.9rem;
            border-radius: var(--radius-full);
            cursor: pointer;
            box-shadow: var(--shadow-sm);
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: var(--transition);
        }}
        .btn-theme:hover {{
            background: var(--color-surface-hover);
            border-color: var(--color-primary);
            color: var(--color-primary);
        }}
        [data-theme="dark"] .btn-theme:hover {{ color: var(--color-link); }}
        .btn-theme:active {{ transform: scale(0.97); }}
        /* Mostra o tema de destino: lua/"Escuro" no claro, sol/"Claro" no escuro */
        .btn-theme .icon-sun, .btn-theme .tema-claro {{ display: none; }}
        [data-theme="dark"] .btn-theme .icon-sun, [data-theme="dark"] .btn-theme .tema-claro {{ display: inline-block; }}
        [data-theme="dark"] .btn-theme .icon-moon, [data-theme="dark"] .btn-theme .tema-escuro {{ display: none; }}

        .back-link:focus-visible, .btn-theme:focus-visible {{
            outline: 2px solid var(--color-primary);
            outline-offset: 3px;
        }}
        [data-theme="dark"] .back-link:focus-visible, [data-theme="dark"] .btn-theme:focus-visible {{ outline-color: var(--color-link); }}

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
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--color-text-muted);
        }}
        .filter-group input {{
            padding: 8px 12px;
            border: 1px solid var(--color-border);
            border-radius: var(--radius-md);
            background: var(--color-bg);
            color: var(--color-text-main);
            font: inherit;
            font-size: 0.95rem;
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
            font-size: 0.9rem;
            color: var(--color-text-muted);
            font-weight: 600;
        }}

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
        .summary-label {{ font-size: 0.78rem; color: var(--color-text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 6px; }}
        .num-blue {{ color: var(--color-primary); }}
        [data-theme="dark"] .num-blue {{ color: var(--color-link); }}
        .num-green {{ color: var(--color-success); }}

        /* Pedido Cards */
        .pedido-card {{
            background: var(--color-surface);
            border: 1px solid var(--color-border);
            border-radius: 12px;
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
        .pedido-numero {{ font-weight: 700; font-size: 1.2rem; }}
        .pedido-valor {{ font-size: 0.9rem; font-weight: 600; color: var(--color-success); margin-left: 8px; }}
        .pedido-cliente {{ color: var(--color-text-muted); font-size: 0.9rem; }}
        .pedido-right {{ display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }}
        .pedido-badge {{
            background: var(--color-badge-bg);
            color: var(--color-badge-fg);
            border: 1px solid var(--color-badge-border);
            padding: 2px 10px;
            border-radius: 99px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .pedido-destino {{
            color: var(--color-text-muted);
            font-size: 0.85rem;
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
            background: var(--color-success-bg);
            border-color: var(--color-success-border);
        }}
        .servico-card.disponivel:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
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
            font-size: 1.4rem;
            font-weight: 800;
            color: var(--color-success);
            margin-bottom: 4px;
        }}
        .servico-prazo {{
            font-size: 0.85rem;
            color: var(--color-text-muted);
            font-weight: 500;
        }}
        .servico-status {{
            color: var(--color-text-muted);
            font-size: 0.85rem;
        }}
        .servico-msg-prazo {{
            font-size: 0.8rem;
            color: var(--color-warning);
            margin-top: 8px;
            padding: 6px 10px;
            background: var(--color-warning-bg);
            border: 1px solid var(--color-warning-border);
            border-radius: 6px;
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
        .empty-state .emoji {{ font-size: 3rem; margin-bottom: 10px; line-height: 1; }}
        .empty-state .emoji .icon {{ width: 1em; height: 1em; color: var(--color-text-subtle); }}

        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}

        @media (prefers-reduced-motion: reduce) {{
            *, *::before, *::after {{
                animation-duration: 0.01ms !important;
                transition-duration: 0.01ms !important;
            }}
            .back-link:hover, .btn-theme:active, .servico-card.disponivel:hover {{ transform: none; }}
        }}

        @media (max-width: 640px) {{
            body {{ padding: 16px 12px 40px; }}
            .header-tools {{ position: static; display: flex; justify-content: flex-end; margin-bottom: 8px; }}
            h1 {{ font-size: 1.75rem; }}
            .filter-bar {{ flex-direction: column; align-items: stretch; padding: 16px; }}
            .filter-group {{ justify-content: space-between; }}
            .filter-group input {{ flex: 1; max-width: 160px; }}
            .filter-count {{ margin-left: 0; text-align: center; }}
            .pedido-header {{ flex-direction: column; align-items: flex-start; padding: 16px; }}
            .pedido-right {{ align-items: flex-start; }}
            .servicos-grid {{ grid-template-columns: 1fr; padding: 16px; }}
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
            <br>
            <a href="relatorio_rastreio.html" class="back-link">← Voltar ao Painel Principal</a>
        </header>

        <div class="summary">
            <div class="summary-card">
                <div class="summary-number num-blue">{total_pedidos}</div>
                <div class="summary-label">Pedidos em Aberto</div>
            </div>
            <div class="summary-card">
                <div class="summary-number num-green">{com_opcoes}</div>
                <div class="summary-label">Com Opções Disponíveis</div>
            </div>
        </div>

        <div class="filter-bar">
            <div class="filter-group">
                <label for="valMin">Valor Mínimo (R$):</label>
                <input type="number" id="valMin" placeholder="0" oninput="filtrarPorValor()">
            </div>
            <div class="filter-group">
                <label for="valMax">Valor Máximo (R$):</label>
                <input type="number" id="valMax" placeholder="Sem limite" oninput="filtrarPorValor()">
            </div>
            <span class="filter-count" id="filterCount" aria-live="polite"></span>
        </div>

        {cards_html}
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
            
            const cards = document.querySelectorAll('.pedido-card');
            let visiveis = 0;
            
            cards.forEach(card => {{
                const val = parseFloat(card.getAttribute('data-valor')) || 0;
                if (val >= minVal && val <= maxVal) {{
                    card.style.display = '';
                    visiveis++;
                }} else {{
                    card.style.display = 'none';
                }}
            }});
            
            const countSpan = document.getElementById('filterCount');
            if (minVal > 0 || maxInput) {{
                countSpan.textContent = `Mostrando ${{visiveis}} de ${{cards.length}}`;
            }} else {{
                countSpan.textContent = '';
            }}
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
        """Gera o arquivo alert_frete.js com alertas de prazo longo."""
        js_content = f"""(function() {{
    const pedidosComPrazo = {str(pedidos_com_prazo_longo)};
    if (pedidosComPrazo.length > 0) {{
        const cacheKey = "alerta_prazo_v2_" + pedidosComPrazo.join("_");
        if (!localStorage.getItem(cacheKey)) {{
            
            // 1. Mostrar o Modal Visual no Centro da Tela
            const overlay = document.createElement('div');
            overlay.style.position = 'fixed';
            overlay.style.top = '0';
            overlay.style.left = '0';
            overlay.style.width = '100vw';
            overlay.style.height = '100vh';
            overlay.style.backgroundColor = 'rgba(0,0,0,0.5)';
            overlay.style.display = 'flex';
            overlay.style.alignItems = 'center';
            overlay.style.justifyContent = 'center';
            overlay.style.zIndex = '99999';
            overlay.style.backdropFilter = 'blur(4px)';

            const modal = document.createElement('div');
            modal.style.backgroundColor = 'var(--card-bg, #ffffff)';
            modal.style.padding = '30px';
            modal.style.borderRadius = '16px';
            modal.style.boxShadow = '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)';
            modal.style.maxWidth = '400px';
            modal.style.textAlign = 'center';
            modal.style.color = 'var(--text-main, #1e293b)';
            modal.style.fontFamily = 'system-ui, -apple-system, sans-serif';

            const icon = document.createElement('div');
            icon.innerHTML = '&#9888;&#65039;'; // Unicode HTML Entity for Warning sign to avoid encoding bugs
            icon.style.fontSize = '3rem';
            icon.style.marginBottom = '15px';

            const title = document.createElement('h2');
            title.innerText = 'Atencao aos Prazos';
            title.style.margin = '0 0 10px 0';
            title.style.fontSize = '1.4rem';

            const text = document.createElement('p');
            text.innerText = "Os pedidos " + pedidosComPrazo.join(", ") + " possuem prazos de entrega superiores a 3 dias uteis.";
            text.style.margin = '0 0 20px 0';
            text.style.lineHeight = '1.5';
            text.style.color = 'var(--text-sub, #64748b)';

            const btnWrap = document.createElement('div');
            btnWrap.style.display = 'flex';
            btnWrap.style.gap = '10px';
            btnWrap.style.justifyContent = 'center';

            const btnFechar = document.createElement('button');
            btnFechar.innerText = 'Fechar';
            btnFechar.style.padding = '10px 20px';
            btnFechar.style.border = '1px solid var(--border, #e2e8f0)';
            btnFechar.style.borderRadius = '8px';
            btnFechar.style.backgroundColor = 'transparent';
            btnFechar.style.color = 'var(--text-main, #1e293b)';
            btnFechar.style.cursor = 'pointer';
            btnFechar.onclick = function() {{
                document.body.removeChild(overlay);
            }};

            const btnIr = document.createElement('button');
            btnIr.innerText = 'Ver Opcoes de Frete';
            btnIr.style.padding = '10px 20px';
            btnIr.style.border = 'none';
            btnIr.style.borderRadius = '8px';
            btnIr.style.backgroundColor = '#ea580c';
            btnIr.style.color = 'white';
            btnIr.style.fontWeight = 'bold';
            btnIr.style.cursor = 'pointer';
            btnIr.onclick = function() {{
                window.location.href = 'opcoes_frete.html';
            }};

            btnWrap.appendChild(btnFechar);
            btnWrap.appendChild(btnIr);

            modal.appendChild(icon);
            modal.appendChild(title);
            modal.appendChild(text);
            modal.appendChild(btnWrap);
            overlay.appendChild(modal);

            document.body.appendChild(overlay);

            // 2. Mostrar a Notificacao do Windows / Navegador
            if ("Notification" in window) {{
                function showNotif() {{
                    let n = new Notification("Alerta de Frete: Prazo Longo (>3 dias)", {{
                        body: "Os pedidos " + pedidosComPrazo.join(", ") + " possuem prazos superiores a 3 dias uteis.",
                        icon: "https://cdn-icons-png.flaticon.com/512/1055/1055065.png"
                    }});
                    n.onclick = function() {{
                        window.location.href = "opcoes_frete.html";
                    }};
                }}
                
                if (Notification.permission === "granted") {{
                    showNotif();
                }} else if (Notification.permission !== "denied") {{
                    Notification.requestPermission().then(function(p) {{
                        if (p === "granted") showNotif();
                    }});
                }}
            }}

            // Registrar que ja avisamos sobre esse grupo de pedidos
            localStorage.setItem(cacheKey, "true");
        }}
    }}
}})();"""

        caminho_js = os.path.join(pasta_projeto, "alert_frete.js")
        with open(caminho_js, mode='w', encoding='utf-8') as f:
            f.write(js_content)
