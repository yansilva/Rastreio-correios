"""Testes automatizados para os assets do painel web e geração de relatórios."""

import mimetypes
from pathlib import Path

from Arquivos.server.security import resolve_safe_path


def test_arquivos_estaticos_frontend_existem():
    """Garante que a estrutura modular de arquivos web/css e web/js existe."""
    raiz = Path(__file__).resolve().parent.parent

    arquivos_esperados = [
        raiz / "web" / "css" / "main.css",
        raiz / "web" / "css" / "components.css",
        raiz / "web" / "js" / "app.js",
        raiz / "web" / "js" / "dashboard.js",
        raiz / "web" / "js" / "logs.js",
    ]

    for arq in arquivos_esperados:
        assert arq.exists(), f"Arquivo estático obrigatório não encontrado: {arq}"
        conteudo = arq.read_text(encoding="utf-8")
        assert len(conteudo) > 50, f"Arquivo {arq} está vazio ou muito curto."


def test_main_css_contem_variaveis_e_tokens():
    """Garante que main.css possui design tokens para light e dark mode."""
    raiz = Path(__file__).resolve().parent.parent
    main_css = (raiz / "web" / "css" / "main.css").read_text(encoding="utf-8")

    assert ":root" in main_css
    assert '[data-theme="dark"]' in main_css
    assert "--color-primary" in main_css
    assert "--color-bg" in main_css
    assert ".nav-tabs" in main_css


def test_components_css_contem_componentes_principais():
    """Garante que components.css possui regras para dashboard, busca, console e toasts."""
    raiz = Path(__file__).resolve().parent.parent
    comp_css = (raiz / "web" / "css" / "components.css").read_text(encoding="utf-8")

    assert ".controls-panel" in comp_css
    assert ".search-input" in comp_css
    assert ".filter-pill" in comp_css
    assert ".dash-card" in comp_css
    assert ".order-card" in comp_css
    assert "#toast" in comp_css
    assert ".console-container" in comp_css


def test_servidor_serve_arquivos_web_com_seguranca_e_mimetypes_corretos():
    """Garante que a camada de segurança do servidor permite servir web/css e web/js."""
    raiz = Path(__file__).resolve().parent.parent

    # Validação de segurança
    css_path = resolve_safe_path(raiz, "/web/css/main.css")
    assert css_path is not None
    assert css_path.exists()
    mime_css, _ = mimetypes.guess_type(str(css_path))
    assert mime_css == "text/css"

    js_path = resolve_safe_path(raiz, "/web/js/dashboard.js")
    assert js_path is not None
    assert js_path.exists()
    mime_js, _ = mimetypes.guess_type(str(js_path))
    assert mime_js in ("application/javascript", "text/javascript")


def test_relatorio_template_integra_assets_modulares():
    """Verifica se o template em consulta_correios.py vincula os arquivos modulares."""
    raiz = Path(__file__).resolve().parent.parent
    consulta_py = (raiz / "Arquivos" / "consulta_correios.py").read_text(encoding="utf-8")

    assert 'href="web/css/main.css' in consulta_py
    assert 'href="web/css/components.css' in consulta_py
    assert 'src="web/js/app.js' in consulta_py
    assert 'src="web/js/dashboard.js' in consulta_py
    assert 'src="web/js/logs.js' in consulta_py
    assert 'id="searchInput"' in consulta_py
    assert 'id="btnClearFilter"' in consulta_py
    assert 'class="nav-tabs"' in consulta_py


def test_ux_tema_botao_e_script():
    """Valida requisitos de UX do botão de tema, acessibilidade e persistência."""
    raiz = Path(__file__).resolve().parent.parent
    app_js = (raiz / "web" / "js" / "app.js").read_text(encoding="utf-8")
    consulta_py = (raiz / "Arquivos" / "consulta_correios.py").read_text(encoding="utf-8")

    # Script manipula data-theme no html e salva em localStorage
    assert "data-theme" in app_js
    assert "localStorage.setItem('theme'" in app_js or 'localStorage.setItem("theme"' in app_js
    assert "btnTheme" in app_js
    assert "aria-label" in app_js

    # Garante que logs.js NÃO registra o listener para evitar execução duplicada
    logs_js = (raiz / "web" / "js" / "logs.js").read_text(encoding="utf-8")
    assert "btnTheme" not in logs_js

    # Template possui botão com id, classe e aria-label
    assert 'id="btnTheme"' in consulta_py
    assert 'class="btn-theme"' in consulta_py
    assert 'aria-label="Alternar tema claro/escuro"' in consulta_py


def test_ux_busca_filtros_organizacao():
    """Valida a separação conceitual da área de busca, ações e filtros."""
    raiz = Path(__file__).resolve().parent.parent
    comp_css = (raiz / "web" / "css" / "components.css").read_text(encoding="utf-8")
    dash_js = (raiz / "web" / "js" / "dashboard.js").read_text(encoding="utf-8")
    consulta_py = (raiz / "Arquivos" / "consulta_correios.py").read_text(encoding="utf-8")

    # CSS possui classes dedicadas para cada seção
    assert ".search-wrapper" in comp_css
    assert ".filters-row" in comp_css
    assert ".filter-pills" in comp_css
    assert ".btn-clear-filter" in comp_css

    # Template organiza os blocos separadamente
    assert 'class="search-wrapper"' in consulta_py
    assert 'class="filters-row"' in consulta_py
    assert 'class="filter-pills"' in consulta_py
    assert 'id="btnClearFilter"' in consulta_py

    # Dashboard.js possui lógica para mostrar/esconder o botão Limpar
    assert "updateClearButton" in dash_js
    assert "clearAllFilters" in dash_js

    # Celular: a busca tem placeholder curto (cabe em 360px); o desktop mantém o texto completo
    assert 'data-placeholder-curto="Pedido, cliente ou rastreio"' in consulta_py
    assert 'data-placeholder-longo="Pedido, cliente, rastreio ou cidade"' in consulta_py
    assert "data-placeholder-curto" in dash_js
    # Celular: a linha de busca, visão e Opções fica numa grade só (sem linha própria)
    assert "display: contents" in comp_css
    assert ":has(.search-wrapper:focus-within" in comp_css
    # Faixa de pílulas: a página não rola ao focar uma pílula; o fade só existe quando há rolagem
    assert "scrollIntoView({ block: 'nearest', inline: 'nearest' })" not in dash_js
    assert "mostrarPilulaInteira" in dash_js
    assert ".filter-pills.tem-rolagem" in comp_css
    assert "scroll-margin-inline" not in comp_css


def test_nav_tabs_fixa_no_celular():
    """A faixa de abas fica presa ao topo ao rolar no celular (position: sticky)."""
    import re

    raiz = Path(__file__).resolve().parent.parent
    main_css = (raiz / "web" / "css" / "main.css").read_text(encoding="utf-8")
    assert re.search(r"\.nav-tabs\s*\{[^}]*position:\s*sticky", main_css, re.S) or re.search(
        r"@media \(max-width: 640px\)\s*\{\s*\.nav-tabs\s*\{[^}]*position:\s*sticky", main_css, re.S
    )


def test_alvos_de_toque_44px_no_celular():
    """No celular, o link 'Ver o painel', o histórico, a legenda e Opções têm 44px de altura."""
    raiz = Path(__file__).resolve().parent.parent
    comp_css = (raiz / "web" / "css" / "components.css").read_text(encoding="utf-8")

    # As regras finais do celular ficam no fim do arquivo (vencem as de 40px do desktop)
    bloco_celular = comp_css[comp_css.index("Lote B (celular"):]
    assert "a.btn-link {" in bloco_celular
    assert "display: inline-flex" in bloco_celular.split("a.btn-link {", 1)[1][:80]
    assert ".status-legend-details > summary,\n    .order-history > summary,\n    .btn-link {\n        min-height: 44px;" in bloco_celular
    assert ".options-menu > summary {\n        min-height: 44px;" in bloco_celular
    assert ".view-option {\n        min-height: 44px;\n        min-width: 44px;" in bloco_celular


def test_regras_duplicadas_removidas_do_celular():
    """Cada regra de celular aparece uma vez: sem duplicatas de .view-option, .btn-theme e .sort-select."""
    raiz = Path(__file__).resolve().parent.parent
    comp_css = (raiz / "web" / "css" / "components.css").read_text(encoding="utf-8")
    assert comp_css.count("    .btn-theme {\n        min-height: 44px;") == 0
    assert comp_css.count("    .view-option {\n        min-height: 44px;\n        padding: 6px 8px;") == 0
    assert comp_css.count("    .sort-select,\n    .btn-link {") == 0


def test_demo_gera_placeholders_e_estrutura_do_painel():
    """O demo tem a mesma estrutura de controles do painel e os atributos de placeholder."""
    raiz = Path(__file__).resolve().parent.parent
    demo_py = (raiz / "Arquivos" / "demo_data.py").read_text(encoding="utf-8")
    dash_js = (raiz / "web" / "js" / "dashboard.js").read_text(encoding="utf-8")

    assert 'data-placeholder-curto="Pedido, cliente ou rastreio"' in demo_py
    assert 'data-placeholder-longo="Pedido, cliente, rastreio ou cidade"' in demo_py
    assert 'class="search-row"' in demo_py
    assert 'class="meta-longo"' in demo_py and 'class="meta-curto"' in demo_py
    # A legenda fica dentro de Opções, como no painel real
    assert demo_py.index('class="options-panel"') < demo_py.index('class="status-legend-details"')
    # Sem o atributo, o placeholder não vira a string "null"
    assert "if (texto) searchInput.placeholder = texto;" in dash_js


def test_copiar_rastreio_usa_execcommand_apos_rejeicao_e_toast_sem_hex():
    """Copiar rastreio tenta o execCommand quando a Clipboard API rejeita, e o toast usa tokens do tema."""
    import re

    raiz = Path(__file__).resolve().parent.parent
    app_js = (raiz / "web" / "js" / "app.js").read_text(encoding="utf-8")

    # Caminho antigo chamado também no tratamento de rejeição da promessa, não só quando a API falta
    bloco_copia = app_js[app_js.index("function copiarPeloCampoOculto("):app_js.index("document.addEventListener('click'", app_js.index("function copiarPeloCampoOculto("))]
    assert re.search(r"writeText\(codigo\)\.then\(aoCopiar,\s*function\(\)\s*\{[^}]*?copiarPeloCampoOculto", bloco_copia, re.S)
    assert "execCommand('copy')" in bloco_copia
    assert "Copie manualmente: " in bloco_copia
    # Foco devolvido a quem estava nele, e o textarea removido mesmo se o execCommand falhar
    assert "activeElement" in bloco_copia
    assert "finally" in bloco_copia
    # Toast segurado por hover, foco ou toque e fechado por clique
    assert "pausarFechamento" in app_js and "fecharToast" in app_js
    # Erros ficam abertos com botão Fechar focável, em role="alert"; sucesso em role="status"
    assert "botaoFecharToast" in app_js and "'erro'" in app_js

    # logs.js: nome acessível acompanha o texto durante a consulta, e os toasts usam tokens (sem hex)
    logs_js = (raiz / "web" / "js" / "logs.js").read_text(encoding="utf-8")
    assert "aria-busy" in logs_js and "ajustarBotaoConsulta(true)" in logs_js
    assert "setAttribute('aria-label'" in logs_js
    for hex_toast in ("'#15803d'", "'#dc2626'", "'#b45309'"):
        assert hex_toast not in logs_js
    # Cooldown: o botão usa aria-disabled (o foco não cai no body) e não o disabled da consulta em andamento
    assert "desativarBotaoConsulta(true)" in logs_js and "iniciarEsperaConsulta(remaining)" in logs_js
    assert "if (btn) btn.disabled" not in logs_js
    assert "Disponível em" in logs_js and "/api/status" in logs_js

    # dashboard.js: o aviso da tabela usa o token de aviso do tema, sem hex fixo
    dash_js = (raiz / "web" / "js" / "dashboard.js").read_text(encoding="utf-8")
    assert "'#b45309'" not in dash_js
    assert "'var(--color-warning)'" in dash_js

    # Toast sem cor hexadecimal fixa: as cores vêm dos tokens do tema
    bloco_toast = app_js[app_js.index("function showToast("):app_js.index("// 2b.")]
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", bloco_toast)
    assert "var(--color-primary)" in bloco_toast
    assert "'alert'" in bloco_toast and "'status'" in bloco_toast
    assert "var(--color-success)" in bloco_copia
    assert "var(--color-danger)" in bloco_copia


def test_tabela_tem_layout_fixo_e_acoes_empilhadas_no_desktop():
    """A tabela cabe no contêiner: layout fixo a partir de 1024px, larguras amarradas à ordem real das células."""
    import re

    raiz = Path(__file__).resolve().parent.parent
    comp_css = (raiz / "web" / "css" / "components.css").read_text(encoding="utf-8")
    dash_js = (raiz / "web" / "js" / "dashboard.js").read_text(encoding="utf-8")

    # Ordem real das colunas: as células montadas em atualizarTabela
    bloco_linhas = dash_js[dash_js.index("linhas.forEach(function(l) {"):dash_js.index("while (envoltorio.firstChild)")]
    rotulos = re.findall(r"tr\.appendChild\(celula\(.*'([^']+)'\)\);|setAttribute\('data-label', '([^']+)'\)", bloco_linhas)
    ordem = [a or b for a, b in rotulos]
    assert ordem == ["Pedido", "Cliente", "Rastreio", "Status", "Último evento", "Tiny", "Ações"]

    # Layout fixo só a partir de 1024px; abaixo disso o layout é automático
    bloco_1024 = comp_css[comp_css.index("@media (min-width: 1024px) {"):]
    bloco_1024 = bloco_1024[:bloco_1024.index("\n}\n") + 3]
    assert "table-layout: fixed;" in bloco_1024

    # Larguras fixas de cada coluna, pela posição real na tabela
    larguras = {"Pedido": 72, "Rastreio": 130, "Status": 184, "Tiny": 100, "Ações": 180}
    for rotulo, px in larguras.items():
        posicao = ordem.index(rotulo) + 1
        assert f".orders-table th:nth-child({posicao}) {{ width: {px}px; }}" in bloco_1024

    # Ações numa linha: "Ver cartão" é botão só com ícone de 36px, alvo de toque de 44px, nome e title
    assert ".orders-table-actions .btn-ver-cartao {" in comp_css
    assert "width: 36px;" in comp_css.split(".orders-table-actions .btn-ver-cartao {")[1].split("}")[0]
    assert ".orders-table-actions .btn-ver-cartao::before {" in comp_css
    # -5px e não -4px: o bloco absoluto parte da área de preenchimento, dentro da borda de 1px
    assert "inset: -5px;" in comp_css.split(".orders-table-actions .btn-ver-cartao::before {")[1].split("}")[0]
    assert "ver.className = 'btn-ver-cartao';" in dash_js
    assert "ver.title = 'Ver cartão';" in dash_js
    assert "'Ver cartão do pedido #' + l.pedido" in dash_js
    assert "#i-package" in dash_js
    # O botão não herda a classe de cópia (estilo e alvo próprios)
    assert "ver.classList.add('btn-copy')" not in dash_js
    assert "botaoDeLinha('Ver cartão'" not in dash_js
    assert "Ver cartão como link" not in comp_css


def test_busca_ignora_texto_so_para_leitor_de_tela():
    """A busca não enxerga o .sr-only (descrição do selo): buscar um termo só da descrição não traz o cartão."""
    raiz = Path(__file__).resolve().parent.parent
    dash_js = (raiz / "web" / "js" / "dashboard.js").read_text(encoding="utf-8")

    assert "function textoDeBusca(no) {" in dash_js
    assert "classList.contains('sr-only')" in dash_js
    assert "var cardText = textoDeBusca(card).toLowerCase();" in dash_js
    assert "card.textContent.toLowerCase()" not in dash_js


def test_copiar_rastreio_da_tabela_tem_nome_que_comeca_pelo_texto_visivel():
    """WCAG 2.5.3 (Label in Name): o aria-label do botão da tabela começa com o texto visível "Copiar rastreio"."""
    raiz = Path(__file__).resolve().parent.parent
    dash_js = (raiz / "web" / "js" / "dashboard.js").read_text(encoding="utf-8")

    assert "copiar.setAttribute('aria-label', 'Copiar rastreio ' + l.rastreio);" in dash_js
    assert "Copiar código de rastreio" not in dash_js


def test_primeiro_pedido_cabe_no_celular_sem_horario_na_contagem_curta():
    """No celular, a contagem curta do cabeçalho é só "N min"; a faixa de ação não estica os chips."""
    import re

    raiz = Path(__file__).resolve().parent.parent
    comp_css = (raiz / "web" / "css" / "components.css").read_text(encoding="utf-8")
    logs_js = (raiz / "web" / "js" / "logs.js").read_text(encoding="utf-8")

    # O horário "(às ...)" continua só na versão completa
    assert re.search(r"curta\.textContent = minutes < 1 \? 'menos de 1 min' : `\$\{minutes\} min`;", logs_js)
    assert "(às ${nextTimeStr})" in logs_js.split("completa.textContent")[1].split(";")[0]

    # Dentro de @media (max-width: 640px), o chip não estica
    bloco_faixa = comp_css[comp_css.index(".action-strip .action-chip {", comp_css.index("Chip cabe no próprio texto")):]
    bloco_faixa = bloco_faixa[:bloco_faixa.index("}") + 1]
    assert "flex: 0 1 auto;" in bloco_faixa
    assert "white-space: nowrap;" in bloco_faixa


def test_tabela_desativada_no_celular_sem_anel():
    """Tabela indisponível (aria-disabled) não usa o anel inset do pressionado: só aria-pressed tem anel."""
    import re

    raiz = Path(__file__).resolve().parent.parent
    comp_css = (raiz / "web" / "css" / "components.css").read_text(encoding="utf-8")

    bloco = re.search(r'\.view-option\[aria-disabled="true"\] \{([^}]*)\}', comp_css)
    assert bloco, "regra .view-option[aria-disabled=\"true\"] não encontrada"
    assert "inset" not in bloco.group(1)
    assert "outline: 1px dashed" in bloco.group(1)
    assert "outline-offset: -1px;" in bloco.group(1)
    assert "cursor: not-allowed;" in bloco.group(1)
    assert "color: var(--color-text-muted);" in bloco.group(1)


def test_expandir_historicos_some_na_compacta_e_na_tabela():
    """O JS liga a classe view-compacta no body, e o CSS esconde #btnToggleHistory e o rótulo nas visões Compacta e Tabela."""
    raiz = Path(__file__).resolve().parent.parent
    comp_css = (raiz / "web" / "css" / "components.css").read_text(encoding="utf-8")
    dash_js = (raiz / "web" / "js" / "dashboard.js").read_text(encoding="utf-8")

    assert "document.body.classList.toggle('view-compacta', modo === 'compacta');" in dash_js
    assert "document.body.classList.toggle('view-tabela', modo === 'tabela');" in dash_js
    # Botão sem :has: regra própria, para navegador sem suporte a :has não perder o esconder do botão
    assert ".view-compacta #btnToggleHistory,\n.view-tabela #btnToggleHistory {\n    display: none;\n}" in comp_css
    # Rótulo com :has: regra separada
    assert ".view-compacta .sort-label:has(+ #btnToggleHistory),\n.view-tabela .sort-label:has(+ #btnToggleHistory) {" in comp_css
    # A regra da Compacta que esconde o histórico do cartão continua valendo
    assert ".orders-list.is-compact .order-history {\n    display: none;\n}" in comp_css



def test_consulta_no_cabecalho_e_flutuante_so_no_celular():
    """O botão de consulta fica dentro de .header-tools (ao lado do tema); no celular vira o círculo fixo de 52px."""
    raiz = Path(__file__).resolve().parent.parent
    comp_css = (raiz / "web" / "css" / "components.css").read_text(encoding="utf-8")
    template = (raiz / "Arquivos" / "consulta_correios.py").read_text(encoding="utf-8")

    inicio_tools = template.index('<div class="header-tools">')
    fim_tools = template.index('<div class="header-main">')
    posicao_botao = template.index('id="btnUpdate"')
    assert template.count('id="btnUpdate"') == 1
    assert inicio_tools < posicao_botao < fim_tools, "botão de consulta fora do cabeçalho"
    assert "floating-actions" not in template
    assert "floating-actions" not in comp_css

    assert "    .btn-update {\n        position: fixed;" in comp_css
    assert "Botão de consulta: no celular sai do cabeçalho" in comp_css


def test_cartao_celular_tem_duas_linhas_e_cliente_com_duas_no_maximo():
    """No celular: selo e idade na 1ª linha, Tiny e copiar na 2ª; nome do cliente limitado a 2 linhas."""
    raiz = Path(__file__).resolve().parent.parent
    comp_css = (raiz / "web" / "css" / "components.css").read_text(encoding="utf-8")

    assert ".order-meta > .btn-copy { grid-column: 3; justify-self: end; }" in comp_css
    assert ".order-meta > .order-age { grid-column: 2 / 4; grid-row: 1; justify-self: end; }" in comp_css
    assert "-webkit-line-clamp: 2;" in comp_css
