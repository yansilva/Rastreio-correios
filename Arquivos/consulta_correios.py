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
    bloco_descricoes_status,
    chave_selo,
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
    textos_descricao,
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


def formatar_evento_html(evento, selo_cabecalho=""):
    """HTML de um evento da linha do tempo. `selo_cabecalho` é o selo do cabeçalho do cartão:
    se o selo do evento tiver o mesmo texto, ele não se repete."""
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
    texto_badge = ""
    classe_badge = ""

    if "RETIRADA" in desc_upper or "RETIRADA" in det_upper:
        status_class = "status-warning"
        texto_badge, classe_badge = "AGUARDANDO RETIRADA", "badge-yellow"
    elif "REMETENTE" in desc_upper:
        status_class = "status-devolvido"
        texto_badge, classe_badge = "DEVOLVIDO AO REMETENTE", "badge-purple"
    elif "CANCELADA" in desc_upper or "CANCELADA" in det_upper:
        status_class = "status-warning"
        texto_badge, classe_badge = "ENTREGA CANCELADA", "badge-yellow"
    elif "DEVOLVIDO" in desc_upper or "DEVOLUÇÃO" in desc_upper:
        status_class = "status-devolvido"
        texto_badge, classe_badge = "DEVOLVIDO", "badge-purple"
    elif "POSTADO" in desc_upper:
        # Verde é "entregue" (One Meaning Per Color): postagem é etapa de trânsito, então azul
        texto_badge, classe_badge = "POSTADO", "badge-blue"

    # O selo do evento some quando repete o do cabeçalho (ex.: "Aguardando retirada" nos dois)
    badge = ""
    if texto_badge and texto_badge.casefold() != selo_cabecalho.casefold():
        badge = f'<span class="badge {classe_badge}">{texto_badge}</span>'

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


_PASTA_WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web")


def _versao_assets() -> int:
    """Versão do cache dos CSS/JS: muda quando qualquer arquivo de web/ muda, então o navegador não reusa o CSS antigo."""
    return int(
        max(
            (os.path.getmtime(os.path.join(raiz, nome)) for raiz, _, nomes in os.walk(_PASTA_WEB) for nome in nomes),
            default=0,
        )
    )


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
                <button id="btnUpdate" class="btn-action btn-update" aria-label="Consultar Tiny e Correios" title="Consulta o Tiny e os Correios agora (pode levar alguns minutos)">
                    <div id="spinner" class="spinner"></div>
                    <svg class="icon icon-refresh" aria-hidden="true" focusable="false"><use href="#i-refresh"></use></svg><span id="btnUpdateText">Consultar Tiny e Correios</span>
                </button>
            </div>
            <div class="header-main">
                <h1><svg class="icon icon-package" aria-hidden="true" focusable="false"><use href="#i-package"></use></svg> Status de Entregas</h1>
                <div class="meta">
                    <span class="meta-dados" title="Relatório gerado em {data_geracao}">Dados <span class="meta-longo">de </span><time id="dadosEm" datetime="{iso_dados}">{data_dados_curta}</time> <span id="dadosIdade" class="meta-idade"></span></span>
                    <span class="meta-sep" aria-hidden="true">·</span>
                    <span id="next-check"><svg class="icon icon-clock" aria-hidden="true" focusable="false"><use href="#i-clock"></use></svg> <span class="meta-longo">Próxima consulta automática em </span><span class="meta-curto">próxima em </span><strong id="countdown-timer">—</strong></span>
                </div>
            </div>
        </header>
        <nav class="nav-tabs" aria-label="Navegação do painel">
            <a href="relatorio_rastreio.html" class="nav-tab active" aria-current="page"><svg class="icon icon-bar-chart" aria-hidden="true" focusable="false"><use href="#i-bar-chart"></use></svg> Painel</a>
            {atrasados_link}
            <a href="opcoes_frete.html" class="nav-tab"><svg class="icon icon-package" aria-hidden="true" focusable="false"><use href="#i-package"></use></svg> Opções de Frete</a>
        </nav>

        {dashboard}

        <!-- Painel de Controles -->
        <div class="controls-panel">
            <div class="search-row">
                <div class="search-wrapper">
                    <span class="search-icon"><svg class="icon icon-search" aria-hidden="true" focusable="false"><use href="#i-search"></use></svg></span>
                    <input type="text" id="searchInput" class="search-input" placeholder="Pedido, cliente, rastreio ou cidade" data-placeholder-longo="Pedido, cliente, rastreio ou cidade" data-placeholder-curto="Pedido, cliente ou rastreio" aria-label="Buscar pedidos" aria-keyshortcuts="/" title="Atalho: tecla /">
                </div>
                <span id="filterCount" class="filter-count" aria-live="polite"></span>
            </div>
            <div class="filters-row">
                {descricoes_status}
                <div class="filter-pills">
                    <button type="button" class="filter-pill active" data-filter="all">Todos</button>
                    <button type="button" class="filter-pill" data-filter="em_transito" title="{texto_em_transito}" aria-describedby="desc-status-em_transito"><svg class="icon icon-truck" aria-hidden="true" focusable="false"><use href="#i-truck"></use></svg> Em trânsito</button>
                    <button type="button" class="filter-pill" data-filter="atrasado" title="{texto_atrasado}" aria-describedby="desc-status-atrasado"><svg class="icon icon-clock" aria-hidden="true" focusable="false"><use href="#i-clock"></use></svg> Atrasados</button>
                    <button type="button" class="filter-pill" data-filter="aguardando_retirada" title="{texto_aguardando_retirada}" aria-describedby="desc-status-aguardando_retirada"><svg class="icon icon-building" aria-hidden="true" focusable="false"><use href="#i-building"></use></svg> Aguardando retirada</button>
                    <button type="button" class="filter-pill" data-filter="entregue" title="{texto_entregue}" aria-describedby="desc-status-entregue"><svg class="icon icon-check-circle" aria-hidden="true" focusable="false"><use href="#i-check-circle"></use></svg> Entregues</button>
                    <button type="button" class="filter-pill" data-filter="nao_enviado" title="{texto_nao_enviado}" aria-describedby="desc-status-nao_enviado"><svg class="icon icon-inbox" aria-hidden="true" focusable="false"><use href="#i-inbox"></use></svg> Não enviados</button>
                    <button type="button" class="filter-pill" data-filter="devolvido" title="{texto_devolvido}" aria-describedby="desc-status-devolvido"><svg class="icon icon-undo" aria-hidden="true" focusable="false"><use href="#i-undo"></use></svg> Devolvidos</button>
                </div>
            </div>
            <div class="list-meta">
                <button type="button" id="btnClearFilter" class="btn-clear-filter" title="Limpar busca e filtros">Limpar filtros</button>
                <div class="view-switch" role="group" aria-label="Visão">
                    <button type="button" class="view-option" data-view="cartoes" aria-pressed="true">Cartões</button>
                    <button type="button" class="view-option" data-view="compacta" aria-pressed="false">Compacta</button>
                    <button type="button" class="view-option" data-view="tabela" aria-pressed="false">Tabela</button>
                </div>
                <details class="options-menu"><summary>Opções</summary><div class="options-panel">
                <details class="status-legend-details"><summary>O que significam os status?</summary><p class="status-legend"><strong>Atrasado:</strong> {texto_atrasado} <strong>Aguardando retirada:</strong> {texto_aguardando_retirada}</p></details>
                <div class="list-tools">
                <label class="sort-label" for="sortSelect">Ordenar por</label>
                <select id="sortSelect" class="sort-select">
                    <option value="urgencia">Urgência</option>
                    <option value="recente">Último evento mais recente</option>
                    <option value="antigo">Último evento mais antigo</option>
                    <option value="pedido">Número do pedido</option>
                </select>
                <span class="sort-label">Dados</span>
                <button type="button" id="btnRegenerate" class="btn-link" title="Reconstrói esta página com os dados já consultados às {hora_dados}, sem chamar o Tiny nem os Correios">Recarregar dados salvos de {hora_dados}</button>
                <span class="sort-label">Históricos</span>
                <button type="button" id="btnToggleHistory" class="btn-link">Expandir históricos</button>
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

            # Pedido que já não precisa aparecer (devolvido à loja, entregue há tempo) some do painel e dos totais
            if TrackingService.deve_ocultar_card(obj_classificado):
                print(f">> Pedido #{pedido} ({rastreio}) — fora do painel ({status_category})")
                if not usar_cache:
                    time.sleep(0.2)
                continue

            # Contabilização de status
            if obj_classificado.is_devolvido:
                devolvidos_count += 1
                print(f">> Pedido #{pedido} ({rastreio}) — Status: DEVOLVIDO AO REMETENTE")
            elif obj_classificado.is_entregue:
                entregues_count += 1
                print(f">> Pedido #{pedido} ({rastreio}) — Status: Entregue")
            elif obj_classificado.is_postado:
                # Quem aguarda retirada também é postado, mas conta só em retiradas_count (faixa e pílula)
                if not obj_classificado.is_retirada:
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

            oculto = False  # cartões que deveriam ficar ocultos nem chegam aqui

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

            chave_descricao = "sem_postagem" if semp else chave_selo(
                status_category, retirada=obj_classificado.is_retirada, atrasado=esta_atrasado
            )
            # Eventos depois do selo do cabeçalho, para o selo do evento não repetir o dele
            events_html = []
            if obj_data and "eventos" in obj_data:
                for evento in obj_data["eventos"]:
                    events_html.append(formatar_evento_html(evento, selo_cabecalho=selo))
            else:
                events_html.append(
                    '<div class="event"><em>Sem informações de rastreio disponíveis nos Correios para este objeto.</em></div>'
                )
            card = montar_card_pedido(
                # Título em partes: número, cliente (campo novo do CSV, quando houver) e código de rastreio
                numero_txt=str(pedido),
                chave_descricao=chave_descricao,
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
            <div class="dash-card{zero(nao_enviados_count)}">
                <div class="dash-icon dash-icon-slate"><svg class="icon icon-inbox" aria-hidden="true" focusable="false"><use href="#i-inbox"></use></svg></div>
                <div class="dash-info">
                    <span class="dash-number dash-number-slate">{nao_enviados_count}</span>
                    <span class="dash-label">Não enviados</span>
                </div>
            </div>
            <div class="dash-card{zero(em_transito_count)}">
                <div class="dash-icon dash-icon-blue"><svg class="icon icon-truck" aria-hidden="true" focusable="false"><use href="#i-truck"></use></svg></div>
                <div class="dash-info">
                    <span class="dash-number dash-number-blue">{em_transito_count}</span>
                    <span class="dash-label">Em trânsito</span>
                </div>
            </div>
            <div class="dash-card{zero(entregues_count)}">
                <div class="dash-icon dash-icon-green"><svg class="icon icon-check-circle" aria-hidden="true" focusable="false"><use href="#i-check-circle"></use></svg></div>
                <div class="dash-info">
                    <span class="dash-number dash-number-green">{entregues_count}</span>
                    <span class="dash-label">Entregues</span>
                </div>
            </div>

            <div class="dash-card{zero(devolvidos_count)}">
                <div class="dash-icon dash-icon-purple"><svg class="icon icon-undo" aria-hidden="true" focusable="false"><use href="#i-undo"></use></svg></div>
                <div class="dash-info">
                    <span class="dash-number dash-number-purple">{devolvidos_count}</span>
                    <span class="dash-label">Devolvidos</span>
                </div>
            </div>
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
            versao_cache=_versao_assets(),
            descricoes_status=bloco_descricoes_status(),
            **textos_descricao(),
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
        th_cliente = '<th scope="col">Cliente</th>' if tem_cliente else ""
        # A coluna Status só aparece quando há mistura de status (hoje todos são "Em trânsito")
        tem_status = len({x["status"] for x in atrasados_data}) > 1
        th_status = '<th scope="col" class="col-secundaria">Status</th>' if tem_status else ""
        rows_html = ""
        for item in atrasados_data:
            dias = item["dias_transito"]
            # A cor de urgência vai no badge de dias; o rótulo (Crítico, Alto, Atenção) fica no próprio texto
            if dias >= 7:
                urgencia_class = "urgencia-alta"
                urgencia_rotulo = "Crítico"
            elif dias >= 5:
                urgencia_class = "urgencia-media"
                urgencia_rotulo = "Alto"
            else:
                urgencia_class = "urgencia-baixa"
                urgencia_rotulo = "Atenção"

            status_label = {"em_transito": "Em trânsito", "devolvido": "Devolvido"}.get(item["status"], item["status"])
            td_cliente = f'<td data-label="Cliente">{escape(item.get("cliente", ""))}</td>' if tem_cliente else ""
            td_status = f'<td data-label="Status" class="col-secundaria">{status_label}</td>' if tem_status else ""
            evento_completo = escape(str(item["ultimo_evento"]), quote=True)

            rows_html += f"""
            <tr class="{urgencia_class}">
                <td data-label="Pedido"><strong>#{item["pedido"]}</strong></td>
                {td_cliente}
                <td data-label="Rastreio"><code>{item["rastreio"]}</code></td>
                <td data-label="Postagem" class="col-secundaria">{item["data_postagem"]}</td>
                <td data-label="Dias"><span class="dias-badge {urgencia_class}">{dias} dias · {urgencia_rotulo}</span></td>
                <td data-label="Último Evento" class="col-secundaria" title="{evento_completo}"><span class="evento-texto">{item["ultimo_evento"]}</span></td>
                <td data-label="Local" class="col-secundaria">{item["ultimo_local"]}</td>
                {td_status}
                <td data-label="Ações"><button type="button" class="btn-copy" data-copy="{escape(str(item["rastreio"]), quote=True)}" aria-label="Copiar código de rastreio {escape(str(item["rastreio"]), quote=True)}">Copiar rastreio</button></td>
            </tr>
            """

        if total_atrasados > 0:
            tabela_conteudo = f"""
        <div class="table-wrapper">
            <table>
                <caption class="sr-only">Pedidos com mais de 3 dias em trânsito</caption>
                <thead>
                    <tr>
                        <th scope="col">Pedido</th>
                        {th_cliente}
                        <th scope="col">Rastreio</th>
                        <th scope="col" class="col-secundaria">Postagem</th>
                        <th scope="col">Dias</th>
                        <th scope="col" class="col-secundaria">Último Evento</th>
                        <th scope="col" class="col-secundaria">Local</th>
                        {th_status}
                        <th scope="col">Ações</th>
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
                <h2>Nada atrasado</h2>
                <p>Todos os pedidos estão dentro do prazo de 3 dias.</p>
                <a href="relatorio_rastreio.html" class="btn-link">Ver o painel</a>
            </div>
        </div>"""

        # Sem atrasos não há o que somar: só a mensagem calma, sem quatro zeros
        resumo_html = ""
        if total_atrasados > 0:
            resumo_html = f"""<div class="summary">
            <div class="summary-card{zero(total_atrasados)}">
                <div class="summary-number num-total">{total_atrasados}</div>
                <div class="summary-label">Total atrasados</div>
            </div>
            <div class="summary-card{zero(criticos)}">
                <div class="summary-number num-critico">{criticos}</div>
                <div class="summary-label">Crítico (7+ dias)</div>
            </div>
            <div class="summary-card{zero(altos)}">
                <div class="summary-number num-alto">{altos}</div>
                <div class="summary-label">Alto (5-6 dias)</div>
            </div>
            <div class="summary-card{zero(atencao)}">
                <div class="summary-number num-atencao">{atencao}</div>
                <div class="summary-label">Atenção (4 dias)</div>
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
    <a class="skip-link" href="#conteudo">Pular para os pedidos</a>
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
        </header>
        <nav class="nav-tabs" aria-label="Navegação de atrasados">
            <a href="relatorio_rastreio.html" class="nav-tab"><svg class="icon icon-bar-chart" aria-hidden="true" focusable="false"><use href="#i-bar-chart"></use></svg> Painel</a>
            <span class="nav-tab active" aria-current="page"><svg class="icon icon-clock" aria-hidden="true" focusable="false"><use href="#i-clock"></use></svg> Atrasados ({total_atrasados})</span>
            <a href="opcoes_frete.html" class="nav-tab"><svg class="icon icon-package" aria-hidden="true" focusable="false"><use href="#i-package"></use></svg> Opções de Frete</a>
        </nav>

        <main id="conteudo" tabindex="-1">
        {resumo_html}
        {tabela_conteudo}
        </main>
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
