"""Selos da linha do tempo: POSTADO não usa verde e o selo do evento não repete o do cabeçalho."""
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
import demo_data  # noqa: E402
from correios import TrackingService  # noqa: E402
from correios.cache import salvar_cache  # noqa: E402


def _evento(descricao, detalhe=""):
    return {
        "dtHrCriado": "2026-10-10T10:00:00",
        "descricao": descricao,
        "detalhe": detalhe,
        "unidade": {"endereco": {"cidade": "SAO PAULO", "uf": "SP"}},
    }


class TestSeloDoEventoUnitario(unittest.TestCase):
    def test_postado_usa_azul_e_nunca_verde(self):
        html = consulta_correios.formatar_evento_html(_evento("Objeto postado"), selo_cabecalho="Em trânsito")
        self.assertIn('<span class="badge badge-blue">POSTADO</span>', html)
        self.assertNotIn("badge-green", html)

    def test_selo_igual_ao_do_cabecalho_some_e_mantem_o_destaque(self):
        html = consulta_correios.formatar_evento_html(
            _evento("Objeto aguardando retirada na agência"), selo_cabecalho="Aguardando retirada"
        )
        self.assertNotIn("AGUARDANDO RETIRADA", html)
        self.assertNotIn('class="badge', html)
        self.assertIn('class="event status-warning"', html)

    def test_selo_diferente_do_cabecalho_continua_aparecendo(self):
        html = consulta_correios.formatar_evento_html(
            _evento("Objeto devolvido ao remetente"), selo_cabecalho="Devolvido"
        )
        self.assertIn('<span class="badge badge-purple">DEVOLVIDO AO REMETENTE</span>', html)


class TestSeloDoEventoNoRelatorio(unittest.TestCase):
    def test_relatorio_sem_postado_verde_e_sem_selo_repetido(self):
        agora = datetime.now()
        recente = (agora - timedelta(hours=2)).replace(microsecond=0).isoformat()
        antigo = (agora - timedelta(days=2)).replace(microsecond=0).isoformat()
        cidade = {"endereco": {"cidade": "SAO PAULO", "uf": "SP"}}
        cache = {
            "SY100BR": {
                "eventos": [
                    {"dtHrCriado": recente, "descricao": "Objeto aguardando retirada no endereço indicado", "unidade": cidade},
                    {"dtHrCriado": antigo, "descricao": "Objeto postado", "unidade": cidade},
                ]
            },
            "SY200BR": {"eventos": [{"dtHrCriado": recente, "descricao": "Objeto postado", "unidade": cidade}]},
        }
        with tempfile.TemporaryDirectory() as pasta:
            arquivos = os.path.join(pasta, "Arquivos")
            os.makedirs(arquivos)
            Path(arquivos, "rastreios_tiny.csv").write_text(
                "Número do Pedido no Tiny,Situação,Código de Rastreio\n8001,Enviado,SY100BR\n8002,Enviado,SY200BR\n",
                encoding="utf-8",
            )
            salvar_cache(os.path.join(arquivos, "rastreios_cache.json"), cache, agora)
            with (
                patch.object(consulta_correios, "__file__", os.path.join(arquivos, "consulta_correios.py")),
                patch.object(TrackingService, "deve_ocultar_card", return_value=False),
                patch("sys.stdout", new_callable=io.StringIO),
            ):
                resultado = consulta_correios.processar(usar_cache=True)
            self.assertIsNot(resultado, False)
            html = Path(pasta, "relatorio_rastreio.html").read_text(encoding="utf-8")

        self.assertNotIn('badge-green">POSTADO', html)
        self.assertIn('badge-blue">POSTADO', html)
        # Cabeçalho do cartão mostra "Aguardando retirada"; o primeiro evento não repete o selo
        self.assertIn(">Aguardando retirada</span>", html)
        self.assertNotIn("AGUARDANDO RETIRADA", html)


class TestSeloDaDemonstracao(unittest.TestCase):
    def test_demo_sem_postado_verde_e_sem_selo_repetido(self):
        with tempfile.TemporaryDirectory() as pasta, patch("sys.stdout", new_callable=io.StringIO):
            caminhos = demo_data.gerar_dados_demonstracao(pasta)
            conteudo = "".join(Path(c).read_text(encoding="utf-8") for c in caminhos.values() if Path(c).is_file())

        self.assertTrue(conteudo)
        self.assertNotIn('badge-green">POSTADO', conteudo)
        self.assertNotIn("AGUARDANDO RETIRADA", conteudo)
        self.assertNotIn("ENTREGUE</span>", conteudo)
        # A demo usa o mesmo gerador do painel: selo com descrição (title/sr-only) e nenhum selo de evento repetido
        self.assertIn('<span class="sr-only">: ', conteudo)
        cartoes = conteudo.split('class="order-card')[1:]
        self.assertTrue(cartoes)
        for cartao in cartoes:
            cabecalho = re.search(r'<span class="badge [a-z-]+"[^>]*>([^<]+)</span>', cartao).group(1)
            selos_eventos = re.findall(r'class="event-date">[^<]*</span>\s*<span class="badge [a-z-]+">([^<]+)</span>', cartao)
            for selo in selos_eventos:
                self.assertNotEqual(selo.casefold(), cabecalho.casefold())


if __name__ == "__main__":
    unittest.main()
