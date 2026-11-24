"""Avisos dos Correios: eventos que avisam sem mudar o status (ex.: 'pode levar mais tempo')."""
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
from correios.cards import faixa_acao, montar_card_pedido  # noqa: E402

AVISO_PRAZO = "Sua entrega ou retirada nos Correios pode levar mais tempo do que o previsto"

EVENTOS_43312 = {
    "eventos": [
        {"descricao": "Objeto em transferência - por favor aguarde", "dtHrCriado": "2026-11-24T12:12:00"},
        {"descricao": AVISO_PRAZO, "dtHrCriado": "2026-11-24T12:09:00"},
        {"descricao": "Objeto em transferência", "dtHrCriado": "2026-11-24T08:56:00"},
        {"descricao": "Objeto em transferência", "dtHrCriado": "2026-11-23T18:00:00"},
        {"descricao": "Objeto postado", "dtHrCriado": "2026-11-23T10:00:00"},
        {"descricao": "Etiqueta emitida", "dtHrCriado": "2026-11-23T09:00:00"},
    ]
}


def _card(aviso="", aviso_data=""):
    return montar_card_pedido(
        numero_txt="1",
        chave_descricao="em_transito",
        tokens="em_transito",
        selo="Em trânsito",
        classe_selo="badge-blue",
        situacao_tiny="Enviado",
        eventos_html=[],
        aviso=aviso,
        aviso_data=aviso_data,
    )


class TestDetecaoDeAviso(unittest.TestCase):
    def test_pedido_43312_e_em_transito_com_aviso(self):
        obj = TrackingService.processar_objeto("AE192204124BR", EVENTOS_43312)
        self.assertEqual(obj.status_categoria, "em_transito")
        self.assertEqual(TrackingService.aviso_do_objeto(obj), AVISO_PRAZO)

    def test_favor_desconsiderar_nao_e_aviso(self):
        dados = {
            "eventos": [
                {"descricao": "Favor desconsiderar a informação anterior", "dtHrCriado": "2026-11-24T12:00:00"},
                {"descricao": "Objeto postado", "dtHrCriado": "2026-11-23T10:00:00"},
            ]
        }
        obj = TrackingService.processar_objeto("AE000000025BR", dados)
        self.assertEqual(TrackingService.aviso_do_objeto(obj), "")

    def test_guarda_a_data_do_aviso(self):
        obj = TrackingService.processar_objeto("AE192204124BR", EVENTOS_43312)
        self.assertEqual(obj.aviso_data, "2026-11-24T12:09:00")

    def test_transferencia_e_etiqueta_nao_sao_aviso(self):
        dados = {
            "eventos": [
                {"descricao": "Objeto em transferência - por favor aguarde", "dtHrCriado": "2026-11-24T12:12:00"},
                {"descricao": "Objeto postado", "dtHrCriado": "2026-11-23T10:00:00"},
            ]
        }
        obj = TrackingService.processar_objeto("AE000000021BR", dados)
        self.assertEqual(TrackingService.aviso_do_objeto(obj), "")

    def test_aviso_mais_recente_e_o_guardado(self):
        dados = {
            "eventos": [
                {"descricao": "Inconsistências no endereçamento do objeto.", "dtHrCriado": "2026-11-25T09:00:00"},
                {"descricao": AVISO_PRAZO, "dtHrCriado": "2026-11-24T12:09:00"},
                {"descricao": "Objeto postado", "dtHrCriado": "2026-11-23T10:00:00"},
            ]
        }
        obj = TrackingService.processar_objeto("AE000000022BR", dados)
        self.assertEqual(TrackingService.aviso_do_objeto(obj), "Inconsistências no endereçamento do objeto.")

    def test_pedido_entregue_com_aviso_antigo_fica_sem_aviso(self):
        dados = {
            "eventos": [
                {"descricao": "Objeto entregue ao destinatário", "dtHrCriado": "2026-11-24T10:00:00"},
                {"descricao": AVISO_PRAZO, "dtHrCriado": "2026-11-23T12:09:00"},
                {"descricao": "Objeto postado", "dtHrCriado": "2026-11-20T10:00:00"},
            ]
        }
        obj = TrackingService.processar_objeto("AE000000023BR", dados)
        self.assertEqual(obj.status_categoria, "entregue")
        self.assertEqual(TrackingService.aviso_do_objeto(obj), "")

    def test_devolvido_nao_tem_aviso(self):
        dados = {
            "eventos": [
                {"descricao": "Objeto entregue ao remetente", "dtHrCriado": "2026-11-24T10:00:00"},
                {"descricao": AVISO_PRAZO, "dtHrCriado": "2026-11-23T12:09:00"},
            ]
        }
        obj = TrackingService.processar_objeto("AE000000024BR", dados)
        self.assertEqual(TrackingService.aviso_do_objeto(obj), "")


class TestCartao(unittest.TestCase):
    def test_com_aviso_marca_o_pedido_e_o_token(self):
        html = _card(aviso=AVISO_PRAZO)
        self.assertIn('data-aviso="1"', html)
        self.assertIn('data-status="em_transito com_aviso"', html)

    def test_contrato_do_paragrafo_do_aviso(self):
        html = _card(aviso=AVISO_PRAZO, aviso_data="22/11")
        self.assertRegex(
            html,
            r'<p class="order-aviso"><svg class="icon icon-info" aria-hidden="true" focusable="false">'
            r'<use href="#i-info"></use></svg>'
            r'<strong>Aviso dos Correios</strong> <span class="order-aviso-texto">'
            + re.escape(AVISO_PRAZO)
            + r'</span>\s*<time class="order-aviso-data">22/11</time></p>',
        )

    def test_paragrafo_fica_logo_depois_do_order_header(self):
        html = _card(aviso=AVISO_PRAZO)
        fim_header = html.index('<div class="events-container">')
        self.assertLess(html.index('<p class="order-aviso">'), fim_header)
        self.assertGreater(html.index('<p class="order-aviso">'), html.index('<div class="order-header">'))
        self.assertGreater(html.index('<p class="order-aviso">'), html.index('class="order-meta"'))

    def test_data_do_aviso_e_opcional(self):
        self.assertNotIn("order-aviso-data", _card(aviso=AVISO_PRAZO))

    def test_sem_aviso_nao_tem_marcas_do_aviso(self):
        html = _card()
        self.assertNotIn("data-aviso", html)
        self.assertNotIn("com_aviso", html)
        self.assertNotIn("order-aviso", html)

    def test_aviso_e_escapado(self):
        html = _card(aviso="<b>x</b>")
        self.assertNotIn("<b>x</b>", html)
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", html)


class TestFaixaComAviso(unittest.TestCase):
    def test_conta_pedidos_com_aviso_com_icone_info(self):
        faixa = faixa_acao(0, 0, 2)
        self.assertIn('data-filter="com_aviso"', faixa)
        self.assertIn("icon-info", faixa)
        self.assertNotIn("alert-triangle", faixa)
        self.assertRegex(faixa, r"<strong>2</strong> (?:<span[^>]*>)?Com aviso")

    def test_chip_so_aparece_com_avisos_positivos(self):
        self.assertNotIn("com_aviso", faixa_acao(3, 1, 0))

    def test_linha_calma_sem_atraso_nem_retirada(self):
        self.assertIn("Nada atrasado nem aguardando retirada", faixa_acao(0, 0, 0))
        self.assertNotIn("com_aviso", faixa_acao(0, 0, 0))

    def test_so_aviso_mostra_linha_calma_com_chip_e_sem_precisam_de_acao(self):
        # Decisão do usuário (17ª crítica): aviso não pede ação, então não há "Precisam de ação"
        faixa = faixa_acao(0, 0, 1)
        self.assertIn("Nada atrasado nem aguardando retirada", faixa)
        self.assertIn('data-filter="com_aviso"', faixa)
        self.assertNotIn("Precisam de ação", faixa)
        self.assertNotIn("action-strip-title", faixa)

    def test_com_atraso_ou_retirada_mantem_precisam_de_acao(self):
        self.assertIn("Precisam de ação", faixa_acao(1, 0, 1))
        self.assertIn("Precisam de ação", faixa_acao(0, 2, 0))


class TestPainelComCache(unittest.TestCase):
    def test_pedido_43312_no_relatorio_com_aviso_e_sem_aviso_nos_outros(self):
        agora = datetime.now()
        recente = (agora - timedelta(days=1)).replace(microsecond=0).isoformat()
        cache = {
            "AE192204124BR": EVENTOS_43312,
            "AE000000931BR": {"eventos": [{"dtHrCriado": recente, "descricao": "Objeto postado"}]},
        }
        csv = (
            "Número do Pedido no Tiny,Situação,Código de Rastreio\n"
            "43312,Enviado,AE192204124BR\n"
            "9311,Enviado,AE000000931BR\n"
        )
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
            html = Path(pasta, "relatorio_rastreio.html").read_text(encoding="utf-8")

        self.assertRegex(html, r"<strong>1</strong> (?:<span[^>]*>)?Com aviso")
        # O filtro fica na barra depois de "Aguardando retirada" (zerado, quando não há aviso)
        self.assertRegex(html, r'(?s)data-filter="aguardando_retirada".*?data-filter="com_aviso"')
        cartoes = {}
        for bloco in re.split(r'(?=<div class="order-card)', html)[1:]:
            cartoes[re.search(r'data-pedido="(\d+)"', bloco).group(1)] = bloco
        self.assertIn('data-aviso="1"', cartoes["43312"])
        self.assertIn('data-status="em_transito com_aviso"', cartoes["43312"])
        self.assertIn(f'<span class="order-aviso-texto">{AVISO_PRAZO}</span>', cartoes["43312"])
        self.assertNotIn("data-aviso", cartoes["9311"])
        self.assertNotIn("com_aviso", cartoes["9311"])


class TestTabelaDeAtrasados(unittest.TestCase):
    def test_linha_de_atrasado_com_aviso_marca_a_linha(self):
        agora = datetime.now()
        postado_ha_10_dias = (agora - timedelta(days=10)).replace(microsecond=0).isoformat()
        aviso_recente = (agora - timedelta(hours=2)).replace(microsecond=0).isoformat()
        cache = {
            "AE000000941BR": {
                "eventos": [
                    {"dtHrCriado": aviso_recente, "descricao": AVISO_PRAZO},
                    {"dtHrCriado": postado_ha_10_dias, "descricao": "Objeto postado"},
                ]
            },
        }
        csv = "Número do Pedido no Tiny,Situação,Código de Rastreio\n9411,Enviado,AE000000941BR\n"
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
            tabela = Path(pasta, "pedidos_atrasados.html").read_text(encoding="utf-8")

        linhas = [linha for linha in re.findall(r"<tr[^>]*>.*?</tr>", tabela, re.S) if "AE000000941BR" in linha]
        self.assertEqual(len(linhas), 1)
        self.assertIn('data-aviso="1"', linhas[0].split(">", 1)[0])
        self.assertIn(f'<span class="order-aviso-texto">{AVISO_PRAZO}</span>', linhas[0])


if __name__ == "__main__":
    unittest.main()
