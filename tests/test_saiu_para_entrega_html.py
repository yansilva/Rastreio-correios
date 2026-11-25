"""HTML do status "Saiu para entrega": tokens, selo, precedência, linha de atraso, pílula e tabela."""
import io
import os
import re
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_arquivos = os.path.join(_raiz, "Arquivos")
for _caminho in (_raiz, _arquivos):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

import consulta_correios  # noqa: E402
from correios import TrackingService  # noqa: E402
from correios.cache import salvar_cache  # noqa: E402
from correios.cards import (  # noqa: E402
    DESCRICAO_STATUS,
    ROTULO_SELO,
    chave_selo,
    linha_atraso,
    montar_card_pedido,
    selo_status,
    status_tokens,
)

SAIU_CARD = "Saiu para entrega"


class TestTokens(unittest.TestCase):
    def test_saiu_soma_ao_em_transito(self):
        self.assertEqual(status_tokens("em_transito", saiu=True), "em_transito saiu_para_entrega")

    def test_saiu_com_atraso(self):
        self.assertEqual(
            status_tokens("em_transito", atrasado=True, saiu=True), "em_transito saiu_para_entrega atrasado"
        )

    def test_sem_saiu_nao_muda(self):
        self.assertEqual(status_tokens("em_transito"), "em_transito")

    def test_retirada_vence_e_nao_leva_saiu(self):
        self.assertEqual(status_tokens("em_transito", retirada=True, saiu=True), "aguardando_retirada")

    def test_entregue_nunca_leva_saiu(self):
        self.assertEqual(status_tokens("entregue", saiu=True), "entregue")


class TestSelo(unittest.TestCase):
    def test_rotulo_e_classe_teal(self):
        self.assertEqual(ROTULO_SELO["saiu_para_entrega"], ("Saiu para entrega", "badge-teal"))

    def test_descricao_do_designer(self):
        self.assertEqual(DESCRICAO_STATUS["saiu_para_entrega"], "Objeto com o carteiro, a caminho do destinatário.")

    def test_selo_saiu(self):
        self.assertEqual(selo_status("em_transito", saiu=True), (SAIU_CARD, "badge-teal"))

    def test_selo_saiu_atrasado_nao_ganha_dias_no_selo(self):
        self.assertEqual(
            selo_status("em_transito", atrasado=True, saiu=True, dias_atraso=8), (SAIU_CARD, "badge-teal")
        )

    def test_precedencia_retirada_antes_de_saiu(self):
        self.assertEqual(chave_selo("em_transito", retirada=True, saiu=True), "aguardando_retirada")

    def test_precedencia_saiu_antes_de_atrasado(self):
        self.assertEqual(chave_selo("em_transito", atrasado=True, saiu=True), "saiu_para_entrega")

    def test_atrasado_sem_saiu_continua_atrasado(self):
        self.assertEqual(chave_selo("em_transito", atrasado=True), "atrasado")

    def test_entregue_vence_saiu(self):
        self.assertEqual(chave_selo("entregue", saiu=True), "entregue")


class TestLinhaDeAtraso(unittest.TestCase):
    def test_linha_critica(self):
        html = linha_atraso(8)
        self.assertIn('class="order-atraso urgencia-alta"', html)
        self.assertIn("Atrasado · 8 dias · Crítico", html)
        self.assertIn('<use href="#i-clock">', html)

    def test_linha_media_e_baixa(self):
        self.assertIn("urgencia-media", linha_atraso(5))
        self.assertIn("Alto", linha_atraso(5))
        self.assertIn("urgencia-baixa", linha_atraso(3))
        self.assertIn("Atenção", linha_atraso(3))


class TestCartaoSaiu(unittest.TestCase):
    def _card(self, *, atraso_html="", **kwargs):
        return montar_card_pedido(
            numero_txt="43333",
            tokens=kwargs.pop("tokens", "em_transito saiu_para_entrega"),
            selo=kwargs.pop("selo", SAIU_CARD),
            classe_selo="badge-teal",
            situacao_tiny="Enviado",
            eventos_html=['<div class="event">x</div>'],
            chave_descricao="saiu_para_entrega",
            atraso_html=atraso_html,
            **kwargs,
        )

    def test_data_status_e_selo_teal(self):
        html = self._card()
        self.assertIn('data-status="em_transito saiu_para_entrega"', html)
        self.assertIn('<span class="badge badge-teal">Saiu para entrega</span>', html)

    def test_sem_atraso_nao_tem_linha(self):
        self.assertNotIn("order-atraso", self._card())

    def test_linha_de_atraso_entra_no_order_meta(self):
        html = self._card(atraso_html=linha_atraso(8), tokens="em_transito saiu_para_entrega atrasado")
        meta = html.split('<div class="order-meta">', 1)[1].split('<div class="events-container">', 1)[0]
        self.assertIn('class="order-atraso urgencia-alta"', meta)
        self.assertIn("Atrasado · 8 dias · Crítico", meta)


class TestPainelSaiu(unittest.TestCase):
    """Ponta a ponta com o cache: pedido que saiu, pílula, legenda e tabela de atrasados."""

    def _gerar(self, cache, csv):
        agora = datetime.now()
        with tempfile.TemporaryDirectory() as pasta:
            arquivos = os.path.join(pasta, "Arquivos")
            os.makedirs(arquivos)
            Path(arquivos, "rastreios_tiny.csv").write_text(csv, encoding="utf-8")
            salvar_cache(os.path.join(arquivos, "rastreios_cache.json"), cache, agora)
            with (
                patch.object(consulta_correios, "__file__", os.path.join(arquivos, "consulta_correios.py")),
                patch.object(TrackingService, "deve_ocultar_card", return_value=False),
                patch("sys.stdout", new_callable=io.StringIO),
            ):
                self.assertIsNot(consulta_correios.processar(usar_cache=True), False)
            relatorio = Path(pasta, "relatorio_rastreio.html").read_text(encoding="utf-8")
            tabela = Path(pasta, "pedidos_atrasados.html").read_text(encoding="utf-8")
        return relatorio, tabela

    @staticmethod
    def _cartoes(html):
        cartoes = {}
        for bloco in re.split(r'(?=<div class="order-card)', html)[1:]:
            cartoes[re.search(r'data-pedido="(\d+)"', bloco).group(1)] = bloco
        return cartoes

    def test_pedido_que_saiu_aparece_com_selo_teal_e_pilula(self):
        agora = datetime.now()
        recente = (agora - timedelta(hours=3)).replace(microsecond=0).isoformat()
        postado = (agora - timedelta(days=1)).replace(microsecond=0).isoformat()
        cache = {
            "AE000000333BR": {
                "eventos": [
                    {"codigo": "OEC", "tipo": "01", "descricao": "Objeto saiu para entrega ao destinatário",
                     "dtHrCriado": recente},
                    {"codigo": "PO", "tipo": "01", "descricao": "Objeto postado", "dtHrCriado": postado},
                ]
            }
        }
        csv = "Número do Pedido no Tiny,Situação,Código de Rastreio\n43333,Enviado,AE000000333BR\n"
        relatorio, _ = self._gerar(cache, csv)
        cartao = self._cartoes(relatorio)["43333"]
        self.assertIn('data-status="em_transito saiu_para_entrega"', cartao)
        self.assertIn('badge-teal">Saiu para entrega</span>', cartao)
        self.assertNotIn("order-atraso", cartao)
        self.assertRegex(relatorio, r'(?s)data-filter="em_transito".*?data-filter="saiu_para_entrega".*?data-filter="atrasado"')
        self.assertIn("<strong>Saiu para entrega:</strong>", relatorio)

    def test_saiu_atrasado_mostra_linha_e_status_na_tabela(self):
        agora = datetime.now()
        saiu = (agora - timedelta(hours=3)).replace(microsecond=0).isoformat()
        postado = (agora - timedelta(days=10)).replace(microsecond=0).isoformat()
        cache = {
            "AE000000284BR": {
                "eventos": [
                    {"codigo": "OEC", "tipo": "01", "descricao": "Objeto saiu para entrega ao destinatário",
                     "dtHrCriado": saiu},
                    {"codigo": "PO", "tipo": "01", "descricao": "Objeto postado", "dtHrCriado": postado},
                ]
            }
        }
        # Segundo atrasado sem saiu: a coluna Status só aparece quando há status misturados
        cache["AE000000285BR"] = {"eventos": [{"codigo": "PO", "tipo": "01", "descricao": "Objeto postado", "dtHrCriado": postado}]}
        csv = (
            "Número do Pedido no Tiny,Situação,Código de Rastreio\n"
            "43284,Enviado,AE000000284BR\n"
            "43285,Enviado,AE000000285BR\n"
        )
        relatorio, tabela = self._gerar(cache, csv)
        cartao = self._cartoes(relatorio)["43284"]
        self.assertIn('data-status="em_transito saiu_para_entrega atrasado"', cartao)
        self.assertIn('class="order-atraso urgencia-alta"', cartao)
        self.assertIn("Atrasado · 10 dias · Crítico", cartao)
        linhas = [linha for linha in re.findall(r"<tr[^>]*>.*?</tr>", tabela, re.S) if "AE000000284BR" in linha]
        self.assertEqual(len(linhas), 1)
        self.assertIn("Saiu para entrega", linhas[0])

    @staticmethod
    def _retirada(postado_em, retirada_em):
        return {
            "eventos": [
                {"codigo": "LDI", "tipo": "01", "descricao": "Objeto aguardando retirada no endereço indicado",
                 "dtHrCriado": retirada_em},
                {"codigo": "PO", "tipo": "01", "descricao": "Objeto postado", "dtHrCriado": postado_em},
            ]
        }

    def test_retirada_atrasada_mostra_a_linha_de_atraso(self):
        agora = datetime.now()
        postado = (agora - timedelta(days=10)).replace(microsecond=0).isoformat()
        retirada = (agora - timedelta(days=2)).replace(microsecond=0).isoformat()
        cache = {"AE000000431BR": self._retirada(postado, retirada)}
        csv = "Número do Pedido no Tiny,Situação,Código de Rastreio\n43249,Enviado,AE000000431BR\n"
        relatorio, _ = self._gerar(cache, csv)
        cartao = self._cartoes(relatorio)["43249"]
        self.assertIn('data-status="aguardando_retirada atrasado"', cartao)
        self.assertIn('badge-yellow">Aguardando retirada</span>', cartao)
        self.assertIn('class="order-atraso urgencia-alta"', cartao)
        self.assertIn("Atrasado · 10 dias · Crítico", cartao)

    def test_retirada_sem_atraso_nao_mostra_a_linha(self):
        agora = datetime.now()
        postado = (agora - timedelta(days=1)).replace(microsecond=0).isoformat()
        retirada = (agora - timedelta(hours=5)).replace(microsecond=0).isoformat()
        cache = {"AE000000432BR": self._retirada(postado, retirada)}
        csv = "Número do Pedido no Tiny,Situação,Código de Rastreio\n43250,Enviado,AE000000432BR\n"
        relatorio, _ = self._gerar(cache, csv)
        cartao = self._cartoes(relatorio)["43250"]
        self.assertIn("Aguardando retirada", cartao)
        self.assertNotIn("order-atraso", cartao)


if __name__ == "__main__":
    unittest.main()
