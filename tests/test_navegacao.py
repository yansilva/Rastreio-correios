"""Menu de abas compartilhado (correios/navegacao.py): mesma ordem e rótulos em todas as páginas."""

import re
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import mock_open, patch

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
ARQUIVOS_DIR = PROJECT_ROOT / "Arquivos"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(ARQUIVOS_DIR) not in sys.path:
    sys.path.insert(0, str(ARQUIVOS_DIR))

from correios.navegacao import ABAS, CHAVES, nav_html  # noqa: E402
from correios.pagina_entregues import montar_html_entregues  # noqa: E402
from demo_data import gerar_dados_demonstracao  # noqa: E402
from frete.config import FreteConfig  # noqa: E402
from frete.report import FreteReportGenerator  # noqa: E402

AGORA = datetime(2026, 11, 12, 10, 0)
NAV_RE = re.compile(r'<nav class="nav-tabs".*?</nav>', re.S)
ARQUIVO_DA_ABA = {chave: arquivo for chave, arquivo, _, _ in ABAS}


def _normalizar(nav: str) -> str:
    """Estrutura do menu sem a marca da aba ativa e sem a contagem de atrasados."""
    sem_ativa = nav.replace(' active" aria-current="page"', '"')
    return re.sub(r' <span class="atrasados-count">\d+</span>', "", sem_ativa)


def _nav_da_pagina(html: str) -> str:
    achado = NAV_RE.search(html)
    assert achado, "a página não tem <nav class=\"nav-tabs\">"
    return achado.group(0)


class TestMenuUnico(unittest.TestCase):
    def test_ordem_unica_em_todas_as_abas(self):
        esperado = [ARQUIVO_DA_ABA[c] for c in ("painel", "atrasados", "entregues", "frete")]
        for ativa in CHAVES:
            with self.subTest(ativa=ativa):
                hrefs = re.findall(r'<a href="([^"]+)"', nav_html(ativa))
                self.assertEqual(hrefs, esperado)

    def test_so_a_aba_ativa_tem_marca_de_pagina_atual(self):
        for ativa in CHAVES:
            with self.subTest(ativa=ativa):
                nav = nav_html(ativa, atrasados=3)
                self.assertEqual(nav.count('aria-current="page"'), 1)
                marca = f'href="{ARQUIVO_DA_ABA[ativa]}" class="nav-tab active" aria-current="page"'
                self.assertIn(marca, nav)

    def test_menus_iguais_mudando_so_a_aba_ativa(self):
        referencia = _normalizar(nav_html("painel", atrasados=3))
        for ativa in CHAVES:
            with self.subTest(ativa=ativa):
                self.assertEqual(_normalizar(nav_html(ativa, atrasados=3)), referencia)

    def test_contagem_de_atrasados_so_com_numero_positivo(self):
        self.assertNotIn("atrasados-count", nav_html("painel", atrasados=0))
        self.assertNotIn("atrasados-count", nav_html("painel", atrasados=None))
        nav = nav_html("painel", atrasados=3)
        self.assertIn('<span class="atrasados-count">3</span>', nav)
        # A contagem fica na aba Atrasados, não em outra
        self.assertRegex(nav, r'pedidos_atrasados\.html" class="nav-tab">.*?atrasados-count">3<')

    def test_aba_desconhecida_levanta_erro(self):
        with self.assertRaises(ValueError):
            nav_html("inexistente")


class TestFerramentasDoCabecalho(unittest.TestCase):
    """O bloco de botões do cabeçalho (tema e, no painel, consulta) sai de uma função só."""

    def test_com_consulta_tem_tema_e_consulta(self):
        from correios.navegacao import ferramentas_html
        bloco = ferramentas_html(True)
        self.assertIn('<div class="header-tools">', bloco)
        self.assertIn('id="btnTheme" class="btn-theme"', bloco)
        self.assertIn('id="btnThemeText">Escuro</span>', bloco)
        self.assertIn('id="btnUpdate"', bloco)
        self.assertIn('aria-label="Consultar Tiny e Correios"', bloco)

    def test_sem_consulta_so_tem_o_tema(self):
        from correios.navegacao import ferramentas_html
        bloco = ferramentas_html(False)
        self.assertIn('id="btnTheme"', bloco)
        self.assertNotIn("btnUpdate", bloco)
        self.assertNotIn("Consultar", bloco)

    def test_paginas_geradas_usam_o_mesmo_bloco(self):
        from correios.navegacao import ferramentas_html
        # Entregues e a demo (painel e atrasados) renderizam o bloco pela mesma função
        html_entregues = montar_html_entregues({"entregas": {}}, AGORA, dados_em=AGORA)
        self.assertIn(ferramentas_html(False), html_entregues)
        with tempfile.TemporaryDirectory() as pasta:
            caminhos = gerar_dados_demonstracao(pasta)
            painel = Path(caminhos["relatorio"]).read_text(encoding="utf-8")
            atrasados = Path(caminhos["atrasados"]).read_text(encoding="utf-8")
        self.assertIn(ferramentas_html(True), painel)
        self.assertIn(ferramentas_html(False), atrasados)
        # O botão de consulta só existe no painel
        self.assertNotIn("btnUpdate", atrasados)
        self.assertNotIn("btnUpdate", html_entregues)

    def test_nao_ha_copia_do_bloco_fora_da_funcao(self):
        # As páginas de estilo painel não escrevem o bloco à mão; o frete tem o seu (outro botão de tema)
        raiz = Path(__file__).resolve().parent.parent / "Arquivos"
        arquivos = [raiz / "consulta_correios.py", raiz / "demo_data.py", raiz / "correios" / "pagina_entregues.py"]
        for caminho in arquivos:
            with self.subTest(arquivo=caminho.name):
                self.assertNotIn('<div class="header-tools">', caminho.read_text(encoding="utf-8"))


class TestPaginasGeradasComOMesmoMenu(unittest.TestCase):
    def _verificar(self, html: str, ativa: str):
        nav = _nav_da_pagina(html)
        marca = f'href="{ARQUIVO_DA_ABA[ativa]}" class="nav-tab active" aria-current="page"'
        self.assertIn(marca, nav)
        self.assertEqual(_normalizar(nav), _normalizar(nav_html("painel")))

    def test_entregues(self):
        self._verificar(montar_html_entregues({"entregas": {}}, AGORA, dados_em=AGORA, atrasados=3), "entregues")

    def test_frete(self):
        generator = FreteReportGenerator(config=FreteConfig(cep_origem="05617010"))
        pedido = {
            "numero": "1001", "situacao": "Aberto", "nome_cliente": "Teste", "valor": 150.0,
            "cep_destino": "01001000", "destino_label": "São Paulo/SP", "servicos": {},
        }
        with patch("builtins.open", mock_open()) as arquivo:
            generator.gerar_html([pedido])
            html = "".join(c.args[0] for c in arquivo().write.call_args_list if c.args)
        self._verificar(html, "frete")

    def test_demo_painel_e_atrasados(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminhos = gerar_dados_demonstracao(pasta)
            painel = Path(caminhos["relatorio"]).read_text(encoding="utf-8")
            atrasados = Path(caminhos["atrasados"]).read_text(encoding="utf-8")
        self._verificar(painel, "painel")
        self._verificar(atrasados, "atrasados")


if __name__ == "__main__":
    unittest.main()
