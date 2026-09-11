"""Gerador de dados sintéticos de demonstração para portfólio e testes locais.

Permite testar o painel completo (filtros, busca instantânea, Dark Mode, timeline
e relatórios de atrasados e frete) sem requerer credenciais ativas do Tiny ERP
ou dos Correios.
"""
import time
from pathlib import Path

# Obtém a raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent


def gerar_dados_demonstracao(pasta_destino: Path | str | None = None) -> dict[str, str]:
    """Gera arquivos HTML com dados simulados realistas para exibição imediata.

    Retorna um dicionário com os caminhos dos arquivos gerados.
    """
    if pasta_destino is None:
        destino = BASE_DIR
    else:
        destino = Path(pasta_destino)

    versao_cache = int(time.time())
    data_geracao = time.strftime("%d/%m/%Y %H:%M:%S")

    # -------------------------------------------------------------------------
    # 1. Dashboard de Resumo
    # -------------------------------------------------------------------------
    dashboard_html = """
        <div class="dashboard">
            <div class="dash-card dash-clickable" onclick="filterOrders('nao_enviado')" data-filter="nao_enviado">
                <div class="dash-icon dash-icon-orange">📭</div>
                <div class="dash-info">
                    <span class="dash-number dash-number-orange">2</span>
                    <span class="dash-label">Não Enviados</span>
                </div>
            </div>
            <div class="dash-card dash-clickable" onclick="filterOrders('em_transito')" data-filter="em_transito">
                <div class="dash-icon dash-icon-blue">🚚</div>
                <div class="dash-info">
                    <span class="dash-number dash-number-blue">4</span>
                    <span class="dash-label">Em Trânsito</span>
                </div>
            </div>
            <div class="dash-card dash-clickable" onclick="filterOrders('entregue')" data-filter="entregue">
                <div class="dash-icon dash-icon-green">✅</div>
                <div class="dash-info">
                    <span class="dash-number dash-number-green">2</span>
                    <span class="dash-label">Entregues</span>
                </div>
            </div>
            <div class="dash-card dash-clickable" onclick="filterOrders('devolvido')" data-filter="devolvido">
                <div class="dash-icon dash-icon-purple">↩️</div>
                <div class="dash-info">
                    <span class="dash-number dash-number-purple">1</span>
                    <span class="dash-label">Devolvidos</span>
                </div>
            </div>
        </div>
        <div id="filterBanner" class="filter-banner">
            <span class="filter-banner-text" id="filterBannerText"></span>
            <button class="filter-banner-close" onclick="filterOrders(null)">✕ Mostrar Todos</button>
        </div>
    """

    # -------------------------------------------------------------------------
    # 2. Pedidos Demonstrativos (10 pedidos com situações variadas)
    # -------------------------------------------------------------------------
    orders = [
        {
            "pedido": "41763",
            "rastreio": "AD896561063BR",
            "cliente": "Mariana Souza",
            "situacao": "Enviado",
            "status": "em_transito",
            "eventos": [
                {
                    "data": "11/09/2026 10:52",
                    "badge": '<span class="badge badge-yellow">SAIU PARA ENTREGA</span>',
                    "desc": "Objeto saiu para entrega ao destinatário",
                    "local": "CABO FRIO/RJ",
                    "detalhe": "É preciso ter alguém no endereço para receber o carteiro",
                    "class": "status-warning",
                },
                {
                    "data": "10/09/2026 10:16",
                    "badge": "",
                    "desc": "Objeto em transferência - por favor aguarde",
                    "local": "RIO DE JANEIRO/RJ",
                    "detalhe": "",
                    "class": "",
                },
                {
                    "data": "09/09/2026 15:43",
                    "badge": '<span class="badge badge-green">POSTADO</span>',
                    "desc": "Objeto postado após o horário limite",
                    "local": "SAO PAULO/SP",
                    "detalhe": "",
                    "class": "",
                },
            ],
        },
        {
            "pedido": "41755",
            "rastreio": "NL123456789BR",
            "cliente": "Carlos Eduardo Lima",
            "situacao": "Entregue",
            "status": "entregue",
            "eventos": [
                {
                    "data": "10/09/2026 16:30",
                    "badge": '<span class="badge badge-green">ENTREGUE</span>',
                    "desc": "Objeto entregue ao destinatário",
                    "local": "CURITIBA/PR",
                    "detalhe": "",
                    "class": "",
                },
                {
                    "data": "09/09/2026 09:20",
                    "badge": "",
                    "desc": "Objeto em transferência",
                    "local": "SAO PAULO/SP",
                    "detalhe": "",
                    "class": "",
                },
            ],
        },
        {
            "pedido": "41740",
            "rastreio": "NL987654321BR",
            "cliente": "Fernanda Oliveira",
            "situacao": "Enviado",
            "status": "em_transito",
            "eventos": [
                {
                    "data": "11/09/2026 08:15",
                    "badge": "",
                    "desc": "Objeto em transferência para Centro de Distribuição",
                    "local": "BELO HORIZONTE/MG",
                    "detalhe": "",
                    "class": "",
                },
                {
                    "data": "09/09/2026 14:00",
                    "badge": '<span class="badge badge-green">POSTADO</span>',
                    "desc": "Objeto postado",
                    "local": "SAO PAULO/SP",
                    "detalhe": "",
                    "class": "",
                },
            ],
        },
        {
            "pedido": "41732",
            "rastreio": "BR112233445BR",
            "cliente": "Roberto Albuquerque",
            "situacao": "Atrasado",
            "status": "atrasado",
            "eventos": [
                {
                    "data": "05/09/2026 11:00",
                    "badge": '<span class="badge badge-yellow">ATRASO DETECTADO</span>',
                    "desc": "Objeto em transferência - trânsito lento",
                    "local": "RECIFE/PE",
                    "detalhe": "Prazo prometido de entrega expirado há 5 dias",
                    "class": "status-warning",
                },
                {
                    "data": "02/09/2026 14:30",
                    "badge": '<span class="badge badge-green">POSTADO</span>',
                    "desc": "Objeto postado",
                    "local": "SAO PAULO/SP",
                    "detalhe": "",
                    "class": "",
                },
            ],
        },
        {
            "pedido": "41728",
            "rastreio": "AD556677889BR",
            "cliente": "Juliana Mendes",
            "situacao": "Aguardando Retirada",
            "status": "aguardando_retirada",
            "eventos": [
                {
                    "data": "10/09/2026 14:20",
                    "badge": '<span class="badge badge-red">AGUARDANDO RETIRADA</span>',
                    "desc": "Objeto aguardando retirada na agência dos Correios",
                    "local": "SAO PAULO/SP",
                    "detalhe": "AC República — Prazo de permanência: 7 dias corridos",
                    "class": "status-critical",
                },
                {
                    "data": "09/09/2026 17:00",
                    "badge": "",
                    "desc": "Tentativa de entrega não efetuada - Carteiro não atendido",
                    "local": "SAO PAULO/SP",
                    "detalhe": "",
                    "class": "",
                },
            ],
        },
        {
            "pedido": "41719",
            "rastreio": "NL443322110BR",
            "cliente": "Paulo Ricardo",
            "situacao": "Devolvido",
            "status": "devolvido",
            "eventos": [
                {
                    "data": "10/09/2026 09:10",
                    "badge": '<span class="badge badge-purple">DEVOLVIDO AO REMETENTE</span>',
                    "desc": "Objeto em devolução ao remetente",
                    "local": "RIO DE JANEIRO/RJ",
                    "detalhe": "Endereço com numeração inexistente",
                    "class": "status-devolvido",
                },
                {
                    "data": "06/09/2026 11:30",
                    "badge": '<span class="badge badge-green">POSTADO</span>',
                    "desc": "Objeto postado",
                    "local": "SAO PAULO/SP",
                    "detalhe": "",
                    "class": "",
                },
            ],
        },
        {
            "pedido": "41710",
            "rastreio": "BR998877665BR",
            "cliente": "Beatriz Martins",
            "situacao": "Entregue",
            "status": "entregue",
            "eventos": [
                {
                    "data": "09/09/2026 15:40",
                    "badge": '<span class="badge badge-green">ENTREGUE</span>',
                    "desc": "Objeto entregue ao destinatário",
                    "local": "FLORIANOPOLIS/SC",
                    "detalhe": "",
                    "class": "",
                },
            ],
        },
        {
            "pedido": "41701",
            "rastreio": "AD332211009BR",
            "cliente": "Lucas Silveira",
            "situacao": "Enviado",
            "status": "em_transito",
            "eventos": [
                {
                    "data": "11/09/2026 07:45",
                    "badge": "",
                    "desc": "Objeto em transferência",
                    "local": "BRASILIA/DF",
                    "detalhe": "",
                    "class": "",
                },
            ],
        },
        {
            "pedido": "41695",
            "rastreio": "PENDENTE_01",
            "cliente": "Camila Nogueira",
            "situacao": "Pronto para Envio",
            "status": "nao_enviado",
            "eventos": [
                {
                    "data": "11/09/2026 09:00",
                    "badge": '<span class="badge badge-yellow">AGUARDANDO COLETA</span>',
                    "desc": "Etiqueta impressa pelo Tiny ERP — Aguardando despacho",
                    "local": "SAO PAULO/SP",
                    "detalhe": "",
                    "class": "",
                },
            ],
        },
        {
            "pedido": "41690",
            "rastreio": "PENDENTE_02",
            "cliente": "Thiago Barbosa",
            "situacao": "Em Separação",
            "status": "nao_enviado",
            "eventos": [
                {
                    "data": "11/09/2026 08:30",
                    "badge": '<span class="badge badge-yellow">SEPARAÇÃO</span>',
                    "desc": "Pedido faturado no estoque — Aguardando expedição",
                    "local": "SAO PAULO/SP",
                    "detalhe": "",
                    "class": "",
                },
            ],
        },
    ]

    orders_cards = []
    for o in orders:
        events_html = []
        for ev in o["eventos"]:
            detalhe_div = f'<div class="event-detail">{ev["detalhe"]}</div>' if ev["detalhe"] else ""
            events_html.append(f"""
                <div class="event {ev['class']}">
                    <div class="event-header">
                        <span class="event-date">{ev['data']}</span>
                        {ev['badge']}
                    </div>
                    <div class="event-desc">{ev['desc']} - <strong>{ev['local']}</strong></div>
                    {detalhe_div}
                </div>
            """)

        card = f"""
        <div class="order-card" data-status="{o['status']}">
            <div class="order-header">
                <div class="order-title">Pedido Tiny #{o['pedido']} — {o['cliente']} ({o['rastreio']})</div>
                <div class="order-tiny-status">Status Tiny: {o['situacao']}</div>
            </div>
            <div class="events-container">
                {''.join(events_html)}
            </div>
        </div>
        """
        orders_cards.append(card)

    atrasados_link_html = (
        '<a href="pedidos_atrasados.html" class="nav-tab atrasados-tab">'
        '⏰ Pedidos Atrasados <span class="atrasados-count">1</span></a>'
    )

    # -------------------------------------------------------------------------
    # 3. HTML Principal: relatorio_rastreio.html
    # -------------------------------------------------------------------------
    relatorio_html = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Rastreio Correios (Demonstração)</title>
    <link rel="stylesheet" href="web/css/main.css?v={versao_cache}">
    <link rel="stylesheet" href="web/css/components.css?v={versao_cache}">
</head>
<body>
    <div id="toast" class="toast"></div>

    <div class="floating-actions">
        <button id="btnTheme" class="btn-theme" aria-label="Alternar tema claro/escuro">
            <span id="btnThemeText">🌙 Escuro</span>
        </button>
        <button id="btnUpdate" class="btn-action btn-update" title="Sincronizar dados com o Tiny e Correios">
            <div id="spinner" class="spinner"></div>
            <span id="btnUpdateText">🔄 Atualizar Dados</span>
        </button>
    </div>

    <div class="container">
        <header>
            <div class="header-main">
                <h1>📦 Status de Entregas</h1>
                <div class="meta">
                    Modo Demonstração (Portfólio) — Gerado em: {data_geracao}
                    <span id="next-check" style="margin-left: 10px; opacity: 0.9;">
                        | ⏰ Próxima verificação automática em: <strong id="countdown-timer">45:00</strong>
                    </span>
                </div>
            </div>
            <nav class="nav-tabs" aria-label="Navegação do painel">
                <a href="relatorio_rastreio.html" class="nav-tab active">📊 Painel Geral</a>
                {atrasados_link_html}
                <a href="opcoes_frete.html" class="nav-tab">📦 Opções de Frete</a>
            </nav>
        </header>

        {dashboard_html}

        <!-- Painel de Controles -->
        <div class="controls-panel">
            <div class="search-wrapper">
                <span class="search-icon">🔍</span>
                <input type="text" id="searchInput" class="search-input" placeholder="Buscar pedido, cliente, rastreio ou cidade..." aria-label="Buscar pedidos">
            </div>
            <div class="filters-row">
                <div class="filter-pills">
                    <button type="button" class="filter-pill active" data-filter="all">Todos</button>
                    <button type="button" class="filter-pill" data-filter="em_transito">🚚 Em Trânsito</button>
                    <button type="button" class="filter-pill" data-filter="atrasado">⏰ Atrasados</button>
                    <button type="button" class="filter-pill" data-filter="aguardando_retirada">🏢 Retirada</button>
                    <button type="button" class="filter-pill" data-filter="entregue">✅ Entregues</button>
                    <button type="button" class="filter-pill" data-filter="nao_enviado">📭 Não Enviados</button>
                    <button type="button" class="filter-pill" data-filter="devolvido">↩️ Devolvidos</button>
                    <button type="button" id="btnClearFilter" class="btn-clear-filter" title="Limpar busca e filtros">✕ Limpar filtros</button>
                </div>
                <span id="filterCount" class="filter-count"></span>
            </div>
        </div>

        <!-- Terminal de Logs Visual -->
        <div id="console" class="console-container">
            <div class="console-header">
                <div class="console-dot dot-red"></div>
                <div class="console-dot dot-yellow"></div>
                <div class="console-dot dot-green"></div>
                <span style="margin-left: 10px; color: #94a3b8; font-weight: 600; font-size: 0.85rem;">Terminal de Atualização (Ao Vivo)</span>
            </div>
            <div id="consoleBody" class="console-body">
                <div class="log-line log-info">⚡ Modo Demonstração inicializado com 10 pedidos realistas.</div>
                <div class="log-line log-success">✅ Sistema operacional pronto para consulta e filtros.</div>
            </div>
        </div>

        <!-- Lista de Cards de Pedidos -->
        <main class="orders-list">
            {''.join(orders_cards)}
        </main>
    </div>

    <script src="web/js/app.js?v={versao_cache}"></script>
    <script src="web/js/dashboard.js?v={versao_cache}"></script>
    <script src="web/js/logs.js?v={versao_cache}"></script>
    <script src="alert_frete.js?v={versao_cache}"></script>
</body>
</html>"""

    # -------------------------------------------------------------------------
    # 4. HTML Atrasados: pedidos_atrasados.html
    # -------------------------------------------------------------------------
    atrasados_html = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pedidos Atrasados — Mais de 3 Dias (Demonstração)</title>
    <link rel="stylesheet" href="web/css/main.css?v={versao_cache}">
    <link rel="stylesheet" href="web/css/components.css?v={versao_cache}">
</head>
<body>
    <div class="floating-actions">
        <button id="btnTheme" class="btn-theme" aria-label="Alternar tema claro/escuro">
            <span id="btnThemeText">🌙 Escuro</span>
        </button>
    </div>
    <div class="container">
        <header>
            <div class="header-main">
                <h1>⏰ Pedidos Atrasados</h1>
                <div class="meta">Pedidos com mais de 3 dias em trânsito — Gerado em: {data_geracao}</div>
            </div>
            <nav class="nav-tabs" aria-label="Navegação de atrasados">
                <a href="relatorio_rastreio.html" class="nav-tab">← Voltar ao Painel Principal</a>
                <span class="nav-tab active">⏰ Pedidos Atrasados (1)</span>
                <a href="opcoes_frete.html" class="nav-tab">📦 Opções de Frete</a>
            </nav>
        </header>

        <div class="summary">
            <div class="summary-card">
                <div class="summary-number num-total">1</div>
                <div class="summary-label">Total Atrasados</div>
            </div>
            <div class="summary-card">
                <div class="summary-number num-critico">0</div>
                <div class="summary-label">Crítico (7+ dias)</div>
            </div>
            <div class="summary-card">
                <div class="summary-number num-alto">1</div>
                <div class="summary-label">Alto (5-6 dias)</div>
            </div>
            <div class="summary-card">
                <div class="summary-number num-atencao">0</div>
                <div class="summary-label">Atenção (3-4 dias)</div>
            </div>
        </div>

        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Pedido</th>
                        <th>Rastreio</th>
                        <th>Postagem</th>
                        <th>Dias</th>
                        <th>Urgência</th>
                        <th>Último Evento</th>
                        <th>Local</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="urgencia-alta">
                        <td><strong>#41732</strong></td>
                        <td><code>BR112233445BR</code></td>
                        <td>02/09/2026</td>
                        <td><span class="dias-badge urgencia-alta">6 dias</span></td>
                        <td><span class="urgencia-tag urgencia-alta">ALTA</span></td>
                        <td>Objeto em transferência - trânsito lento</td>
                        <td>RECIFE/PE</td>
                        <td>Em Trânsito</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <script src="web/js/app.js?v={versao_cache}"></script>
    <script src="alert_frete.js?v={versao_cache}"></script>
</body>
</html>"""

    # -------------------------------------------------------------------------
    # 5. Script de Alerta de Frete: alert_frete.js
    # -------------------------------------------------------------------------
    alert_frete_js = """// Alerta de Frete — Script auxiliar carregado nos relatórios
console.log('alert_frete.js: pronto');
"""

    # -------------------------------------------------------------------------
    # 6. Gravação dos Arquivos
    # -------------------------------------------------------------------------
    p_relatorio = destino / "relatorio_rastreio.html"
    p_atrasados = destino / "pedidos_atrasados.html"
    p_alert = destino / "alert_frete.js"

    with open(p_relatorio, mode="w", encoding="utf-8") as f:
        f.write(relatorio_html)

    with open(p_atrasados, mode="w", encoding="utf-8") as f:
        f.write(atrasados_html)

    with open(p_alert, mode="w", encoding="utf-8") as f:
        f.write(alert_frete_js)

    return {
        "relatorio": str(p_relatorio),
        "atrasados": str(p_atrasados),
        "alert": str(p_alert),
    }


if __name__ == "__main__":
    gerados = gerar_dados_demonstracao()
    print("Dados de demonstração gerados com sucesso:")
    for k, v in gerados.items():
        print(f"  - {k}: {v}")
