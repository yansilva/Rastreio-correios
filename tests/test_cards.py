"""Testes dos cartões de pedido do painel: selo de status, filtros, idade e histórico recolhido."""
import os
import sys
import unittest
from datetime import datetime

_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_arquivos = os.path.join(_raiz, "Arquivos")
if _arquivos not in sys.path:
    sys.path.insert(0, _arquivos)

from correios.cards import (  # noqa: E402
    PRIORIDADE_STATUS,
    dias_desde,
    divergencia_tiny,
    esta_encerrado,
    montar_card_pedido,
    prioridade,
    selo_status,
    sem_postagem,
    status_tokens,
    texto_idade,
)


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
            ("Aguardando retirada", "badge-yellow"),
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
        # Do que mais pede ação ao que já está encerrado (entregues por último)
        ordem = [
            prioridade("em_transito", retirada=True),
            prioridade("em_transito", atrasado=True),
            prioridade("em_transito"),
            prioridade("nao_enviado"),
            prioridade("devolvido"),
            prioridade("entregue"),
        ]
        self.assertEqual(sorted(ordem), ordem)
        self.assertEqual(len(set(ordem)), len(ordem))


class TestTextoIdade(unittest.TestCase):
    AGORA = datetime(2026, 10, 16, 12, 0)

    def test_hoje_ontem_e_dias(self):
        self.assertEqual(texto_idade("2026-10-16T08:00:00", self.AGORA), "Último evento hoje")
        self.assertEqual(texto_idade("2026-10-15T23:30:00", self.AGORA), "Último evento ontem")
        self.assertEqual(texto_idade("2026-10-11T10:00:00", self.AGORA), "Último evento há 5 dias")

    def test_data_invalida_devolve_vazio(self):
        self.assertEqual(texto_idade("", self.AGORA), "")
        self.assertEqual(texto_idade("não é data", self.AGORA), "")


class TestDiasDesde(unittest.TestCase):
    def test_dias_e_data_invalida(self):
        agora = datetime(2026, 10, 16, 12, 0)
        self.assertEqual(dias_desde("2026-10-11T10:00:00", agora), 5)
        self.assertIsNone(dias_desde("", agora))


class TestDivergenciaTiny(unittest.TestCase):
    def test_entregue_nos_correios_com_tiny_desatualizado(self):
        self.assertIn("Entregue nos Correios", divergencia_tiny("entregue", "Enviado"))
        self.assertIn("Entregue nos Correios", divergencia_tiny("entregue", "Não entregue"))

    def test_entregue_coerente(self):
        self.assertEqual(divergencia_tiny("entregue", "Entregue"), "")
        self.assertEqual(divergencia_tiny("entregue", "ENTREGUE "), "")

    def test_devolvido_com_tiny_enviado(self):
        self.assertIn("Devolvido nos Correios", divergencia_tiny("devolvido", "Enviado"))

    def test_devolvido_com_nao_entregue_e_coerente(self):
        self.assertEqual(divergencia_tiny("devolvido", "Não entregue"), "")

    def test_sem_situacao_ou_em_transito(self):
        self.assertEqual(divergencia_tiny("devolvido", ""), "")
        self.assertEqual(divergencia_tiny("em_transito", "Enviado"), "")


class TestSemPostagem(unittest.TestCase):
    def test_enviado_no_tiny_com_etiqueta_antiga(self):
        from correios.cards import DIAS_SEM_POSTAGEM

        self.assertTrue(sem_postagem("nao_enviado", "Enviado", DIAS_SEM_POSTAGEM + 1))
        self.assertTrue(sem_postagem("nao_enviado", "ENVIADO ", 9))

    def test_etiqueta_recente_ou_status_coerente_nao_avisa(self):
        self.assertFalse(sem_postagem("nao_enviado", "Enviado", 1))
        self.assertFalse(sem_postagem("nao_enviado", "Pronto para envio", 9))
        self.assertFalse(sem_postagem("em_transito", "Enviado", 9))
        self.assertFalse(sem_postagem("nao_enviado", "Enviado", None))

    def test_prioridade_fica_entre_atrasado_e_em_transito(self):
        self.assertLess(PRIORIDADE_STATUS["atrasado"], PRIORIDADE_STATUS["sem_postagem"])
        self.assertLess(PRIORIDADE_STATUS["sem_postagem"], PRIORIDADE_STATUS["em_transito"])


class TestEstaEncerrado(unittest.TestCase):
    def test_entregue_e_devolvido_sem_pendencia(self):
        self.assertTrue(esta_encerrado("entregue"))
        self.assertTrue(esta_encerrado("devolvido"))

    def test_pendencias_mantem_aberto(self):
        self.assertFalse(esta_encerrado("devolvido", retirada=True))
        self.assertFalse(esta_encerrado("entregue", atrasado=True))
        self.assertFalse(esta_encerrado("em_transito"))


class TestMontarCardPedido(unittest.TestCase):
    def test_atributos_de_ordenacao_encerrado_e_divergencia(self):
        card = montar_card_pedido(
            titulo="Pedido Tiny #42517",
            tokens="entregue",
            selo="Entregue",
            classe_selo="badge-green",
            situacao_tiny="Enviado",
            eventos_html=['<div class="event">x</div>'],
            encerrado=True,
            numero="42517",
            idade_dias=2,
            divergencia="Entregue nos Correios, mas o Tiny mostra 'Enviado'",
        )
        self.assertIn('class="order-card order-closed"', card)
        self.assertIn('data-pedido="42517"', card)
        self.assertIn('data-idade="2"', card)
        self.assertIn("Tiny desatualizado", card)
        self.assertIn("Entregue nos Correios, mas o Tiny mostra &#x27;Enviado&#x27;", card)

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
        self.assertIn("Situação no Tiny: Enviado", card)
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
        self.assertIn("Situação no Tiny: —", card)


if __name__ == "__main__":
    unittest.main()
