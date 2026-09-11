import csv
import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv

# Garante que o diretório Arquivos/ esteja no PYTHONPATH
_dir_atual = os.path.dirname(os.path.abspath(__file__))
if _dir_atual not in sys.path:
    sys.path.insert(0, _dir_atual)

from correios import (
    CorreiosClient,
    CorreiosConfig,
    TrackingService,
)

# Carrega variáveis de ambiente do .env na raiz do projeto ou em Arquivos/
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# Configuração e Credenciais Correios
_config = CorreiosConfig()
ID_CORREIOS = _config.id_correios
CONTRATO = _config.contrato
CODIGO_ACESSO = _config.codigo_acesso

# Endpoints
URL_TOKEN = _config.url_token
URL_RASTREIO = _config.url_rastreio

# Arquivos
CSV_ENTRADA = "rastreios_tiny.csv"
RELATORIO_HTML = "relatorio_rastreio.html"
RELATORIO_ATRASADOS = "pedidos_atrasados.html"


def obter_token():
    """Obtém token de autenticação nos Correios utilizando o CorreiosClient."""
    client = CorreiosClient()
    return client.gerar_token()


def consultar_objeto(objeto, token):
    """Consulta dados de rastreamento de um objeto na API dos Correios."""
    client = CorreiosClient()
    return client.consultar_objeto(objeto, token=token)


def formatar_evento_html(evento):
    dt_iso = evento.get("dtHrCriado", "")
    desc = evento.get("descricao", "")
    unidade = evento.get("unidade", {})
    endereco = unidade.get("endereco", {})
    cidade = endereco.get("cidade", "")
    uf = endereco.get("uf", "")
    local = f"{cidade}/{uf}".strip("/")
    detalhe = evento.get("detalhe", "")

    try:
        dt_obj = datetime.fromisoformat(dt_iso)
        dt_br = dt_obj.strftime("%d/%m/%Y %H:%M")
    except Exception:
        dt_br = dt_iso

    desc_upper = desc.upper()
    det_upper = detalhe.upper()

    status_class = ""
    badge = ""

    if "RETIRADA" in desc_upper or "RETIRADA" in det_upper:
        status_class = "status-critical"
        badge = '<span class="badge badge-red">AGUARDANDO RETIRADA</span>'
    elif "REMETENTE" in desc_upper:
        status_class = "status-devolvido"
        badge = '<span class="badge badge-purple">DEVOLVIDO AO REMETENTE</span>'
    elif "CANCELADA" in desc_upper or "CANCELADA" in det_upper:
        status_class = "status-warning"
        badge = '<span class="badge badge-yellow">ENTREGA CANCELADA</span>'
    elif "DEVOLVIDO" in desc_upper or "DEVOLUÇÃO" in desc_upper:
        status_class = "status-devolvido"
        badge = '<span class="badge badge-purple">DEVOLVIDO</span>'
    elif "POSTADO" in desc_upper:
        badge = '<span class="badge badge-green">POSTADO</span>'

    detalhe_html = f'<div class="event-detail">{detalhe}</div>' if detalhe else ""

    return f"""
    <div class="event {status_class}">
        <div class="event-header">
            <span class="event-date">{dt_br}</span>
            {badge}
        </div>
        <div class="event-desc">{desc} - <strong>{local}</strong></div>
        {detalhe_html}
    </div>
    """


def processar():
    config = CorreiosConfig()
    if not config.credenciais_preenchidas():
        print(
            "Erro: Credenciais dos Correios não configuradas. Verifique ID_CORREIOS, CONTRATO e CODIGO_ACESSO no .env."
        )
        return False

    try:
        token = obter_token()

        # Garante que procuramos o CSV na mesma pasta do script
        caminho_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)), CSV_ENTRADA)
        print(f"Lendo '{caminho_csv}'...")

        vendas = []
        with open(caminho_csv, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                vendas.append(row)

        if not vendas:
            print("Nenhum registro encontrado no CSV de entrada.")
            return

        print(f"\nConsultando {len(vendas)} objetos...")

        html_template = """<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Rastreio Correios</title>
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
                    Relatório gerado em: {data_geracao}
                    <span id="next-check" style="margin-left: 10px; opacity: 0.9;">
                        | ⏰ Próxima verificação automática em: <strong id="countdown-timer">carregando...</strong>
                    </span>
                </div>
            </div>
            <nav class="nav-tabs" aria-label="Navegação do painel">
                <a href="relatorio_rastreio.html" class="nav-tab active">📊 Painel Geral</a>
                {atrasados_link}
                <a href="opcoes_frete.html" class="nav-tab">📦 Opções de Frete</a>
            </nav>
        </header>

        {dashboard}

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
            <div id="consoleBody" class="console-body"></div>
        </div>

        <!-- Lista de Cards de Pedidos -->
        <main class="orders-list">
            {content}
        </main>
    </div>

    <script src="web/js/app.js?v={versao_cache}"></script>
    <script src="web/js/dashboard.js?v={versao_cache}"></script>
    <script src="web/js/logs.js?v={versao_cache}"></script>
    <script src="alert_frete.js?v={versao_cache}"></script>
</body>
</html>
        """

        orders_html = []
        atrasados_data = []
        entregues_count = 0
        devolvidos_count = 0
        nao_enviados_count = 0
        em_transito_count = 0

        PEDIDOS_IGNORADOS = ["39192"]

        for venda in vendas:
            pedido = venda.get("Número do Pedido no Tiny")
            if pedido in PEDIDOS_IGNORADOS:
                continue

            rastreio = venda.get("Código de Rastreio")
            situacao_tiny = venda.get("Situação")

            print(f"Processando {pedido}...")
            obj_data = consultar_objeto(rastreio, token)

            # Processamento e classificação com TrackingService
            obj_classificado = TrackingService.processar_objeto(rastreio, obj_data)
            status_category = obj_classificado.status_categoria

            events_html = []
            if obj_data and "eventos" in obj_data:
                for evento in obj_data["eventos"]:
                    events_html.append(formatar_evento_html(evento))
            else:
                events_html.append(
                    '<div class="event"><em>Sem informações de rastreio disponíveis nos Correios para este objeto.</em></div>'
                )

            # Contabilização de status
            if obj_classificado.is_devolvido:
                devolvidos_count += 1
                print(f">> Pedido #{pedido} ({rastreio}) — Status: DEVOLVIDO AO REMETENTE")
            elif obj_classificado.is_entregue:
                entregues_count += 1
                print(f">> Pedido #{pedido} ({rastreio}) — Status: Entregue")
            elif obj_classificado.is_postado:
                em_transito_count += 1
            else:
                nao_enviados_count += 1

            # Verificação de atraso com TrackingService
            atraso = TrackingService.verificar_atraso(obj_classificado, pedido, situacao_tiny)
            if atraso:
                atrasados_data.append(
                    {
                        "pedido": atraso.pedido,
                        "rastreio": atraso.rastreio,
                        "situacao_tiny": atraso.situacao_tiny,
                        "data_postagem": atraso.data_postagem,
                        "dias_transito": atraso.dias_transito,
                        "ultimo_evento": atraso.ultimo_evento,
                        "ultimo_local": atraso.ultimo_local,
                        "status": atraso.status,
                    }
                )

            # Visibilidade do card conforme regras de negócio
            hidden_class = "order-hidden" if TrackingService.deve_ocultar_card(obj_classificado) else ""

            card = f"""
            <div class="order-card {hidden_class}" data-status="{status_category}">
                <div class="order-header">
                    <div class="order-title">Pedido Tiny #{pedido} — {rastreio}</div>
                    <div class="order-tiny-status">Status Tiny: {situacao_tiny}</div>
                </div>
                <div class="events-container">
                    {"".join(events_html)}
                </div>
            </div>
            """
            orders_html.append(card)
            time.sleep(0.2)

        print(f"\nRelatório gerado. Entregues: {entregues_count} | Devolvidos: {devolvidos_count}")

        # Monta o dashboard de resumo
        dashboard_html = f"""
        <div class="dashboard">
            <div class="dash-card dash-clickable" onclick="filterOrders('nao_enviado')" data-filter="nao_enviado">
                <div class="dash-icon dash-icon-orange">📭</div>
                <div class="dash-info">
                    <span class="dash-number dash-number-orange">{nao_enviados_count}</span>
                    <span class="dash-label">Não Enviados</span>
                </div>
            </div>
            <div class="dash-card dash-clickable" onclick="filterOrders('em_transito')" data-filter="em_transito">
                <div class="dash-icon dash-icon-blue">🚚</div>
                <div class="dash-info">
                    <span class="dash-number dash-number-blue">{em_transito_count}</span>
                    <span class="dash-label">Em Trânsito</span>
                </div>
            </div>
            <div class="dash-card dash-clickable" onclick="filterOrders('entregue')" data-filter="entregue">
                <div class="dash-icon dash-icon-green">✅</div>
                <div class="dash-info">
                    <span class="dash-number dash-number-green">{entregues_count}</span>
                    <span class="dash-label">Entregues</span>
                </div>
            </div>

            <div class="dash-card dash-clickable" onclick="filterOrders('devolvido')" data-filter="devolvido">
                <div class="dash-icon dash-icon-purple">↩️</div>
                <div class="dash-info">
                    <span class="dash-number dash-number-purple">{devolvidos_count}</span>
                    <span class="dash-label">Devolvidos</span>
                </div>
            </div>
        </div>
        <div id="filterBanner" class="filter-banner">
            <span class="filter-banner-text" id="filterBannerText"></span>
            <button class="filter-banner-close" onclick="filterOrders(null)">✕ Mostrar Todos</button>
        </div>
        """

        # Monta link para página de atrasados
        if len(atrasados_data) > 0:
            atrasados_link_html = f'<a href="pedidos_atrasados.html" class="nav-tab atrasados-tab">⏰ Pedidos Atrasados <span class="atrasados-count">{len(atrasados_data)}</span></a>'
        else:
            atrasados_link_html = ""

        final_html = html_template.format(
            data_geracao=time.strftime("%d/%m/%Y %H:%M:%S"),
            dashboard=dashboard_html,
            content="".join(orders_html),
            atrasados_link=atrasados_link_html,
            versao_cache=int(time.time()),
        )

        # Salva o relatório na raiz do projeto (um nível acima de Arquivos/)
        pasta_projeto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caminho_html = os.path.join(pasta_projeto, RELATORIO_HTML)

        with open(caminho_html, mode="w", encoding="utf-8") as f:
            f.write(final_html)

        print(f"\nSucesso! Relatório HTML premium salvo em '{caminho_html}'.")

        # ===== GERA PÁGINA DE PEDIDOS ATRASADOS =====
        atrasados_data.sort(key=lambda x: x["dias_transito"], reverse=True)

        data_geracao_atrasados = time.strftime("%d/%m/%Y %H:%M:%S")
        total_atrasados = len(atrasados_data)

        # Calcula contagens por urgência
        criticos = len([x for x in atrasados_data if x["dias_transito"] >= 7])
        altos = len([x for x in atrasados_data if 5 <= x["dias_transito"] < 7])
        atencao = len([x for x in atrasados_data if x["dias_transito"] < 5])

        rows_html = ""
        for item in atrasados_data:
            dias = item["dias_transito"]
            if dias >= 7:
                urgencia_class = "urgencia-alta"
                urgencia_label = "CRÍTICO"
            elif dias >= 5:
                urgencia_class = "urgencia-media"
                urgencia_label = "ALTO"
            else:
                urgencia_class = "urgencia-baixa"
                urgencia_label = "ATENÇÃO"

            status_label = {"em_transito": "Em Trânsito", "devolvido": "Devolvido"}.get(item["status"], item["status"])

            rows_html += f"""
            <tr class="{urgencia_class}">
                <td><strong>#{item["pedido"]}</strong></td>
                <td><code>{item["rastreio"]}</code></td>
                <td>{item["data_postagem"]}</td>
                <td><span class="dias-badge {urgencia_class}">{dias} dias</span></td>
                <td><span class="urgencia-tag {urgencia_class}">{urgencia_label}</span></td>
                <td>{item["ultimo_evento"]}</td>
                <td>{item["ultimo_local"]}</td>
                <td>{status_label}</td>
            </tr>
            """

        if total_atrasados > 0:
            tabela_conteudo = f"""
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
                    {rows_html}
                </tbody>
            </table>
        </div>"""
        else:
            tabela_conteudo = """
        <div class="table-wrapper">
            <div class="empty-state">
                <div class="emoji">🎉</div>
                <h2>Nenhum pedido atrasado!</h2>
                <p>Todos os pedidos estão dentro do prazo de 3 dias.</p>
            </div>
        </div>"""

        atrasados_html_page = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pedidos Atrasados — Mais de 3 Dias</title>
    <link rel="stylesheet" href="web/css/main.css?v={int(time.time())}">
    <link rel="stylesheet" href="web/css/components.css?v={int(time.time())}">
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
                <div class="meta">Pedidos com mais de 3 dias em trânsito — Gerado em: {data_geracao_atrasados}</div>
            </div>
            <nav class="nav-tabs" aria-label="Navegação de atrasados">
                <a href="relatorio_rastreio.html" class="nav-tab">← Voltar ao Painel Principal</a>
                <span class="nav-tab active">⏰ Pedidos Atrasados ({total_atrasados})</span>
                <a href="opcoes_frete.html" class="nav-tab">📦 Opções de Frete</a>
            </nav>
        </header>

        <div class="summary">
            <div class="summary-card">
                <div class="summary-number num-total">{total_atrasados}</div>
                <div class="summary-label">Total Atrasados</div>
            </div>
            <div class="summary-card">
                <div class="summary-number num-critico">{criticos}</div>
                <div class="summary-label">Crítico (7+ dias)</div>
            </div>
            <div class="summary-card">
                <div class="summary-number num-alto">{altos}</div>
                <div class="summary-label">Alto (5-6 dias)</div>
            </div>
            <div class="summary-card">
                <div class="summary-number num-atencao">{atencao}</div>
                <div class="summary-label">Atenção (4-3 dias)</div>
            </div>
        </div>

        {tabela_conteudo}
    </div>

    <script src="web/js/app.js?v={int(time.time())}"></script>
    <script src="alert_frete.js?v={int(time.time())}"></script>
</body>
</html>"""

        caminho_atrasados = os.path.join(pasta_projeto, RELATORIO_ATRASADOS)
        with open(caminho_atrasados, mode="w", encoding="utf-8") as f:
            f.write(atrasados_html_page)

        print(
            f"Página de atrasados salva em '{caminho_atrasados}' ({len(atrasados_data)} pedido(s) com mais de 3 dias)."
        )

    except Exception as e:
        print(f"Erro no processamento: {e}")


if __name__ == "__main__":
    processar()
