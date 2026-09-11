"""Geração do relatório HTML de opções de frete.

Responsabilidade exclusiva: montar e salvar os arquivos de saída.
NÃO consulta APIs, NÃO decide qual frete recomendar.

O HTML e CSS são idênticos ao gerado anteriormente por consulta_frete.py
para manter compatibilidade com o painel e alert_frete.js.
"""
import logging
import os
import time
from typing import Any, Dict, List, Optional

from .config import FreteConfig

logger = logging.getLogger("frete.report")


class FreteReportGenerator:
    """Gera o HTML de opções de frete e o script de alertas."""

    def __init__(self, config: Optional[FreteConfig] = None):
        self.config = config or FreteConfig()

    def gerar_html(
        self,
        pedidos_com_frete: List[Dict[str, Any]],
        alertas_extras: Optional[List[str]] = None,
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

        tem_prazo_longo = False
        pedidos_com_prazo_longo = []

        # Inclui alertas de pedidos Motoboy/Retirada com prazo longo (não exibidos nos cards)
        if alertas_extras:
            pedidos_com_prazo_longo.extend(alertas_extras)
            if alertas_extras:
                tem_prazo_longo = True

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
                        tem_prazo_longo = True
                        if str(pedido['numero']) not in pedidos_com_prazo_longo:
                            pedidos_com_prazo_longo.append(str(pedido['numero']))

                    msg_prazo_html = ""
                    if info.get("msg_prazo"):
                        msg_prazo_html = f'\n                    <div class="servico-msg-prazo" title="{info["msg_prazo"]}">⚠️ {info["msg_prazo"]}</div>'

                    servicos_html += f"""
                <div class="servico-card disponivel">
                    <div class="servico-nome">{nome}</div>
                    <div class="servico-preco">{preco_display}</div>
                    <div class="servico-prazo">📅 {prazo_display}</div>{msg_prazo_html}
                </div>"""
                else:
                    erro = info.get("erro", "Indisponível")
                    servicos_html += f"""
                <div class="servico-card indisponivel">
                    <div class="servico-nome">{nome}</div>
                    <div class="servico-status">Indisponível</div>
                </div>"""

            cards_html += f"""
        <div class="pedido-card" data-valor="{valor_float}">
            <div class="pedido-header">
                <div class="pedido-left">
                    <span class="pedido-numero">Pedido #{pedido['numero']} <span style="font-size: 0.9rem; font-weight: normal; color: #16a34a; margin-left: 8px;">{valor_fmt}</span></span>
                    <span class="pedido-cliente">{pedido.get('nome_cliente', '—')}</span>
                </div>
                <div class="pedido-right">
                    <span class="pedido-badge">{pedido['situacao']}</span>
                    <span class="pedido-destino">📍 {pedido.get('destino_label', '—')} — CEP {pedido.get('cep_destino', '—')}</span>
                </div>
            </div>
            <div class="servicos-grid">
                {servicos_html}
            </div>
        </div>"""

        # Estado vazio
        if not pedidos_com_frete:
            cards_html = """
        <div class="empty-state">
            <div class="emoji">📭</div>
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
            --primary: #2563eb;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #1e293b;
            --text-sub: #64748b;
            --border: #e2e8f0;
            --green: #16a34a;
            --red: #dc2626;
        }}
        [data-theme="dark"] {{
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text-main: #f1f5f9;
            --text-sub: #94a3b8;
            --border: #334155;
        }}
        body {{
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text-main);
            margin: 0;
            padding: 20px;
            line-height: 1.5;
            transition: background-color 0.3s ease, color 0.3s ease;
        }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        header {{ text-align: center; margin-bottom: 30px; }}
        h1 {{
            margin: 0;
            font-size: 2.2rem;
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .meta {{ color: var(--text-sub); margin-top: 8px; }}
        .config-info {{
            display: inline-block;
            margin-top: 10px;
            padding: 6px 16px;
            background: var(--border);
            border-radius: 8px;
            font-size: 0.82rem;
            color: var(--text-sub);
        }}

        .back-link {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 22px;
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: white;
            text-decoration: none;
            border-radius: 99px;
            font-weight: 600;
            font-size: 0.9rem;
            margin-top: 14px;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
            transition: all 0.2s ease;
        }}
        .back-link:hover {{ transform: translateY(-2px); box-shadow: 0 8px 20px rgba(37, 99, 235, 0.45); }}

        .btn-theme {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: var(--card-bg);
            color: var(--text-main);
            border: 2px solid var(--border);
            padding: 8px 16px;
            border-radius: 99px;
            font-weight: 600;
            cursor: pointer;
            z-index: 1000;
            transition: all 0.2s ease;
        }}
        .btn-theme:hover {{ transform: translateY(-2px); }}

        /* Filter Bar */
        .filter-bar {{
            display: flex;
            align-items: center;
            gap: 16px;
            background: var(--card-bg);
            padding: 16px 24px;
            border-radius: 14px;
            border: 1px solid var(--border);
            margin-bottom: 24px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.06);
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
            color: var(--text-sub);
        }}
        .filter-group input {{
            padding: 8px 12px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--bg);
            color: var(--text-main);
            font-size: 0.95rem;
            width: 120px;
            outline: none;
            transition: border-color 0.2s;
        }}
        .filter-group input:focus {{
            border-color: var(--primary);
        }}
        .filter-count {{
            margin-left: auto;
            font-size: 0.9rem;
            color: var(--text-sub);
            font-weight: 600;
        }}

        /* Summary Cards */
        .summary {{
            display: flex;
            gap: 16px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }}
        .summary-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px 28px;
            flex: 1;
            min-width: 180px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.06);
            text-align: center;
        }}
        .summary-number {{ font-size: 2.5rem; font-weight: 800; line-height: 1.2; }}
        .summary-label {{ font-size: 0.82rem; color: var(--text-sub); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }}
        .num-blue {{ color: #2563eb; }}
        .num-green {{ color: #16a34a; }}

        /* Pedido Cards */
        .pedido-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 14px;
            margin-bottom: 20px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.06);
            animation: fadeIn 0.4s ease forwards;
        }}
        .pedido-header {{
            padding: 18px 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .pedido-left {{ display: flex; flex-direction: column; gap: 4px; }}
        .pedido-numero {{ font-weight: 800; font-size: 1.15rem; }}
        .pedido-cliente {{ color: var(--text-sub); font-size: 0.9rem; }}
        .pedido-right {{ display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }}
        .pedido-badge {{
            background: linear-gradient(135deg, #eff6ff, #bfdbfe);
            color: #2563eb;
            padding: 3px 12px;
            border-radius: 99px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
        }}
        [data-theme="dark"] .pedido-badge {{
            background: linear-gradient(135deg, #1e3a5f, #1e40af);
            color: #93c5fd;
        }}
        .pedido-destino {{
            color: var(--text-sub);
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
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            transition: all 0.2s ease;
        }}
        .servico-card.disponivel {{
            background: linear-gradient(135deg, #f0fdf4, #dcfce7);
            border-color: #bbf7d0;
        }}
        [data-theme="dark"] .servico-card.disponivel {{
            background: linear-gradient(135deg, #052e16, #14532d);
            border-color: #166534;
        }}
        .servico-card.disponivel:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(22, 163, 74, 0.2);
        }}
        .servico-card.indisponivel {{
            background: var(--bg);
            opacity: 0.6;
        }}
        .servico-nome {{
            font-weight: 800;
            font-size: 1rem;
            margin-bottom: 8px;
            color: var(--text-main);
        }}
        .servico-preco {{
            font-size: 1.4rem;
            font-weight: 800;
            color: var(--green);
            margin-bottom: 4px;
        }}
        [data-theme="dark"] .servico-preco {{
            color: #4ade80;
        }}
        .servico-prazo {{
            font-size: 0.82rem;
            color: var(--text-sub);
            font-weight: 500;
        }}
        .servico-status {{
            color: var(--text-sub);
            font-size: 0.85rem;
            font-style: italic;
        }}
        .servico-msg-prazo {{
            font-size: 0.72rem;
            color: #d97706;
            margin-top: 8px;
            padding: 6px 10px;
            background: rgba(217, 119, 6, 0.08);
            border: 1px solid rgba(217, 119, 6, 0.15);
            border-radius: 6px;
            text-align: left;
            word-break: break-word;
            line-height: 1.3;
        }}
        [data-theme="dark"] .servico-msg-prazo {{
            color: #f59e0b;
            background: rgba(245, 158, 11, 0.08);
            border-color: rgba(245, 158, 11, 0.15);
        }}

        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: var(--text-sub);
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 14px;
        }}
        .empty-state .emoji {{ font-size: 3rem; margin-bottom: 10px; }}

        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .summary-card {{ animation: fadeIn 0.4s ease forwards; }}
        .summary-card:nth-child(2) {{ animation-delay: 0.1s; }}

        @media (max-width: 600px) {{
            .pedido-header {{ flex-direction: column; align-items: flex-start; }}
            .pedido-right {{ align-items: flex-start; }}
            .servicos-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <button class="btn-theme" onclick="toggleTheme()">🌓 Tema</button>
    <div class="container">
        <header>
            <h1>📦 Opções de Frete Correios</h1>
            <div class="meta">Consulta de serviços disponíveis para pedidos em aberto — Gerado em: {data_geracao}</div>
            <div class="config-info">📐 Pacote padrão: {config.peso_gramas/1000:.1f}kg — {config.comprimento}x{config.largura}x{config.altura} cm — Origem CEP: {config.cep_origem}</div>
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
            <span class="filter-count" id="filterCount"></span>
        </div>

        {cards_html}
    </div>

    <script>
        // Lógica de Tema
        function setTheme(theme) {{
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
        }}
        function toggleTheme() {{
            const current = localStorage.getItem('theme') || 'light';
            setTheme(current === 'light' ? 'dark' : 'light');
        }}
        setTheme(localStorage.getItem('theme') || 'light');

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

    def _gerar_alert_js(self, pasta_projeto: str, pedidos_com_prazo_longo: List[str]) -> None:
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
