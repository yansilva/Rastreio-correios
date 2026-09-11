"""Inicialização, lifecycle e execução do servidor HTTP multithreaded."""
import socketserver
import sys
import threading
import time
import webbrowser

from .config import ServerConfig
from .handler import RastreioRequestHandler
from .logger import ServerLogQueue, StreamToQueue, logger
from .service import UpdateManager


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Servidor TCP multithreaded para requisições concorrentes."""

    allow_reuse_address = True
    daemon_threads = True


def abrir_navegador(url: str, delay: float = 1.5) -> None:
    """Abre o navegador padrão na URL do painel após um pequeno delay."""
    def _abrir():
        time.sleep(delay)
        try:
            logger.info(f"Abrindo navegador em: {url}")
            webbrowser.open(url)
        except Exception as exc:
            logger.warning(f"Não foi possível abrir o navegador automaticamente: {exc}")

    threading.Thread(target=_abrir, daemon=True).start()


def iniciar_servidor(
    config: ServerConfig | None = None,
    abrir_browser: bool = True,
    capturar_stdout: bool = True,
) -> None:
    """Inicia o servidor web local para o painel de rastreio.

    Args:
        config: Configurações do servidor (se omitido, lê de variáveis de ambiente/padrão).
        abrir_browser: Se True, agenda abertura do navegador na URL do painel.
        capturar_stdout: Se True, espelha prints para a fila de streaming SSE.
    """
    cfg = config or ServerConfig.from_env()
    log_queue = ServerLogQueue()
    update_manager = UpdateManager(config=cfg, log_queue=log_queue)

    # Injeta instâncias no handler HTTP
    RastreioRequestHandler.server_config = cfg
    RastreioRequestHandler.log_queue = log_queue
    RastreioRequestHandler.update_manager = update_manager

    # Inicia atualização automática a cada 45 min
    update_manager.start_auto_update_loop()

    # Redireciona stdout de forma transparente para logs SSE caso solicitado
    original_stdout = sys.stdout
    if capturar_stdout:
        sys.stdout = StreamToQueue(original_stream=original_stdout, log_queue=log_queue)

    server_address = (cfg.host if cfg.host not in ("127.0.0.1", "") else "", cfg.port)

    logger.info("=" * 60)
    logger.info("INICIANDO SERVIDOR DO PAINEL DE RASTREIO E FRETE")
    logger.info("=" * 60)
    logger.info(f"Diretório base: {cfg.base_dir}")
    logger.info(f"URL de acesso:  {cfg.url}")
    logger.info("Pressione Ctrl+C para encerrar o servidor.")
    logger.info("=" * 60)

    if abrir_browser:
        abrir_navegador(cfg.url, delay=1.5)

    try:
        with ThreadedTCPServer(server_address, RastreioRequestHandler) as httpd:
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                logger.info("\nEncerrando servidor solicitado pelo usuário...")
            finally:
                update_manager.stop()
                httpd.server_close()
    finally:
        if capturar_stdout:
            sys.stdout = original_stdout
        logger.info("Servidor finalizado com sucesso.")
