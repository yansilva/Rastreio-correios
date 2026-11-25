"""Aba Atrasados com contagem: a página de Frete mostra o mesmo número que o painel, sem chamar API."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_arquivos = os.path.join(_raiz, "Arquivos")
for _caminho in (_raiz, _arquivos):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from correios.navegacao import (  # noqa: E402
    CONTAGEM_ARQUIVO,
    ler_contagem_atrasados,
    nav_html,
    salvar_contagem_atrasados,
)
from frete import FreteConfig, FreteReportGenerator  # noqa: E402


def _aba_atrasados(html):
    return next(linha for linha in html.splitlines() if "pedidos_atrasados.html" in linha)


class TestContagemGravada(unittest.TestCase):
    def test_grava_e_le_a_mesma_contagem(self):
        with tempfile.TemporaryDirectory() as pasta:
            salvar_contagem_atrasados(pasta, 3)
            self.assertEqual(ler_contagem_atrasados(pasta), 3)

    def test_sem_arquivo_devolve_none(self):
        with tempfile.TemporaryDirectory() as pasta:
            self.assertIsNone(ler_contagem_atrasados(pasta))

    def test_arquivo_invalido_devolve_none(self):
        with tempfile.TemporaryDirectory() as pasta:
            Path(pasta, CONTAGEM_ARQUIVO).write_text("{não é json", encoding="utf-8")
            self.assertIsNone(ler_contagem_atrasados(pasta))

    def test_valor_que_nao_e_inteiro_devolve_none(self):
        with tempfile.TemporaryDirectory() as pasta:
            Path(pasta, CONTAGEM_ARQUIVO).write_text('{"atrasados": "1"}', encoding="utf-8")
            self.assertIsNone(ler_contagem_atrasados(pasta))


class TestAbaAtrasadosComNumero(unittest.TestCase):
    def test_nav_frete_mostra_a_contagem(self):
        self.assertIn('<span class="atrasados-count">1</span>', _aba_atrasados(nav_html("frete", 1)))

    def test_nav_frete_sem_contagem_nao_mostra_numero(self):
        self.assertNotIn("atrasados-count", _aba_atrasados(nav_html("frete", None)))

    def test_nav_frete_com_zero_nao_mostra_numero(self):
        self.assertNotIn("atrasados-count", _aba_atrasados(nav_html("frete", 0)))

    def test_pagina_de_frete_gerada_mostra_o_numero_do_painel(self):
        # Gera a página sem pedidos (não chama a API de frete) num arquivo temporário
        with tempfile.TemporaryDirectory() as pasta:
            salvar_contagem_atrasados(pasta, 4)
            caminho = os.path.join(pasta, "opcoes_frete.html")
            config = FreteConfig()
            config.relatorio_html = caminho
            FreteReportGenerator(config=config).gerar_html([], atrasados=ler_contagem_atrasados(pasta))
            html = Path(caminho).read_text(encoding="utf-8")
        self.assertIn('<span class="atrasados-count">4</span>', _aba_atrasados(html))


if __name__ == "__main__":
    unittest.main()
