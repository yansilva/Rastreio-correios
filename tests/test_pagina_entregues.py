"""Testes da página Entregues (entregues_semana.html).

O histórico é montado à mão: a página não depende do módulo de histórico ser executado.
"""

import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
ARQUIVOS_DIR = PROJECT_ROOT / "Arquivos"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(ARQUIVOS_DIR) not in sys.path:
    sys.path.insert(0, str(ARQUIVOS_DIR))

from correios.pagina_entregues import gerar_pagina_entregues, montar_html_entregues  # noqa: E402
from server.config import ServerConfig  # noqa: E402
from server.handler import RastreioRequestHandler  # noqa: E402

from tests.test_server import DummyHandler  # noqa: E402

# 12/11/2026 é quinta-feira: a semana atual vai de 09/11 a 15/11 e a anterior de 02/11 a 08/11
AGORA = datetime(2026, 11, 12, 10, 0)


def _item(pedido, entregue_em, postado_em="2026-11-07T14:02:00", cliente="Fulano de Tal", cidade="Rio de Janeiro/RJ"):
    rastreio = f"AE{pedido}BR"
    return {
        "pedido": pedido,
        "cliente": cliente,
        "rastreio": rastreio,
        "cidade": cidade,
        "postado_em": postado_em,
        "entregue_em": entregue_em,
        "registrado_em": entregue_em,
    }


def _historico(*itens):
    return {"versao": 1, "acompanhados": {}, "entregas": {i["rastreio"]: i for i in itens}}


def _tabela_atual(html):
    """Trecho da primeira tabela (semana atual), para não pegar a semana anterior."""
    inicio = html.index("<tbody")
    return html[inicio : html.index("</tbody>", inicio)]


class TestMaisDemoradoSemQuebra(unittest.TestCase):
    """O rótulo "Mais demorado · X dias" não pode quebrar com o "·" no início da linha."""

    def test_rotulo_e_dias_ficam_juntos_sem_quebra(self):
        # Postado 09/11 12:24, entregue 11/11 10:00: exatamente 1,9 dias
        historico = _historico(_item("9001", "2026-11-11T10:00:00", postado_em="2026-11-09T12:24:00"))
        html = montar_html_entregues(historico, AGORA, dados_em=AGORA)
        self.assertIn("Mais demorado&nbsp;·&nbsp;1,9&nbsp;dias", html)
        self.assertNotIn("Mais demorado · ", html)
        self.assertIn("1,9&nbsp;dias</td>", html)


class TestPaginaEntregues(unittest.TestCase):
    def test_pagina_tem_duas_semanas_e_seletor(self):
        html = montar_html_entregues(_historico(_item("42934", "2026-11-11T10:15:00")), AGORA, dados_em=AGORA)
        self.assertIn("Esta semana (09/11–15/11)", html)
        self.assertIn("Semana anterior", html)
        self.assertIn('aria-pressed="true"', html)
        self.assertIn('aria-pressed="false"', html)
        self.assertIn('data-painel-semana="0"', html)
        self.assertIn('data-painel-semana="1"', html)
        self.assertIn('src="web/js/entregues.js', html)

    def test_semana_vazia_sem_zeros(self):
        html = montar_html_entregues(_historico(), AGORA, dados_em=AGORA)
        self.assertIn("Nenhuma entrega nesta semana", html)
        self.assertNotIn(">0<", html)
        self.assertNotIn("Média de dias", html)

    def test_ordem_mais_recente_primeiro(self):
        historico = _historico(
            _item("1001", "2026-11-09T09:00:00"),
            _item("1002", "2026-11-11T09:00:00"),
            _item("1003", "2026-11-10T09:00:00"),
        )
        tabela = _tabela_atual(montar_html_entregues(historico, AGORA, dados_em=AGORA))
        self.assertLess(tabela.index("#1002"), tabela.index("#1003"))
        self.assertLess(tabela.index("#1003"), tabela.index("#1001"))

    def test_dias_sem_postagem_mostra_traco(self):
        historico = _historico(_item("2001", "2026-11-11T10:00:00", postado_em=None))
        html = montar_html_entregues(historico, AGORA, dados_em=AGORA)
        tabela = _tabela_atual(html)
        self.assertIn('data-label="Dias">—</td>', tabela)
        # Sem postagem, a média também fica de fora: o cartão mostra traço
        self.assertIn('<div class="summary-number">—</div>', html)

    def test_dias_acima_de_sete_recebem_tom_de_aviso(self):
        historico = _historico(_item("3001", "2026-11-12T08:00:00", postado_em="2026-11-02T08:00:00"))
        tabela = _tabela_atual(montar_html_entregues(historico, AGORA, dados_em=AGORA))
        self.assertIn('class="dias-badge urgencia-baixa"', tabela)

    def test_aba_entregues_no_menu_da_propria_pagina(self):
        html = montar_html_entregues(_historico(), AGORA, dados_em=AGORA)
        self.assertIn('href="entregues_semana.html" class="nav-tab active" aria-current="page"', html)
        self.assertIn('href="relatorio_rastreio.html"', html)
        self.assertIn('href="pedidos_atrasados.html"', html)
        self.assertIn('href="opcoes_frete.html"', html)

    def test_gerar_pagina_grava_arquivo_e_devolve_caminho(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = gerar_pagina_entregues(_historico(_item("4001", "2026-11-11T10:00:00")), AGORA, pasta, dados_em=AGORA)
            self.assertTrue(caminho.endswith("entregues_semana.html"))
            with open(caminho, encoding="utf-8") as f:
                self.assertIn("#4001", f.read())

    def test_escapa_cliente_cidade_e_rastreio(self):
        item = _item("5001", "2026-11-11T10:00:00", cliente='<script>alert("x")</script>', cidade='Vila "Nova"/SP')
        item["rastreio"] = 'AE"5001<b>BR'
        historico = {"versao": 1, "acompanhados": {}, "entregas": {item["rastreio"]: item}}
        html = montar_html_entregues(historico, AGORA, dados_em=AGORA)
        self.assertNotIn("<script>alert", html)
        self.assertIn("&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;", html)
        self.assertIn("Vila &quot;Nova&quot;/SP", html)
        self.assertIn('data-copy="AE&quot;5001&lt;b&gt;BR"', html)
        self.assertNotIn("<b>BR", html)

    def test_anuncio_da_troca_de_semana(self):
        historico = _historico(_item("6001", "2026-11-11T10:00:00"), _item("6002", "2026-11-10T10:00:00"))
        html = montar_html_entregues(historico, AGORA, dados_em=AGORA)
        self.assertIn('data-anuncio="Esta semana: 2 entregas"', html)
        self.assertIn('data-anuncio="Semana anterior: nenhuma entrega"', html)
        self.assertIn('id="entregues-anuncio" class="sr-only" role="status" aria-live="polite"', html)

    def test_tabela_com_papeis_explicitos(self):
        html = montar_html_entregues(_historico(_item("7001", "2026-11-11T10:00:00")), AGORA, dados_em=AGORA)
        self.assertIn('<table role="table">', html)
        self.assertIn('<tr role="row">', html)
        self.assertIn('<th role="columnheader" scope="col">Pedido</th>', html)
        self.assertIn('<td role="cell" data-label="Pedido">', html)

    def test_botao_copiar_tem_o_mesmo_nome_do_painel(self):
        # WCAG 2.5.3 (Label in Name): o nome acessível começa com o texto visível "Copiar rastreio"
        html = montar_html_entregues(_historico(_item("7002", "2026-11-11T10:00:00")), AGORA, dados_em=AGORA)
        self.assertIn('aria-label="Copiar rastreio AE7002BR"', html)
        self.assertNotIn("Copiar código de rastreio", html)

    def test_botao_de_tema_sem_aria_label(self):
        # O nome acessível é o texto visível ("Escuro"/"Claro"), como pede o WCAG 2.5.3
        html = montar_html_entregues(_historico(), AGORA, dados_em=AGORA)
        self.assertIn('<button id="btnTheme" class="btn-theme">', html)
        self.assertIn('<span id="btnThemeText">Escuro</span>', html)


class TestServidorEntregues(unittest.TestCase):
    """A página é servida de uma pasta temporária, sem depender do arquivo gerado na raiz do projeto."""

    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        base = Path(pasta.name)
        (base / "entregues_semana.html").write_text("<!DOCTYPE html><title>Entregues</title>", encoding="utf-8")
        anterior = RastreioRequestHandler.server_config
        RastreioRequestHandler.server_config = ServerConfig(base_dir=base, cooldown_seconds=10)
        self.addCleanup(setattr, RastreioRequestHandler, "server_config", anterior)

    def test_servidor_serve_entregues_semana(self):
        handler = DummyHandler(b"", "GET", "/entregues_semana.html")
        handler.do_GET()
        self.assertIn("HTTP/1.0 200", handler.wfile.getvalue().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
