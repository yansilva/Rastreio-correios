"""Handler HTTP do servidor com roteamento, SSE e proteção anti-traversal."""
import http.server
import json
import mimetypes
import queue
from typing import Any

from .config import ServerConfig
from .logger import ServerLogQueue, logger
from .security import resolve_safe_path
from .service import UpdateManager


class RastreioRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handler HTTP customizado para o painel de rastreio e frete."""

    # Referências globais/padrão injetáveis pelo servidor
    server_config: ServerConfig = ServerConfig()
    log_queue: ServerLogQueue = ServerLogQueue()
    update_manager: UpdateManager | None = None

    def end_headers(self) -> None:
        """Adiciona headers CORS e de segurança padrão."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        """Responde requisições preflight CORS."""
        self.send_response(200)
        self.end_headers()

    def do_GET(self) -> None:
        """Roteia requisições GET."""
        clean_path = self.path.split("?")[0].strip()

        # Rota 1: Streaming de logs via Server-Sent Events (SSE)
        if clean_path == "/logs":
            self._handle_sse_logs()
            return

        # Rota 2: Consulta do timer de próxima atualização
        if clean_path == "/proxima-atualizacao":
            self._handle_proxima_atualizacao()
            return

        # Rota 3: Status geral da API interna
        if clean_path == "/api/status":
            self._handle_api_status()
            return

        # Rota 4: Página principal do painel (/ ou /relatorio_rastreio.html)
        html_file = self.server_config.html_file
        if clean_path in ("/", f"/{html_file}"):
            self._serve_main_html()
            return

        # Rota 5: Arquivos estáticos e relatórios auxiliares (validando segurança)
        self._serve_static_file(clean_path)

    def do_POST(self) -> None:
        """Roteia requisições POST."""
        clean_path = self.path.split("?")[0].strip()

        if clean_path == "/atualizar":
            self._handle_atualizar()
            return

        if clean_path == "/api/demo":
            self._handle_gerar_demo()
            return

        self._send_json_response({"sucesso": False, "erro": "Rota não encontrada"}, status=404)

    # ---------------------------------------------------------
    # Handlers Internos de Rotas
    # ---------------------------------------------------------

    def _handle_gerar_demo(self) -> None:
        """Gera relatórios de demonstração via API."""
        try:
            import sys
            dir_arquivos = str(self.server_config.base_dir / "Arquivos")
            if dir_arquivos not in sys.path:
                sys.path.append(dir_arquivos)

            from demo_data import gerar_dados_demonstracao
            gerar_dados_demonstracao(self.server_config.base_dir)
            self._send_json_response(
                {"sucesso": True, "mensagem": "Dados de demonstração gerados com sucesso."},
                status=200,
            )
        except Exception as exc:
            self._send_json_response({"sucesso": False, "erro": str(exc)}, status=500)

    def _handle_sse_logs(self) -> None:
        """Gerencia o streaming SSE de logs."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        try:
            while True:
                try:
                    message = self.log_queue.get(timeout=1.0)
                    line = f"data: {message}\n\n".encode()
                    self.wfile.write(line)
                    self.wfile.flush()
                except queue.Empty:
                    # Envia heartbeat keep-alive
                    self.wfile.write(b": keep-alive\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as exc:
            logger.debug(f"Conexão SSE encerrada: {exc}")

    def _handle_proxima_atualizacao(self) -> None:
        """Retorna JSON com remaining e next_time."""
        if self.update_manager:
            data = self.update_manager.get_proxima_atualizacao_info()
        else:
            data = {"remaining": 0, "next_time": "--:--"}
        self._send_json_response(data, status=200)

    def _handle_api_status(self) -> None:
        """Retorna status geral da API."""
        if self.update_manager:
            data = self.update_manager.get_status_info()
        else:
            data = {"sucesso": True, "status": "pronto"}
        self._send_json_response(data, status=200)

    def _handle_atualizar(self) -> None:
        """Dispara atualização se fora do cooldown."""
        if not self.update_manager:
            self._send_json_response({"status": "error", "erro": "UpdateManager inativo"}, status=500)
            return

        rem = self.update_manager.remaining_cooldown()
        if rem > 0:
            self._send_json_response({"remaining": rem}, status=429)
            return

        sucesso = self.update_manager.trigger_update(motivo="SOLICITAÇÃO VIA WEB")
        if sucesso:
            self._send_json_response({"status": "started"}, status=200)
        else:
            rem = self.update_manager.remaining_cooldown()
            self._send_json_response({"remaining": rem, "erro": "Atualização já em andamento"}, status=429)

    def _serve_main_html(self) -> None:
        """Serve o arquivo HTML principal do painel ou tela de boas-vindas/onboarding."""
        caminho_html = self.server_config.base_dir / self.server_config.html_file
        if caminho_html.is_file():
            self._serve_file(caminho_html, content_type="text/html; charset=utf-8")
        else:
            onboarding_html = (
                "<!DOCTYPE html>\n"
                "<html lang='pt-br'>\n"
                "<head>\n"
                "    <meta charset='UTF-8'>\n"
                "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>\n"
                "    <title>Bem-vindo ao Painel de Rastreio Correios</title>\n"
                "    <link rel='stylesheet' href='web/css/main.css'>\n"
                "    <link rel='stylesheet' href='web/css/components.css'>\n"
                "</head>\n"
                "<body>\n"
                "    <div class='floating-actions'>\n"
                "        <button id='btnTheme' class='btn-theme' aria-label='Alternar tema claro/escuro'>\n"
                "            <span id='btnThemeText'>🌙 Escuro</span>\n"
                "        </button>\n"
                "    </div>\n"
                "    <div class='container' style='max-width: 760px; margin-top: 40px; text-align: center;'>\n"
                "        <h1>📦 Rastreio Correios & Tiny ERP</h1>\n"
                "        <p class='meta' style='font-size: 1.05rem; margin-bottom: 30px;'>\n"
                "            Sistema automatizado de rastreamento, auditoria de prazos e cotação de fretes.\n"
                "        </p>\n"
                "        <div class='order-card' style='padding: 32px 28px; text-align: left;'>\n"
                "            <h2 style='margin-top: 0; color: var(--color-primary); font-size: 1.3rem;'>⚡ Primeiro Acesso Detectado</h2>\n"
                "            <p style='color: var(--color-text-muted); line-height: 1.6;'>\n"
                "                Nenhum relatório de rastreio foi encontrado no momento. Escolha uma das opções abaixo para começar:\n"
                "            </p>\n"
                "            <div style='display: flex; flex-direction: column; gap: 14px; margin: 25px 0;'>\n"
                "                <button type='button' id='btnCarregarDemo' class='btn-action' style='justify-content: center; width: 100%; font-size: 1rem; padding: 14px 20px;'>\n"
                "                    🚀 Carregar Dados de Demonstração (Modo Portfólio)\n"
                "                </button>\n"
                "                <button type='button' id='btnSincronizar' class='btn-action btn-theme' style='justify-content: center; width: 100%; font-size: 0.95rem; padding: 12px 20px;'>\n"
                "                    🔄 Sincronizar com APIs Reais (Tiny ERP & Correios)\n"
                "                </button>\n"
                "            </div>\n"
                "            <div style='background: var(--color-header-bg); border-radius: 8px; padding: 16px 20px; font-size: 0.88rem; color: var(--color-text-muted); border: 1px solid var(--color-border);'>\n"
                "                <strong>💡 Dica para Avaliadores e Recrutadores:</strong><br>\n"
                "                O botão <em>Carregar Dados de Demonstração</em> gera instantaneamente 10 pedidos realistas (em trânsito, atrasados com alerta, entregues e aguardando retirada) para permitir a exploração completa de filtros, busca instantânea e dark mode sem necessidade de credenciais de produção.\n"
                "            </div>\n"
                "        </div>\n"
                "    </div>\n"
                "    <script src='web/js/app.js'></script>\n"
                "    <script>\n"
                "        document.getElementById('btnCarregarDemo').addEventListener('click', function() {\n"
                "            var btn = this;\n"
                "            btn.disabled = true;\n"
                "            btn.textContent = '⏳ Gerando demonstração...';\n"
                "            fetch('/api/demo', { method: 'POST' })\n"
                "                .then(function(res) { return res.json(); })\n"
                "                .then(function(data) {\n"
                "                    if (data.sucesso) {\n"
                "                        window.location.reload();\n"
                "                    } else {\n"
                "                        alert('Erro ao carregar demonstração: ' + (data.erro || 'Desconhecido'));\n"
                "                        btn.disabled = false;\n"
                "                        btn.textContent = '🚀 Carregar Dados de Demonstração (Modo Portfólio)';\n"
                "                    }\n"
                "                })\n"
                "                .catch(function(err) {\n"
                "                    alert('Erro de conexão: ' + err);\n"
                "                    btn.disabled = false;\n"
                "                    btn.textContent = '🚀 Carregar Dados de Demonstração (Modo Portfólio)';\n"
                "                });\n"
                "        });\n"
                "        document.getElementById('btnSincronizar').addEventListener('click', function() {\n"
                "            var btn = this;\n"
                "            btn.disabled = true;\n"
                "            btn.textContent = '⏳ Iniciando sincronização...';\n"
                "            fetch('/atualizar', { method: 'POST' })\n"
                "                .then(function(res) { return res.json(); })\n"
                "                .then(function() {\n"
                "                    alert('Sincronização iniciada! Acompanhe o terminal ou aguarde a conclusão.');\n"
                "                    setTimeout(function() { window.location.reload(); }, 3000);\n"
                "                })\n"
                "                .catch(function(err) {\n"
                "                    alert('Erro ao acionar sincronização: ' + err);\n"
                "                    btn.disabled = false;\n"
                "                    btn.textContent = '🔄 Sincronizar com APIs Reais (Tiny ERP & Correios)';\n"
                "                });\n"
                "        });\n"
                "    </script>\n"
                "</body>\n"
                "</html>"
            )
            self._send_bytes_response(onboarding_html.encode("utf-8"), content_type="text/html; charset=utf-8", status=200)

    def _serve_static_file(self, requested_url_path: str) -> None:
        """Serve arquivo estático validado contra Path Traversal e arquivos confidenciais."""
        safe_file = resolve_safe_path(
            base_dir=self.server_config.base_dir,
            requested_url_path=requested_url_path,
            allowed_extensions=self.server_config.allowed_extensions,
        )

        if not safe_file:
            # Rejeita com 404 (ou 403 se foi tentativa explícita de traversal/bloqueado)
            if ".." in requested_url_path or ".env" in requested_url_path or ".py" in requested_url_path:
                self._send_json_response({"sucesso": False, "erro": "Acesso negado"}, status=403)
            else:
                self._send_json_response({"sucesso": False, "erro": "Arquivo não encontrado"}, status=404)
            return

        # Determina mimetype
        mime, _ = mimetypes.guess_type(str(safe_file))
        if not mime:
            mime = "application/octet-stream"
        if mime.startswith("text/") or mime in ("application/javascript", "application/json"):
            content_type = f"{mime}; charset=utf-8"
        else:
            content_type = mime

        self._serve_file(safe_file, content_type=content_type)

    def _serve_file(self, file_path, content_type: str = "text/html; charset=utf-8") -> None:
        """Lê e envia arquivo com status 200."""
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self._send_bytes_response(content, content_type=content_type, status=200)
        except Exception as exc:
            logger.error(f"Erro ao ler arquivo {file_path}: {exc}")
            self._send_json_response({"sucesso": False, "erro": "Erro ao carregar arquivo"}, status=500)

    def _send_bytes_response(self, content: bytes, content_type: str, status: int = 200) -> None:
        """Envia resposta binária com código HTTP e cabeçalhos."""
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        try:
            self.wfile.write(content)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _send_json_response(self, data: Any, status: int = 200) -> None:
        """Envia resposta JSON codificada em UTF-8."""
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self._send_bytes_response(body, content_type="application/json; charset=utf-8", status=status)

    def log_message(self, format: str, *args: Any) -> None:
        """Substitui o log padrão de requisições pelo logger configurado."""
        # Evita poluição de SSE heartbeats e debugs excessivos no console
        path = getattr(self, "path", "")
        if path.startswith("/logs") or path.startswith("/proxima-atualizacao"):
            return
        addr = self.client_address[0] if hasattr(self, "client_address") and self.client_address else "127.0.0.1"
        logger.debug(f"{addr} - {format % args}")
