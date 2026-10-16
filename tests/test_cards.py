"""Testes dos cartões de pedido do painel: selo de status, filtros, idade e histórico recolhido."""
import os
import sys
import unittest
from datetime import datetime

_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_arquivos = os.path.join(_raiz, "Arquivos")
if _arquivos not in sys.path:
    sys.path.insert(0, _arquivos)

from correios.cards import montar_card_pedido, prioridade, selo_status, status_tokens, texto_idade  # noqa: E402


class TestStatusTokens(unittest.TestCase):
    def test_categoria_simples(self):
        self.assertEqual(status_tokens("em_transito"), "em_transito")

    def test_atrasado_e_retirada_somam_a_categoria(self):
        self.assertEqual(
            status_tokens("em_transito", retirada=True, atrasado=True),
            "em_transito aguardando_retirada atrasado",
        )

    def test_entregue_e_devolvido_nao_viram_retirada(self):
        self.assertEqual(status_tokens("entregue", retirada=True), "entregue")
        self.assertEqual(status_tokens("devolvido", retirada=True), "devolvido")


class TestSeloStatus(unittest.TestCase):
    def test_devolvido_e_entregue_tem_precedencia(self):
        self.assertEqual(selo_status("devolvido", retirada=True, atrasado=True), ("Devolvido", "badge-purple"))
        self.assertEqual(selo_status("entregue"), ("Entregue", "badge-green"))

    def test_retirada_antes_de_atrasado(self):
        self.assertEqual(
            selo_status("em_transito", retirada=True, atrasado=True, dias_atraso=5),
            ("Aguardando retirada", "badge-red"),
        )

    def test_atrasado_mostra_dias(self):
        self.assertEqual(
            selo_status("em_transito", atrasado=True, dias_atraso=6),
            ("Atrasado · 6 dias", "badge-red"),
        )

    def test_em_transito_e_nao_enviado(self):
        self.assertEqual(selo_status("em_transito"), ("Em trânsito", "badge-blue"))
        self.assertEqual(selo_status("nao_enviado"), ("Não enviado", "badge-yellow"))


class TestPrioridade(unittest.TestCase):
    def test_ordem_de_acao(self):
        ordem = [
            prioridade("entregue"),
            prioridade("nao_enviado"),
            prioridade("em_transito"),
            prioridade("devolvido"),
            prioridade("em_transito", atrasado=True),
            prioridade("em_transito", retirada=True),
        ]
        self.assertEqual(sorted(ordem, reverse=True), ordem)


class TestTextoIdade(unittest.TestCase):
    AGORA = datetime(2026, 10, 16, 12, 0)

    def test_hoje_ontem_e_dias(self):
        self.assertEqual(texto_idade("2026-10-16T08:00:00", self.AGORA), "Último evento hoje")
        self.assertEqual(texto_idade("2026-10-15T23:30:00", self.AGORA), "Último evento ontem")
        self.assertEqual(texto_idade("2026-10-11T10:00:00", self.AGORA), "Último evento há 5 dias")

    def test_data_invalida_devolve_vazio(self):
        self.assertEqual(texto_idade("", self.AGORA), "")
        self.assertEqual(texto_idade("não é data", self.AGORA), "")


class TestMontarCardPedido(unittest.TestCase):
    def _card(self, eventos, **kwargs):
        return montar_card_pedido(
            titulo="Pedido Tiny #1 — AB123BR",
            tokens="em_transito atrasado",
            selo="Atrasado · 4 dias",
            classe_selo="badge-red",
            situacao_tiny="Enviado",
            eventos_html=eventos,
            **kwargs,
        )

    def test_primeiro_evento_visivel_e_resto_recolhido(self):
        card = self._card(['<div class="event">novo</div>', '<div class="event">antigo</div>'])
        antes, _, depois = card.partition("<details")
        self.assertIn("novo", antes)
        self.assertNotIn("antigo", antes)
        self.assertIn("antigo", depois)
        self.assertIn("Ver histórico completo (2 eventos)", card)

    def test_evento_unico_nao_cria_historico(self):
        self.assertNotIn("<details", self._card(['<div class="event">único</div>']))

    def test_cabecalho_tem_selo_idade_e_status_tiny(self):
        card = self._card(['<div class="event">x</div>'], idade="Último evento ontem")
        self.assertIn('class="badge badge-red">Atrasado · 4 dias', card)
        self.assertIn("Último evento ontem", card)
        self.assertIn("Tiny: Enviado", card)
        self.assertIn('data-status="em_transito atrasado"', card)

    def test_oculto_e_escape_do_titulo(self):
        card = montar_card_pedido(
            titulo="<b>Cliente & Cia</b>",
            tokens="entregue",
            selo="Entregue",
            classe_selo="badge-green",
            situacao_tiny="",
            eventos_html=[],
            oculto=True,
        )
        self.assertIn('class="order-card order-hidden"', card)
        self.assertIn("&lt;b&gt;Cliente &amp; Cia&lt;/b&gt;", card)
        self.assertIn("Tiny: —", card)


if __name__ == "__main__":
    unittest.main()
