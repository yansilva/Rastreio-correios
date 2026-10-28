import csv
import os
import sys
import time
from datetime import datetime
from html import escape

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
from correios.cache import carregar_cache, salvar_cache
from correios.cards import (
    PRIORIDADE_STATUS,
    dias_desde,
    divergencia_tiny,
    esta_encerrado,
    faixa_acao,
    montar_card_pedido,
    prioridade,
    selo_status,
    sem_postagem,
    status_tokens,
    texto_idade,
    zero,
)
from correios.icons import ICON_SPRITE

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
CACHE_ARQUIVO = "rastreios_cache.json"
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
        status_class = "status-warning"
        badge = '<span class="badge badge-yellow">AGUARDANDO RETIRADA</span>'
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


def processar(usar_cache=False):
    """Gera os relatórios HTML. Com `usar_cache=True` reaproveita o último retorno dos Correios, sem rede."""
    if not usar_cache:
        config = CorreiosConfig()
        if not config.credenciais_preenchidas():
            print(
                "Erro: Credenciais dos Correios não configuradas. "
                "Verifique ID_CORREIOS, CONTRATO e CODIGO_ACESSO no .env."
            )
            return False

    try:
        token = None if usar_cache else obter_token()

        # Cache das respostas dos Correios, na mesma pasta do script
        caminho_cache = os.path.join(os.path.dirname(os.path.abspath(__file__)), CACHE_ARQUIVO)
        objetos_cache = {}
        momento_dados = datetime.now()
        if usar_cache:
            carregado = carregar_cache(caminho_cache)
            if carregado is None:
                print("Erro: não há dados em cache. Clique em Consultar Tiny e Correios primeiro.")
                return False
            objetos_cache, momento_dados = carregado
        data_dados = momento_dados.strftime("%d/%m/%Y %H:%M:%S")
        if usar_cache:
            print(f"Regerando o relatório com os dados consultados em {data_dados} (sem chamar as APIs).")

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
    {icon_sprite}
    <a class="skip-link" href="#conteudo">Pular para os pedidos</a>
    <div id="toast" class="toast" role="status" aria-live="polite"></div>

    <div class="container">
        <header>
            <div class="header-tools">
                <button id="btnTheme" class="btn-theme" aria-label="Alternar tema claro/escuro">
            <svg class="icon icon-sun" aria-hidden="true" focusable="false"><use href="#i-sun"></use></svg><svg class="icon icon-moon" aria-hidden="true" focusable="false"><use href="#i-moon"></use></svg><span id="btnThemeText">Escuro</span>
        </button>
            </div>
            <div class="header-main">
                <h1><svg class="icon icon-package" aria-hidden="true" focusable="false"><use href="#i-package"></use></svg> Status de Entregas</h1>
                <div class="meta">
                    <span class="meta-dados" title="Relatório gerado em {data_geracao}">Dados de <time id="dadosEm" datetime="{iso_dados}">{data_dados_curta}</time> <span id="dadosIdade" class="meta-idade"></span></span>
                    <span class="meta-sep" aria-hidden="true">·</span>
                    <span id="next-check"><svg class="icon icon-clock" aria-hidden="true" focusable="false"><use href="#i-clock"></use></svg> Próxima consulta automática em <strong id="countdown-timer">carregando...</strong></span>
                </div>
            </div>
            <nav class="nav-tabs" aria-label="Navegação do painel">
                <a href="relatorio_rastreio.html" class="nav-tab active"><svg class="icon icon-bar-chart" aria-hidden="true" focusable="false"><use href="#i-bar-chart"></use></svg> Painel Geral</a>
                {atrasados_link}
                <a href="opcoes_frete.html" class="nav-tab"><svg class="icon icon-package" aria-hidden="true" focusable="false"><use href="#i-package"></use></svg> Opções de Frete</a>
            </nav>
        </header>

        {dashboard}

        <!-- Painel de Controles -->
        <div class="controls-panel">
            <div class="search-wrapper">
                <span class="search-icon"><svg class="icon icon-search" aria-hidden="true" focusable="false"><use href="#i-search"></use></svg></span>
                <input type="text" id="searchInput" class="search-input" placeholder="Pedido, cliente, rastreio ou cidade" aria-label="Buscar pedidos" aria-keyshortcuts="/" title="Atalho: tecla /">
            </div>
            <div class="filters-row">
                <div class="filter-pills">
                    <button type="button" class="filter-pill active" data-filter="all">Todos</button>
                    <button type="button" class="filter-pill" data-filter="em_transito"><svg class="icon icon-truck" aria-hidden="true" focusable="false"><use href="#i-truck"></use></svg> Em Trânsito</button>
                    <button type="button" class="filter-pill" data-filter="atrasado" title="Mais de 3 dias em trânsito desde a postagem"><svg class="icon icon-clock" aria-hidden="true" focusable="false"><use href="#i-clock"></use></svg> Atrasados</button>
                    <button type="button" class="filter-pill" data-filter="aguardando_retirada"><svg class="icon icon-building" aria-hidden="true" focusable="false"><use href="#i-building"></use></svg> Aguardando retirada</button>
                    <button type="button" class="filter-pill" data-filter="entregue"><svg class="icon icon-check-circle" aria-hidden="true" focusable="false"><use href="#i-check-circle"></use></svg> Entregues</button>
                    <button type="button" class="filter-pill" data-filter="nao_enviado"><svg class="icon icon-inbox" aria-hidden="true" focusable="false"><use href="#i-inbox"></use></svg> Não Enviados</button>
                    <button type="button" class="filter-pill" data-filter="devolvido"><svg class="icon icon-undo" aria-hidden="true" focusable="false"><use href="#i-undo"></use></svg> Devolvidos</button>
                    <button type="button" id="btnClearFilter" class="btn-clear-filter" title="Limpar busca e filtros">✕ Limpar filtros</button>
                </div>
                <span id="filterCount" class="filter-count" aria-live="polite"></span>
            </div>
            <div class="list-meta">
                <details class="status-legend-details"><summary>O que significam os status?</summary><p class="status-legend"><strong>Atrasado:</strong> mais de 3 dias em trânsito desde a postagem. <strong>Aguardando retirada:</strong> objeto na agência, esperando o destinatário.</p></details>
                <details class="options-menu"><summary>Opções</summary><div class="options-panel">
                <div class="list-tools">
                <label class="sort-label" for="sortSelect">Ordenar por</label>
                <select id="sortSelect" class="sort-select">
                    <option value="urgencia">Urgência</option>
                    <option value="recente">Último evento mais recente</option>
                    <option value="antigo">Último evento mais antigo</option>
                    <option value="pedido">Número do pedido</option>
                </select>
                <button type="button" id="btnRegenerate" class="btn-link" title="Reconstrói esta página com os dados já consultados às {hora_dados}, sem chamar o Tiny nem os Correios">Recarregar dados salvos de {hora_dados}</button>
                <button type="button" id="btnToggleHistory" class="btn-link">Expandir históricos</button>
                <label class="sort-label" for="viewSelect">Visão</label>
                <select id="viewSelect" class="sort-select">
                    <option value="cartoes">Cartões</option>
                    <option value="compacta">Compacta</option>
                    <option value="tabela">Tabela</option>
                </select>
            </div>
                </div></details>
            </div>
        </div>

        <!-- Terminal de Logs Visual -->
        <div id="console" class="console-container">
            <div class="console-header">
                <div class="console-dot dot-red"></div>
                <div class="console-dot dot-yellow"></div>
                <div class="console-dot dot-green"></div>
                <span style="margin-left: 10px; color: var(--console-muted); font-weight: 600; font-size: 0.85rem;">Terminal de Atualização (Ao Vivo)</span>
            </div>
            <div id="consoleBody" class="console-body" aria-live="polite"></div>
        </div>

        <!-- Lista de Cards de Pedidos -->
        <main class="orders-list" id="conteudo" tabindex="-1">
            {content}
        </main>
    </div>

    <div class="floating-actions">
        <button id="btnUpdate" class="btn-action btn-update" aria-label="Consultar Tiny e Correios" title="Consulta o Tiny e os Correios agora (pode levar alguns minutos)">
            <div id="spinner" class="spinner"></div>
            <svg class="icon icon-refresh" aria-hidden="true" focusable="false"><use href="#i-refresh"></use></svg><span id="btnUpdateText">Consultar Tiny e Correios</span>
        </button>
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
        retiradas_count = 0

        PEDIDOS_IGNORADOS = ["39192"]

        for venda in vendas:
            pedido = venda.get("Número do Pedido no Tiny")
            if pedido in PEDIDOS_IGNORADOS:
                continue

            rastreio = venda.get("Código de Rastreio")
            situacao_tiny = venda.get("Situação")
            cliente = (venda.get("Cliente") or "").strip()

            print(f"Processando {pedido}...")
            if usar_cache:
                obj_data = objetos_cache.get(str(rastreio))
            else:
                obj_data = consultar_objeto(rastreio, token)
                objetos_cache[str(rastreio)] = obj_data

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
                        "cliente": cliente,
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
            oculto = TrackingService.deve_ocultar_card(obj_classificado)

            esta_atrasado = atraso is not None
            if obj_classificado.is_retirada and status_category not in ("entregue", "devolvido"):
                retiradas_count += 1
            dias_atraso = atraso.dias_transito if atraso else 0
            selo, classe_selo = selo_status(
                status_category,
                retirada=obj_classificado.is_retirada,
                atrasado=esta_atrasado,
                dias_atraso=dias_atraso,
            )
            ultimo_evento = obj_classificado.eventos[0].dt_hr_criado if obj_classificado.eventos else ""
            # A etiqueta é o evento mais antigo da lista; se o Tiny diz "enviado" e ela tem mais de N dias, avisa
            data_etiqueta = obj_classificado.eventos[-1].dt_hr_criado if obj_classificado.eventos else ""
            dias_etiqueta = dias_desde(data_etiqueta)
            semp = sem_postagem(status_category, situacao_tiny, dias_etiqueta)
            if semp:
                selo = f"Sem postagem · {dias_etiqueta} dias"
                classe_selo = "badge-yellow"
            divergencia = (
                f"Tiny diz '{situacao_tiny}', mas os Correios só têm a etiqueta há {dias_etiqueta} dias"
                if semp
                else divergencia_tiny(status_category, situacao_tiny)
            )

            card = montar_card_pedido(
                # Com o nome do cliente (campo novo do CSV), o título fica como na demonstração; sem ele, só o rastreio
                titulo=(
                    f"Pedido Tiny #{pedido} — {cliente} ({rastreio})"
                    if cliente
                    else f"Pedido Tiny #{pedido} — {rastreio}"
                ),
                tokens=status_tokens(
                    status_category, retirada=obj_classificado.is_retirada, atrasado=esta_atrasado
                ),
                selo=selo,
                classe_selo=classe_selo,
                situacao_tiny=situacao_tiny,
                eventos_html=events_html,
                idade=texto_idade(ultimo_evento),
                oculto=oculto,
                encerrado=esta_encerrado(
                    status_category, retirada=obj_classificado.is_retirada, atrasado=esta_atrasado
                ),
                numero=str(pedido),
                idade_dias=dias_desde(ultimo_evento),
                divergencia=divergencia,
                rastreio=str(rastreio or ""),
                cliente=cliente,
            )
            ordem = (
                PRIORIDADE_STATUS["sem_postagem"]
                if semp
                else prioridade(status_category, retirada=obj_classificado.is_retirada, atrasado=esta_atrasado)
            )
            orders_html.append((ordem, -dias_atraso, card))
            if not usar_cache:
                time.sleep(0.2)

        if not usar_cache:
            try:
                salvar_cache(caminho_cache, objetos_cache)
            except (OSError, TypeError, ValueError) as exc:
                print(f"Aviso: não foi possível gravar o cache dos Correios ({exc}).")

        # Pedidos que pedem ação primeiro; entre atrasados, os mais antigos antes
        orders_html.sort(key=lambda item: (item[0], item[1]))
        orders_html = [card for _, _, card in orders_html]

        print(f"\nRelatório gerado. Entregues: {entregues_count} | Devolvidos: {devolvidos_count}")

        # Monta o dashboard de resumo
        dashboard_html = f"""
        {faixa_acao(len(atrasados_data), retiradas_count)}
        <div class="dashboard">
            <div class="dash-card dash-clickable{zero(nao_enviados_count)}" role="button" tabindex="0" data-filter="nao_enviado">
                <div class="dash-icon dash-icon-slate"><svg class="icon icon-inbox" aria-hidden="true" focusable="false"><use href="#i-inbox"></use></svg></div>
                <div class="dash-info">
                    <span class="dash-number dash-number-slate">{nao_enviados_count}</span>
                    <span class="dash-label">Não Enviados</span>
                </div>
            </div>
            <div class="dash-card dash-clickable{zero(em_transito_count)}" role="button" tabindex="0" data-filter="em_transito">
                <div class="dash-icon dash-icon-blue"><svg class="icon icon-truck" aria-hidden="true" focusable="false"><use href="#i-truck"></use></svg></div>
                <div class="dash-info">
                    <span class="dash-number dash-number-blue">{em_transito_count}</span>
                    <span class="dash-label">Em Trânsito</span>
                </div>
            </div>
            <div class="dash-card dash-clickable{zero(entregues_count)}" role="button" tabindex="0" data-filter="entregue">
                <div class="dash-icon dash-icon-green"><svg class="icon icon-check-circle" aria-hidden="true" focusable="false"><use href="#i-check-circle"></use></svg></div>
                <div class="dash-info">
                    <span class="dash-number dash-number-green">{entregues_count}</span>
                    <span class="dash-label">Entregues</span>
                </div>
            </div>

            <div class="dash-card dash-clickable{zero(devolvidos_count)}" role="button" tabindex="0" data-filter="devolvido">
                <div class="dash-icon dash-icon-purple"><svg class="icon icon-undo" aria-hidden="true" focusable="false"><use href="#i-undo"></use></svg></div>
                <div class="dash-info">
                    <span class="dash-number dash-number-purple">{devolvidos_count}</span>
                    <span class="dash-label">Devolvidos</span>
                </div>
            </div>
        </div>
        <div id="filterBanner" class="filter-banner">
            <span class="filter-banner-text" id="filterBannerText"></span>
        </div>
        """

        # Monta link para página de atrasados
        if len(atrasados_data) > 0:
            atrasados_link_html = f'<a href="pedidos_atrasados.html" class="nav-tab atrasados-tab"><svg class="icon icon-clock" aria-hidden="true" focusable="false"><use href="#i-clock"></use></svg> Atrasados <span class="atrasados-count">{len(atrasados_data)}</span></a>'
        else:
            atrasados_link_html = ""

        final_html = html_template.format(
            icon_sprite=ICON_SPRITE,
            data_geracao=time.strftime("%d/%m/%Y %H:%M:%S"),
            data_dados=data_dados,
            data_dados_curta=momento_dados.strftime("%d/%m %H:%M"),
            iso_dados=momento_dados.isoformat(timespec="seconds"),
            hora_dados=data_dados[11:16],
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

        # A coluna Cliente só aparece quando o CSV do Tiny trouxe o nome (campo novo, vazio em CSVs antigos)
        tem_cliente = any(x.get("cliente") for x in atrasados_data)
        th_cliente = "<th>Cliente</th>" if tem_cliente else ""
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
            td_cliente = f'<td data-label="Cliente">{escape(item.get("cliente", ""))}</td>' if tem_cliente else ""

            rows_html += f"""
            <tr class="{urgencia_class}">
                <td data-label="Pedido"><strong>#{item["pedido"]}</strong></td>
                {td_cliente}
                <td data-label="Rastreio"><code>{item["rastreio"]}</code></td>
                <td data-label="Postagem">{item["data_postagem"]}</td>
                <td data-label="Dias"><span class="dias-badge {urgencia_class}">{dias} dias</span></td>
                <td data-label="Urgência"><span class="urgencia-tag {urgencia_class}">{urgencia_label}</span></td>
                <td data-label="Último Evento">{item["ultimo_evento"]}</td>
                <td data-label="Local">{item["ultimo_local"]}</td>
                <td data-label="Status">{status_label}</td>
            </tr>
            """

        if total_atrasados > 0:
            tabela_conteudo = f"""
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Pedido</th>
                        {th_cliente}
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
                <div class="emoji"><svg class="icon icon-check-circle" aria-hidden="true" focusable="false"><use href="#i-check-circle"></use></svg></div>
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
    {ICON_SPRITE}
    <div class="container">
        <header>
            <div class="header-tools">
                <button id="btnTheme" class="btn-theme" aria-label="Alternar tema claro/escuro">
            <svg class="icon icon-sun" aria-hidden="true" focusable="false"><use href="#i-sun"></use></svg><svg class="icon icon-moon" aria-hidden="true" focusable="false"><use href="#i-moon"></use></svg><span id="btnThemeText">Escuro</span>
        </button>
            </div>
            <div class="header-main">
                <h1><svg class="icon icon-clock" aria-hidden="true" focusable="false"><use href="#i-clock"></use></svg> Pedidos Atrasados</h1>
                <div class="meta">Pedidos com mais de 3 dias em trânsito — Gerado em: {data_geracao_atrasados}</div>
            </div>
            <nav class="nav-tabs" aria-label="Navegação de atrasados">
                <a href="relatorio_rastreio.html" class="nav-tab">← Voltar ao Painel Principal</a>
                <span class="nav-tab active"><svg class="icon icon-clock" aria-hidden="true" focusable="false"><use href="#i-clock"></use></svg> Atrasados ({total_atrasados})</span>
                <a href="opcoes_frete.html" class="nav-tab"><svg class="icon icon-package" aria-hidden="true" focusable="false"><use href="#i-package"></use></svg> Opções de Frete</a>
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
                <div class="summary-label">Atenção (4 dias)</div>
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

        return True

    except Exception as e:
        print(f"Erro no processamento: {e}")
        return False


if __name__ == "__main__":
    processar()
