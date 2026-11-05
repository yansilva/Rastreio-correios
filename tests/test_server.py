"""Suíte de testes automatizados para a camada de servidor web e painel.

Todos os testes utilizam mocks (unittest.mock) sem abrir portas reais na rede
nem abrir abas de navegador.
Compatível tanto com `pytest` quanto com `python -m unittest`.
"""
import email.message
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
from server.launcher import ThreadedTCPServer, abrir_navegador, is_port_in_use
from server.logger import (
    ServerLogQueue,
    StreamToQueue,
    sanitize_log_message,
)
from server.security import (
    host_permitido,
    ip_na_rede_local,
    origem_confiavel,
    resolve_public_path,
    resolve_safe_path,
)
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

    def test_fonte_inter_embutida_e_liberada_pelo_servidor(self):
        permitidas = ServerConfig().allowed_extensions
        resolvido = resolve_safe_path(
            base_dir=self.base_dir,
            requested_url_path="/web/fonts/InterVariable.woff2",
            allowed_extensions=permitidas,
        )
        self.assertIsNotNone(resolvido)
        self.assertGreater(resolvido.stat().st_size, 100_000)


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

    def test_stream_to_queue_tolera_pipe_quebrado_winerror_233(self):
        class BrokenPipeStream:
            def write(self, data):
                err = OSError("Não há processo no outro extremo do pipe")
                err.winerror = 233
                raise err

            def flush(self):
                err = OSError("Não há processo no outro extremo do pipe")
                err.winerror = 233
                raise err

        log_queue = ServerLogQueue(maxsize=10)
        stream_wrapper = StreamToQueue(BrokenPipeStream(), log_queue)

        # Não deve lançar exceção mesmo com WinError 233
        written = stream_wrapper.write("Mensagem durante WinError 233\n")
        stream_wrapper.flush()

        self.assertEqual(written, len("Mensagem durante WinError 233\n"))
        self.assertEqual(log_queue.get(timeout=0.5), "Mensagem durante WinError 233")
        self.assertIsNone(stream_wrapper.original_stream)

    def test_stream_to_queue_tolera_broken_pipe_error(self):
        class BrokenStream:
            def write(self, data):
                raise BrokenPipeError("Broken pipe")

            def flush(self):
                raise BrokenPipeError("Broken pipe")

        log_queue = ServerLogQueue(maxsize=10)
        stream_wrapper = StreamToQueue(BrokenStream(), log_queue)

        written = stream_wrapper.write("Mensagem durante BrokenPipe\n")
        stream_wrapper.flush()

        self.assertEqual(written, len("Mensagem durante BrokenPipe\n"))
        self.assertEqual(log_queue.get(timeout=0.5), "Mensagem durante BrokenPipe")
        self.assertIsNone(stream_wrapper.original_stream)

    def test_stream_to_queue_propriedades_stream(self):
        mock_stream = io.StringIO()
        log_queue = ServerLogQueue(maxsize=10)
        stream_wrapper = StreamToQueue(mock_stream, log_queue)

        self.assertIsInstance(stream_wrapper.encoding, str)
        self.assertIsInstance(stream_wrapper.errors, str)
        self.assertFalse(stream_wrapper.isatty())


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

    def __init__(
        self,
        request_bytes: bytes,
        command: str,
        path: str,
        client_address: tuple = ("127.0.0.1", 12345),
        headers: dict | None = None,
    ):
        self.rfile = io.BytesIO(request_bytes)
        self.wfile = io.BytesIO()
        self.client_address = client_address
        self.command = command
        self.path = path
        self.requestline = f"{command} {path} HTTP/1.1"
        self.request_version = "HTTP/1.1"
        # headers como dict: Host padrão de acesso legítimo, sobrescrito pelo teste.
        # headers como lista de pares: exatamente esses cabeçalhos (ex.: Host duplicado ou ausente).
        if isinstance(headers, list):
            pares = headers
        else:
            base = {"Host": "127.0.0.1:8000"}
            base.update(headers or {})
            pares = list(base.items())
        self.headers = email.message.Message()
        for nome, valor in pares:
            self.headers[nome] = valor
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
        self.assertNotIn("Access-Control-Allow-Origin", output)

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

    def test_get_arquivo_python_fora_da_lista_retorna_404(self):
        handler = DummyHandler(b"", "GET", "/run.py")
        handler.do_GET()
        out = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("HTTP/1.0 404", out)

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

    def test_is_port_in_use(self):
        # Testa chamada com porta improvável de estar em uso (ex: 59199)
        self.assertFalse(is_port_in_use(59199, "127.0.0.1"))


class TestFachadaRetrocompatibilidade(unittest.TestCase):
    """Garante que Arquivos/servidor_rastreio.py mantém a interface legada."""

    def test_importacao_e_simbolos_fachada(self):
        import servidor_rastreio

        self.assertEqual(servidor_rastreio.PORT, 8000)
        self.assertEqual(servidor_rastreio.HTML_FILE, "relatorio_rastreio.html")
        self.assertTrue(callable(servidor_rastreio.iniciar_servidor))
        self.assertTrue(callable(servidor_rastreio.open_browser))
        self.assertIs(servidor_rastreio.RastreioHandler, RastreioRequestHandler)


class TestListaDePermissao(unittest.TestCase):
    """Só páginas da raiz, alerta_frete.js e web/ podem ser servidos."""

    def setUp(self):
        self.permitidas = ServerConfig().allowed_extensions

    def test_dados_internos_nao_resolvem(self):
        for caminho in (
            "Arquivos/rastreios_cache.json",
            "Arquivos/server/handler.py",
            "tests/test_server.py",
            ".env",
            ".git/config",
            "run.py",
        ):
            with self.subTest(caminho=caminho):
                self.assertIsNone(resolve_public_path(PROJECT_ROOT, caminho, self.permitidas))

    def test_paginas_web_e_alerta_resolvem(self):
        self.assertIsNotNone(resolve_public_path(PROJECT_ROOT, "relatorio_rastreio.html", self.permitidas))
        self.assertIsNotNone(resolve_public_path(PROJECT_ROOT, "web/css/main.css", self.permitidas))
        self.assertIsNotNone(resolve_public_path(PROJECT_ROOT, "alert_frete.js", self.permitidas))

    def test_dupla_codificacao_nao_vira_traversal(self):
        # %252e%252e decodifica uma vez para "%2e%2e" (texto literal), nunca para ".."
        self.assertIsNone(resolve_public_path(PROJECT_ROOT, "/web/%252e%252e/run.py", self.permitidas))
        self.assertIsNone(resolve_safe_path(PROJECT_ROOT, "/web/%252e%252e/run.py", self.permitidas))

    def test_dupla_codificacao_no_servidor_retorna_404(self):
        for caminho in ("/web/%252e%252e/run.py", "/web/%252e%252e%252frun.py"):
            with self.subTest(caminho=caminho):
                handler = DummyHandler(b"", "GET", caminho)
                handler.do_GET()
                out = handler.wfile.getvalue().decode("utf-8")
                self.assertTrue("HTTP/1.0 404" in out or "HTTP/1.0 403" in out)

    def test_traversal_dentro_de_web_bloqueado(self):
        self.assertIsNone(
            resolve_public_path(PROJECT_ROOT, "web/../Arquivos/rastreios_cache.json", self.permitidas)
        )
        self.assertIsNone(
            resolve_public_path(PROJECT_ROOT, "web/..%2fArquivos%2frastreios_cache.json", self.permitidas)
        )


class TestRedeLocal(unittest.TestCase):
    """IP do cliente e origem do POST."""

    def test_ips_locais_permitidos(self):
        for ip in ("127.0.0.1", "::1", "192.168.1.50", "10.0.0.7", "172.16.5.5", "::ffff:192.168.0.9"):
            with self.subTest(ip=ip):
                self.assertTrue(ip_na_rede_local(ip))

    def test_ips_publicos_bloqueados(self):
        for ip in ("8.8.8.8", "200.160.0.1", "172.32.0.1", "", "lixo"):
            with self.subTest(ip=ip):
                self.assertFalse(ip_na_rede_local(ip))

    def test_origem_so_do_proprio_host(self):
        host = "192.168.1.50:8000"
        self.assertTrue(origem_confiavel(host, "http://192.168.1.50:8000", None))
        self.assertTrue(origem_confiavel(host, None, "http://192.168.1.50:8000/relatorio_rastreio.html"))
        self.assertTrue(origem_confiavel(host, None, None))
        self.assertFalse(origem_confiavel(host, "http://site-externo.example", None))
        self.assertFalse(origem_confiavel(host, "null", None))
        self.assertFalse(origem_confiavel(host, None, "http://site-externo.example/pagina"))


class TestHandlerRedeLocal(unittest.TestCase):
    """Rotas do handler com IP externo, Origin de outro site e arquivos fora da lista."""

    def setUp(self):
        self.config = ServerConfig(base_dir=PROJECT_ROOT, cooldown_seconds=10)
        self.log_queue = ServerLogQueue()
        self.manager = UpdateManager(self.config, self.log_queue, runner_fn=lambda: None)

        RastreioRequestHandler.server_config = self.config
        RastreioRequestHandler.log_queue = self.log_queue
        RastreioRequestHandler.update_manager = self.manager

    def _saida(self, handler):
        return handler.wfile.getvalue().decode("utf-8")

    def test_post_de_ip_publico_retorna_403_e_nao_atualiza(self):
        handler = DummyHandler(b"", "POST", "/atualizar", client_address=("8.8.8.8", 5000))
        handler.do_POST()
        self.assertIn("HTTP/1.0 403", self._saida(handler))
        self.assertTrue(self.manager.can_update())

    def test_post_com_origin_de_outro_site_retorna_403(self):
        handler = DummyHandler(
            b"",
            "POST",
            "/atualizar",
            client_address=("192.168.1.20", 5000),
            headers={"Host": "192.168.1.50:8000", "Origin": "http://site-externo.example"},
        )
        handler.do_POST()
        self.assertIn("HTTP/1.0 403", self._saida(handler))
        self.assertTrue(self.manager.can_update())

    def test_post_com_origin_do_proprio_host_aceito(self):
        handler = DummyHandler(
            b"",
            "POST",
            "/atualizar",
            client_address=("192.168.1.20", 5000),
            headers={"Host": "192.168.1.50:8000", "Origin": "http://192.168.1.50:8000"},
        )
        handler.do_POST()
        self.assertIn("HTTP/1.0 200", self._saida(handler))

    def test_get_de_ip_publico_retorna_403(self):
        handler = DummyHandler(b"", "GET", "/web/css/main.css", client_address=("8.8.8.8", 5000))
        handler.do_GET()
        self.assertIn("HTTP/1.0 403", self._saida(handler))

    def test_cache_json_de_arquivos_retorna_404(self):
        handler = DummyHandler(b"", "GET", "/Arquivos/rastreios_cache.json")
        handler.do_GET()
        self.assertIn("HTTP/1.0 404", self._saida(handler))

    def test_env_e_tests_retornam_404(self):
        for caminho in ("/.env", "/tests/test_server.py", "/.git/config"):
            with self.subTest(caminho=caminho):
                handler = DummyHandler(b"", "GET", caminho)
                handler.do_GET()
                self.assertIn("HTTP/1.0 404", self._saida(handler))

    def test_css_do_painel_e_pagina_principal_retornam_200(self):
        for caminho in ("/web/css/main.css", "/relatorio_rastreio.html"):
            with self.subTest(caminho=caminho):
                handler = DummyHandler(b"", "GET", caminho)
                handler.do_GET()
                self.assertIn("HTTP/1.0 200", self._saida(handler))

    def test_head_nao_serve_arquivos(self):
        handler = DummyHandler(b"", "HEAD", "/Arquivos/rastreios_cache.json")
        handler.do_HEAD()
        self.assertIn("HTTP/1.0 405", self._saida(handler))


class TestHostPermitido(unittest.TestCase):
    """Cabeçalho Host: só nomes deste servidor (anti DNS rebinding)."""

    def test_hosts_locais_e_privados_aceitos(self):
        for host in (
            "localhost",
            "localhost:8000",
            "127.0.0.1",
            "127.0.0.1:8000",
            "[::1]:8000",
            "192.168.15.45",
            "192.168.15.45:8000",
            "10.0.0.7:8000",
            "172.16.5.5:8000",
        ):
            with self.subTest(host=host):
                self.assertTrue(host_permitido(host, 8000))

    def test_ip_configurado_do_servidor_aceito(self):
        self.assertTrue(host_permitido("200.160.0.1:8000", 8000, "200.160.0.1"))
        self.assertFalse(host_permitido("200.160.0.1:8000", 8000, "0.0.0.0"))

    def test_dominios_e_ips_publicos_recusados(self):
        for host in ("evil.example", "evil.example:8000", "8.8.8.8:8000", "localhost.evil.example", "", None):
            with self.subTest(host=host):
                self.assertFalse(host_permitido(host, 8000))

    def test_host_com_arroba_recusado(self):
        self.assertFalse(host_permitido("evil.example@127.0.0.1:8000", 8000))

    def test_host_com_barra_recusado(self):
        self.assertFalse(host_permitido("127.0.0.1/evil:8000", 8000))

    def test_host_com_query_e_fragmento_recusado(self):
        self.assertFalse(host_permitido("127.0.0.1?x#:8000", 8000))

    def test_porta_diferente_da_configurada_recusada(self):
        self.assertFalse(host_permitido("127.0.0.1:9999", 8000))

    def test_host_malformado_recusado(self):
        self.assertFalse(host_permitido("127.0.0.1:porta_invalida", 8000))
        self.assertFalse(host_permitido("[::1", 8000))


class TestHandlerHost(unittest.TestCase):
    """Host do cabeçalho nas rotas GET e POST do handler."""

    def setUp(self):
        self.config = ServerConfig(base_dir=PROJECT_ROOT, cooldown_seconds=10)
        self.log_queue = ServerLogQueue()
        self.manager = UpdateManager(self.config, self.log_queue, runner_fn=lambda: None)

        RastreioRequestHandler.server_config = self.config
        RastreioRequestHandler.log_queue = self.log_queue
        RastreioRequestHandler.update_manager = self.manager

    def _saida(self, handler):
        return handler.wfile.getvalue().decode("utf-8")

    def test_host_evil_bloqueado_em_get(self):
        handler = DummyHandler(b"", "GET", "/", headers={"Host": "evil.example"})
        handler.do_GET()
        out = self._saida(handler)
        self.assertIn("HTTP/1.0 403", out)
        self.assertNotIn("<html", out.lower())

    def test_host_evil_bloqueado_em_post_e_nao_atualiza(self):
        handler = DummyHandler(b"", "POST", "/atualizar", headers={"Host": "evil.example"})
        handler.do_POST()
        self.assertIn("HTTP/1.0 403", self._saida(handler))
        self.assertTrue(self.manager.can_update())

    def test_host_evil_bloqueado_em_options_e_head(self):
        handler = DummyHandler(b"", "OPTIONS", "/", headers={"Host": "evil.example"})
        handler.do_OPTIONS()
        self.assertIn("HTTP/1.0 403", self._saida(handler))

        handler = DummyHandler(b"", "HEAD", "/", headers={"Host": "evil.example"})
        handler.do_HEAD()
        self.assertIn("HTTP/1.0 403", self._saida(handler))

    def test_sem_cabecalho_host_recusado_com_403(self):
        for metodo, rota in (("GET", "/"), ("POST", "/atualizar"), ("HEAD", "/"), ("OPTIONS", "/")):
            with self.subTest(metodo=metodo):
                handler = DummyHandler(b"", metodo, rota, headers=[])
                getattr(handler, f"do_{metodo}")()
                self.assertIn("HTTP/1.0 403", self._saida(handler))

    def test_host_duplicado_local_primeiro_e_recusado(self):
        handler = DummyHandler(
            b"", "GET", "/", headers=[("Host", "127.0.0.1:8000"), ("Host", "evil.example")]
        )
        handler.do_GET()
        self.assertIn("HTTP/1.0 403", self._saida(handler))

    def test_host_duplicado_hostil_primeiro_e_recusado(self):
        handler = DummyHandler(
            b"", "GET", "/", headers=[("Host", "evil.example"), ("Host", "127.0.0.1:8000")]
        )
        handler.do_GET()
        self.assertIn("HTTP/1.0 403", self._saida(handler))

    def test_host_duplicado_local_nao_e_aceito_nem_isolado(self):
        handler = DummyHandler(
            b"", "GET", "/", headers=[("Host", "127.0.0.1:8000"), ("Host", "127.0.0.1:8000")]
        )
        handler.do_GET()
        self.assertIn("HTTP/1.0 403", self._saida(handler))

    def test_host_127_com_porta_aceito(self):
        handler = DummyHandler(b"", "GET", "/", headers={"Host": "127.0.0.1:8000"})
        handler.do_GET()
        self.assertIn("HTTP/1.0 200", self._saida(handler))

    def test_host_localhost_com_porta_aceito(self):
        handler = DummyHandler(b"", "GET", "/", headers={"Host": "localhost:8000"})
        handler.do_GET()
        self.assertIn("HTTP/1.0 200", self._saida(handler))

    def test_host_ip_da_rede_com_porta_aceito(self):
        handler = DummyHandler(
            b"",
            "GET",
            "/",
            client_address=("192.168.15.20", 5000),
            headers={"Host": "192.168.15.45:8000"},
        )
        handler.do_GET()
        self.assertIn("HTTP/1.0 200", self._saida(handler))

    def test_post_com_host_da_rede_e_origem_propria_aceito(self):
        handler = DummyHandler(
            b"",
            "POST",
            "/atualizar",
            client_address=("192.168.15.20", 5000),
            headers={"Host": "192.168.15.45:8000", "Origin": "http://192.168.15.45:8000"},
        )
        handler.do_POST()
        self.assertIn("HTTP/1.0 200", self._saida(handler))


class TestBatsERedeLocal(unittest.TestCase):
    """Painel padrão só escuta neste PC; o .bat do celular escuta na rede."""

    def test_painel_padrao_nao_expoe_rede(self):
        texto = (PROJECT_ROOT / "ABRIR_PAINEL.bat").read_text(encoding="utf-8", errors="replace")
        self.assertNotIn("SERVER_HOST=0.0.0.0", texto)

    def test_bat_celular_expoe_rede_local(self):
        texto = (PROJECT_ROOT / "ABRIR_PAINEL_CELULAR.bat").read_text(encoding="utf-8", errors="replace")
        self.assertIn("SERVER_HOST=0.0.0.0", texto)
        self.assertIn("run.py", texto)

    def test_url_de_rede_nao_mostra_localhost_quando_0_0_0_0(self):
        cfg = ServerConfig(host="0.0.0.0", port=8000)
        self.assertTrue(cfg.url_rede.startswith("http://"))
        self.assertTrue(cfg.url_rede.endswith(":8000"))
        self.assertNotIn("localhost", cfg.url_rede)
        self.assertEqual(cfg.url, "http://localhost:8000")


if __name__ == "__main__":
    unittest.main()
