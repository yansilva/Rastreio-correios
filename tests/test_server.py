"""Suíte de testes automatizados para a camada de servidor web e painel.

Todos os testes utilizam mocks (unittest.mock) sem abrir portas reais na rede
nem abrir abas de navegador.
Compatível tanto com `pytest` quanto com `python -m unittest`.
"""
import io
import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

# Adiciona caminhos ao sys.path para importação consistente
TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
ARQUIVOS_DIR = PROJECT_ROOT / "Arquivos"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(ARQUIVOS_DIR) not in sys.path:
    sys.path.insert(0, str(ARQUIVOS_DIR))

from server.config import ServerConfig
from server.handler import RastreioRequestHandler
from server.launcher import ThreadedTCPServer, abrir_navegador
from server.logger import (
    ServerLogQueue,
    StreamToQueue,
    sanitize_log_message,
)
from server.security import resolve_safe_path
from server.service import UpdateManager


class TestServerConfig(unittest.TestCase):
    """Testes da classe de configuração ServerConfig."""

    def test_valores_padrao(self):
        cfg = ServerConfig()
        self.assertEqual(cfg.host, "127.0.0.1")
        self.assertEqual(cfg.port, 8000)
        self.assertEqual(cfg.html_file, "relatorio_rastreio.html")
        self.assertEqual(cfg.cooldown_seconds, 150)
        self.assertEqual(cfg.auto_update_interval, 2700)
        self.assertIn(".html", cfg.allowed_extensions)
        self.assertIn(".js", cfg.allowed_extensions)
        self.assertEqual(cfg.url, "http://localhost:8000")

    def test_url_customizada(self):
        cfg = ServerConfig(host="192.168.1.50", port=8080)
        self.assertEqual(cfg.url, "http://192.168.1.50:8080")

    def test_from_env_com_variaveis(self):
        env = {"SERVER_HOST": "0.0.0.0", "SERVER_PORT": "9000"}
        with patch.dict(os.environ, env):
            cfg = ServerConfig.from_env(base_dir=PROJECT_ROOT)
            self.assertEqual(cfg.host, "0.0.0.0")
            self.assertEqual(cfg.port, 9000)
            self.assertEqual(cfg.base_dir, PROJECT_ROOT)

    def test_from_env_porta_invalida_usa_fallback(self):
        env = {"SERVER_PORT": "invalido"}
        with patch.dict(os.environ, env):
            cfg = ServerConfig.from_env()
            self.assertEqual(cfg.port, 8000)


class TestServerSecurity(unittest.TestCase):
    """Testes de segurança, resolução de arquivos e anti-path traversal."""

    def setUp(self):
        self.base_dir = PROJECT_ROOT

    def test_path_vazio_ou_none(self):
        self.assertIsNone(resolve_safe_path(self.base_dir, ""))
        self.assertIsNone(resolve_safe_path(self.base_dir, None))

    def test_bloqueio_path_traversal_simples(self):
        self.assertIsNone(resolve_safe_path(self.base_dir, "../outra_pasta/teste.txt"))
        self.assertIsNone(resolve_safe_path(self.base_dir, "../../.env"))
        self.assertIsNone(resolve_safe_path(self.base_dir, "..\\..\\.env"))

    def test_bloqueio_path_traversal_url_encoded(self):
        self.assertIsNone(resolve_safe_path(self.base_dir, "%2e%2e%2f.env"))
        self.assertIsNone(resolve_safe_path(self.base_dir, "..%2f..%2fsecrets.txt"))

    def test_bloqueio_arquivo_env(self):
        self.assertIsNone(resolve_safe_path(self.base_dir, ".env"))
        self.assertIsNone(resolve_safe_path(self.base_dir, "/.env"))
        self.assertIsNone(resolve_safe_path(self.base_dir, "Arquivos/.env"))

    def test_bloqueio_arquivos_ocultos(self):
        self.assertIsNone(resolve_safe_path(self.base_dir, ".gitignore"))
        self.assertIsNone(resolve_safe_path(self.base_dir, ".git/config"))

    def test_bloqueio_arquivos_python(self):
        self.assertIsNone(resolve_safe_path(self.base_dir, "run.py"))
        self.assertIsNone(resolve_safe_path(self.base_dir, "Arquivos/servidor_rastreio.py"))

    def test_bloqueio_scripts_executaveis(self):
        self.assertIsNone(resolve_safe_path(self.base_dir, "ABRIR_PAINEL.bat"))

    def test_arquivo_inexistente_retorna_none(self):
        self.assertIsNone(resolve_safe_path(self.base_dir, "arquivo_que_nao_existe_12345.html"))

    def test_arquivo_valido_existente_permitido(self):
        # Cria um arquivo temporário no base_dir para testar resolução bem-sucedida
        arquivo_teste = self.base_dir / "teste_seguranca.html"
        try:
            arquivo_teste.write_text("<html><body>OK</body></html>", encoding="utf-8")
            resolvido = resolve_safe_path(
                base_dir=self.base_dir,
                requested_url_path="/teste_seguranca.html",
                allowed_extensions={".html"},
            )
            self.assertIsNotNone(resolvido)
            self.assertEqual(resolvido.resolve(), arquivo_teste.resolve())
        finally:
            if arquivo_teste.exists():
                arquivo_teste.unlink()


class TestServerLogger(unittest.TestCase):
    """Testes de logging, sanitização e fila SSE."""

    def test_sanitizacao_tokens_e_credenciais(self):
        msg = "Requisição efetuada com token=abc123xyz456 e Bearer secret_token_999"
        limpa = sanitize_log_message(msg)
        self.assertNotIn("abc123xyz456", limpa)
        self.assertNotIn("secret_token_999", limpa)
        self.assertIn("token=***", limpa)
        self.assertIn("Bearer ***", limpa)

    def test_fila_put_e_get(self):
        queue = ServerLogQueue(maxsize=10)
        queue.put("Mensagem de teste")
        item = queue.get(timeout=0.5)
        self.assertEqual(item, "Mensagem de teste")

    def test_fila_ignora_mensagens_vazias(self):
        queue = ServerLogQueue(maxsize=10)
        queue.put("   ")
        queue.put("")
        with self.assertRaises(Exception):
            queue.get(timeout=0.1)

    def test_stream_to_queue_espelha_saida(self):
        mock_stream = io.StringIO()
        log_queue = ServerLogQueue(maxsize=10)
        stream_wrapper = StreamToQueue(mock_stream, log_queue)

        stream_wrapper.write("Log impresso via print\n")
        stream_wrapper.flush()

        self.assertIn("Log impresso", mock_stream.getvalue())
        self.assertEqual(log_queue.get(timeout=0.5), "Log impresso via print")


class TestUpdateManager(unittest.TestCase):
    """Testes de cooldown, disparo e agendamento no UpdateManager."""

    def setUp(self):
        self.config = ServerConfig(cooldown_seconds=10, auto_update_interval=100)
        self.log_queue = ServerLogQueue()

    def test_estado_inicial_permite_atualizacao(self):
        manager = UpdateManager(self.config, self.log_queue, runner_fn=lambda: None)
        self.assertTrue(manager.can_update())
        self.assertEqual(manager.remaining_cooldown(), 0)

    def test_trigger_update_inicia_cooldown(self):
        chamou = []

        def fake_runner():
            chamou.append(True)

        manager = UpdateManager(self.config, self.log_queue, runner_fn=fake_runner)
        sucesso = manager.trigger_update(motivo="TESTE")
        self.assertTrue(sucesso)

        # Aguarda thread terminar
        time.sleep(0.1)
        self.assertTrue(chamou)
        self.assertGreater(manager.remaining_cooldown(), 0)
        self.assertFalse(manager.can_update())

    def test_bloqueio_de_segunda_atualizacao_em_cooldown(self):
        manager = UpdateManager(self.config, self.log_queue, runner_fn=lambda: None)
        self.assertTrue(manager.trigger_update())
        # Segunda tentativa imediata deve ser rejeitada
        self.assertFalse(manager.trigger_update())

    def test_get_proxima_atualizacao_info(self):
        manager = UpdateManager(self.config, self.log_queue, runner_fn=lambda: None)
        info = manager.get_proxima_atualizacao_info()
        self.assertIn("remaining", info)
        self.assertIn("next_time", info)
        self.assertGreater(info["remaining"], 0)

    def test_get_status_info(self):
        manager = UpdateManager(self.config, self.log_queue, runner_fn=lambda: None)
        status = manager.get_status_info()
        self.assertTrue(status["sucesso"])
        self.assertEqual(status["status"], "pronto")
        self.assertIn("cooldown_remaining", status)

    def test_tratamento_de_excecao_no_runner_nao_trava_lock(self):
        def falha_runner():
            raise RuntimeError("Erro simulado")

        manager = UpdateManager(self.config, self.log_queue, runner_fn=falha_runner)
        manager.trigger_update()
        time.sleep(0.1)
        # Lock de execução deve ter sido liberado no finally
        self.assertFalse(manager._is_updating)


class DummyHandler(RastreioRequestHandler):
    """Handler adaptado para testes unitários com I/O em memória."""

    def __init__(self, request_bytes: bytes, command: str, path: str):
        self.rfile = io.BytesIO(request_bytes)
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


class TestRastreioRequestHandler(unittest.TestCase):
    """Testes unitários das rotas HTTP do RastreioRequestHandler."""

    def setUp(self):
        self.config = ServerConfig(base_dir=PROJECT_ROOT, cooldown_seconds=10)
        self.log_queue = ServerLogQueue()
        self.manager = UpdateManager(self.config, self.log_queue, runner_fn=lambda: None)

        RastreioRequestHandler.server_config = self.config
        RastreioRequestHandler.log_queue = self.log_queue
        RastreioRequestHandler.update_manager = self.manager

    def test_options_cors(self):
        handler = DummyHandler(b"", "OPTIONS", "/")
        handler.do_OPTIONS()
        output = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("HTTP/1.0 200", output)
        self.assertIn("Access-Control-Allow-Origin: *", output)

    def test_get_proxima_atualizacao(self):
        handler = DummyHandler(b"", "GET", "/proxima-atualizacao")
        handler.do_GET()
        output = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("HTTP/1.0 200", output)
        self.assertIn("application/json", output)
        self.assertIn('"remaining"', output)
        self.assertIn('"next_time"', output)

    def test_get_api_status(self):
        handler = DummyHandler(b"", "GET", "/api/status")
        handler.do_GET()
        output = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("HTTP/1.0 200", output)
        self.assertIn('"sucesso": true', output)

    def test_post_atualizar_sucesso_e_cooldown_429(self):
        # 1. Primeira chamada: deve iniciar (200)
        handler1 = DummyHandler(b"", "POST", "/atualizar")
        handler1.do_POST()
        out1 = handler1.wfile.getvalue().decode("utf-8")
        self.assertIn("HTTP/1.0 200", out1)
        self.assertIn('"status": "started"', out1)

        # 2. Segunda chamada imediata: deve retornar 429 Too Many Requests
        handler2 = DummyHandler(b"", "POST", "/atualizar")
        handler2.do_POST()
        out2 = handler2.wfile.getvalue().decode("utf-8")
        self.assertIn("HTTP/1.0 429", out2)
        self.assertIn('"remaining"', out2)

    def test_post_rota_invalida_retorna_404(self):
        handler = DummyHandler(b"", "POST", "/rota_inexistente")
        handler.do_POST()
        out = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("HTTP/1.0 404", out)

    def test_get_path_traversal_bloqueado_com_403(self):
        handler = DummyHandler(b"", "GET", "/../../.env")
        handler.do_GET()
        out = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("HTTP/1.0 403", out)
        self.assertIn("Acesso negado", out)

    def test_get_arquivo_python_bloqueado_com_403(self):
        handler = DummyHandler(b"", "GET", "/run.py")
        handler.do_GET()
        out = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("HTTP/1.0 403", out)

    def test_get_arquivo_inexistente_retorna_404(self):
        handler = DummyHandler(b"", "GET", "/arquivo_inexistente_xyz.html")
        handler.do_GET()
        out = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("HTTP/1.0 404", out)

    def test_get_pagina_principal_raiz(self):
        handler = DummyHandler(b"", "GET", "/")
        handler.do_GET()
        out = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("HTTP/1.0 200", out)
        self.assertIn("text/html", out)


class TestLauncher(unittest.TestCase):
    """Testes do módulo launcher."""

    @patch("webbrowser.open")
    def test_abrir_navegador_invoca_webbrowser(self, mock_browser_open):
        abrir_navegador("http://localhost:8000", delay=0.01)
        time.sleep(0.05)
        mock_browser_open.assert_called_once_with("http://localhost:8000")

    def test_threaded_tcp_server_properties(self):
        self.assertTrue(ThreadedTCPServer.allow_reuse_address)
        self.assertTrue(ThreadedTCPServer.daemon_threads)


class TestFachadaRetrocompatibilidade(unittest.TestCase):
    """Garante que Arquivos/servidor_rastreio.py mantém a interface legada."""

    def test_importacao_e_simbolos_fachada(self):
        import servidor_rastreio

        self.assertEqual(servidor_rastreio.PORT, 8000)
        self.assertEqual(servidor_rastreio.HTML_FILE, "relatorio_rastreio.html")
        self.assertTrue(callable(servidor_rastreio.iniciar_servidor))
        self.assertTrue(callable(servidor_rastreio.open_browser))
        self.assertIs(servidor_rastreio.RastreioHandler, RastreioRequestHandler)


if __name__ == "__main__":
    unittest.main()
