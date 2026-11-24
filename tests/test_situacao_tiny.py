"""A linha 'Situação no Tiny' só aparece no cartão quando o Tiny diverge dos Correios."""
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
from correios.cards import montar_card_pedido, situacao_tiny_visivel  # noqa: E402

ROTULO = "Situação no Tiny"


def _card(numero, mostrar):
    return montar_card_pedido(
        numero_txt=numero,
        chave_descricao="em_transito",
        tokens="em_transito",
        selo="Em trânsito",
        classe_selo="badge-blue",
        situacao_tiny="Entregue",
        eventos_html=[],
        mostrar_situacao_tiny=mostrar,
    )


class TestRegraDeVisibilidade(unittest.TestCase):
    def test_concorda_entregue_com_entregue(self):
        self.assertFalse(situacao_tiny_visivel("entregue", "Entregue", ""))

    def test_concorda_nao_entregue_com_enviado(self):
        for categoria in ("em_transito", "nao_enviado"):
            self.assertFalse(situacao_tiny_visivel(categoria, "Enviado", ""), categoria)

    def test_concorda_ignora_caixa_e_acento(self):
        self.assertFalse(situacao_tiny_visivel("em_transito", "ENVIADO ", ""))

    def test_diverge_nas_outras_combinacoes(self):
        casos = [
            ("em_transito", "Entregue"),  # Tiny entregue, Correios ainda em trânsito
            ("entregue", "Enviado"),  # Correios entregue, Tiny ainda enviado
            ("em_transito", "Pronto para envio"),
            ("nao_enviado", "Cancelado"),
            ("em_transito", ""),  # Tiny sem situação
        ]
        for categoria, tiny in casos:
            with self.subTest(categoria=categoria, tiny=tiny):
                self.assertTrue(situacao_tiny_visivel(categoria, tiny, ""))

    def test_regra_antiga_de_divergencia_tambem_mostra_a_linha(self):
        # Devolvido com Tiny enviado: a regra atual já aponta conflito; a linha continua
        self.assertTrue(situacao_tiny_visivel("devolvido", "Enviado", "Devolvido nos Correios, mas o Tiny mostra 'Enviado'"))


class TestCartao(unittest.TestCase):
    def test_concorda_nao_mostra_a_linha(self):
        self.assertNotIn(ROTULO, _card("1", mostrar=False))

    def test_diverge_mostra_a_linha(self):
        html = _card("2", mostrar=True)
        self.assertIn(f"{ROTULO}: Entregue", html)


class TestPainelComCache(unittest.TestCase):
    """Ponta a ponta: processar() decide por pedido, com o cache (sem rede)."""

    def test_linha_some_quando_concorda_e_aparece_quando_diverge(self):
        agora = datetime.now()
        recente = (agora - timedelta(days=1)).replace(microsecond=0).isoformat()
        entregue_hoje = (agora - timedelta(hours=1)).replace(microsecond=0).isoformat()

        def evento(quando, descricao):
            return {"dtHrCriado": quando, "descricao": descricao}

        cache = {
            # em trânsito + Tiny enviado: concorda
            "AE000000901BR": {"eventos": [evento(recente, "Objeto postado")]},
            # em trânsito + Tiny entregue: diverge
            "AE000000902BR": {"eventos": [evento(recente, "Objeto postado")]},
            # entregue + Tiny entregue: concorda
            "AE000000903BR": {"eventos": [evento(entregue_hoje, "Objeto entregue ao destinatário"), evento(recente, "Objeto postado")]},
        }
        csv = (
            "Número do Pedido no Tiny,Situação,Código de Rastreio\n"
            "9101,Enviado,AE000000901BR\n"
            "9102,Entregue,AE000000902BR\n"
            "9103,Entregue,AE000000903BR\n"
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

        cartoes = {}
        for bloco in re.split(r'(?=<div class="order-card)', html)[1:]:
            numero = re.search(r'data-pedido="(\d+)"', bloco).group(1)
            cartoes[numero] = bloco
        self.assertNotIn(ROTULO, cartoes["9101"])  # concorda
        self.assertIn(f"{ROTULO}: Entregue", cartoes["9102"])  # diverge
        self.assertNotIn(ROTULO, cartoes["9103"])  # concorda
