"""Testes do cache dos Correios e da regeração do relatório sem chamar as APIs."""
import io
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_arquivos = os.path.join(_raiz, "Arquivos")
for _caminho in (_raiz, _arquivos):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

import consulta_correios  # noqa: E402
from correios.cache import carregar_cache, salvar_cache  # noqa: E402
from server.config import ServerConfig  # noqa: E402
from server.handler import RastreioRequestHandler  # noqa: E402
from server.logger import ServerLogQueue  # noqa: E402
from server.service import UpdateManager  # noqa: E402


class TestCache(unittest.TestCase):
    def test_salvar_e_carregar(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "cache.json")
            momento = datetime(2026, 10, 16, 18, 30, 5)
            salvar_cache(caminho, {"AB123BR": {"eventos": [{"descricao": "Objeto postado"}]}}, momento)

            objetos, quando = carregar_cache(caminho)
            self.assertEqual(objetos["AB123BR"]["eventos"][0]["descricao"], "Objeto postado")
            self.assertEqual(quando, momento)
            self.assertFalse(os.path.exists(caminho + ".tmp"))

    def test_arquivo_inexistente_ou_invalido_devolve_none(self):
        with tempfile.TemporaryDirectory() as pasta:
            self.assertIsNone(carregar_cache(os.path.join(pasta, "nao_existe.json")))
            ruim = os.path.join(pasta, "ruim.json")
            Path(ruim).write_text("{ não é json", encoding="utf-8")
            self.assertIsNone(carregar_cache(ruim))
            sem_objetos = os.path.join(pasta, "sem_objetos.json")
            Path(sem_objetos).write_text('{"gerado_em": "2026-10-16T10:00:00"}', encoding="utf-8")
            self.assertIsNone(carregar_cache(sem_objetos))

    def test_data_invalida_usa_data_do_arquivo(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "cache.json")
            Path(caminho).write_text('{"gerado_em": "ontem", "objetos": {}}', encoding="utf-8")
            objetos, quando = carregar_cache(caminho)
            self.assertEqual(objetos, {})
            self.assertIsInstance(quando, datetime)


class TestRegerarSemRede(unittest.TestCase):
    """Executa o processar() real com cache, numa pasta temporária, sem nenhuma chamada de rede."""

    def _montar(self, pasta: str, com_cache: bool) -> str:
        arquivos = os.path.join(pasta, "Arquivos")
        os.makedirs(arquivos)
        Path(os.path.join(arquivos, "rastreios_tiny.csv")).write_text(
            "Número do Pedido no Tiny,Situação,Código de Rastreio\n42517,Enviado,AE023423841BR\n",
            encoding="utf-8",
        )
        if com_cache:
            salvar_cache(
                os.path.join(arquivos, "rastreios_cache.json"),
                {
                    "AE023423841BR": {
                        "eventos": [
                            {
                                "dtHrCriado": "2026-10-14T23:02:00",
                                "descricao": "Objeto entregue ao destinatário",
                                "unidade": {"endereco": {"cidade": "SAO PAULO", "uf": "SP"}},
                            },
                            {
                                "dtHrCriado": "2026-10-10T10:00:00",
                                "descricao": "Objeto postado",
                                "unidade": {"endereco": {"cidade": "SAO PAULO", "uf": "SP"}},
                            },
                        ]
                    }
                },
                datetime(2026, 10, 14, 23, 30, 0),
            )
        return os.path.join(arquivos, "consulta_correios.py")

    def test_regera_html_do_cache_sem_chamar_apis(self):
        with tempfile.TemporaryDirectory() as pasta:
            falso_modulo = self._montar(pasta, com_cache=True)
            with (
                patch.object(consulta_correios, "__file__", falso_modulo),
                patch.object(consulta_correios, "obter_token", side_effect=AssertionError("chamou a rede")),
                patch.object(consulta_correios, "consultar_objeto", side_effect=AssertionError("chamou a rede")),
                patch("sys.stdout", new_callable=io.StringIO),
            ):
                resultado = consulta_correios.processar(usar_cache=True)

            self.assertIsNot(resultado, False)
            html = Path(pasta, "relatorio_rastreio.html").read_text(encoding="utf-8")
            self.assertIn("Dados consultados em: 14/10/2026 23:30:00", html)
            self.assertIn('data-status="entregue"', html)
            self.assertIn("Tiny desatualizado", html)
            self.assertTrue(Path(pasta, "pedidos_atrasados.html").exists())

    def test_sem_cache_devolve_false(self):
        with tempfile.TemporaryDirectory() as pasta:
            falso_modulo = self._montar(pasta, com_cache=False)
            with (
                patch.object(consulta_correios, "__file__", falso_modulo),
                patch("sys.stdout", new_callable=io.StringIO) as saida,
            ):
                resultado = consulta_correios.processar(usar_cache=True)

            self.assertIs(resultado, False)
            self.assertIn("não há dados em cache", saida.getvalue())
            self.assertFalse(Path(pasta, "relatorio_rastreio.html").exists())


class TestUpdateManagerRegenerate(unittest.TestCase):
    def setUp(self):
        self.config = ServerConfig(cooldown_seconds=10, auto_update_interval=100)
        self.log_queue = ServerLogQueue()

    def test_sucesso_nao_inicia_cooldown(self):
        chamadas = []
        manager = UpdateManager(
            self.config, self.log_queue, runner_fn=lambda: None, regenerator_fn=lambda: chamadas.append(1)
        )
        sucesso, mensagem = manager.regenerate()
        self.assertTrue(sucesso)
        self.assertIn("regerado", mensagem)
        self.assertEqual(chamadas, [1])
        self.assertEqual(manager.remaining_cooldown(), 0)
        self.assertFalse(manager._is_updating)

    def test_falha_devolve_mensagem_e_libera_trava(self):
        def falha():
            raise RuntimeError("sem cache")

        manager = UpdateManager(self.config, self.log_queue, runner_fn=lambda: None, regenerator_fn=falha)
        sucesso, mensagem = manager.regenerate()
        self.assertFalse(sucesso)
        self.assertEqual(mensagem, "sem cache")
        self.assertFalse(manager._is_updating)

    def test_nao_roda_durante_atualizacao(self):
        manager = UpdateManager(
            self.config, self.log_queue, runner_fn=lambda: None, regenerator_fn=lambda: self.fail("não deveria rodar")
        )
        manager._is_updating = True
        sucesso, mensagem = manager.regenerate()
        self.assertFalse(sucesso)
        self.assertIn("atualização em andamento", mensagem)


class DummyHandler(RastreioRequestHandler):
    """Handler com I/O em memória, como nos testes do servidor."""

    def __init__(self, command: str, path: str):
        self.rfile = io.BytesIO(b"")
        self.wfile = io.BytesIO()
        self.client_address = ("127.0.0.1", 12345)
        self.command = command
        self.path = path
        self.requestline = f"{command} {path} HTTP/1.1"
        self.request_version = "HTTP/1.1"
        self.headers = {}
        self.server_version = "TestServer/1.0"
        self.sys_version = "Python/3.12"
        self.close_connection = True

    def setup(self):
        pass

    def finish(self):
        pass


class TestRotaRegerar(unittest.TestCase):
    def setUp(self):
        self.config = ServerConfig(base_dir=Path(_raiz), cooldown_seconds=10)
        self.log_queue = ServerLogQueue()
        self._anteriores = (
            RastreioRequestHandler.server_config,
            RastreioRequestHandler.log_queue,
            RastreioRequestHandler.update_manager,
        )
        RastreioRequestHandler.server_config = self.config
        RastreioRequestHandler.log_queue = self.log_queue

    def tearDown(self):
        (
            RastreioRequestHandler.server_config,
            RastreioRequestHandler.log_queue,
            RastreioRequestHandler.update_manager,
        ) = self._anteriores

    def test_post_regerar_sucesso(self):
        RastreioRequestHandler.update_manager = UpdateManager(
            self.config, self.log_queue, runner_fn=lambda: None, regenerator_fn=lambda: None
        )
        handler = DummyHandler("POST", "/regerar")
        handler.do_POST()
        saida = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("HTTP/1.0 200", saida)
        self.assertIn('"sucesso": true', saida)

    def test_post_regerar_falha_devolve_409_com_erro(self):
        def falha():
            raise RuntimeError("não há dados em cache")

        RastreioRequestHandler.update_manager = UpdateManager(
            self.config, self.log_queue, runner_fn=lambda: None, regenerator_fn=falha
        )
        handler = DummyHandler("POST", "/regerar")
        handler.do_POST()
        saida = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("HTTP/1.0 409", saida)
        self.assertIn("não há dados em cache", saida)


if __name__ == "__main__":
    unittest.main()
