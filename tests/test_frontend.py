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

