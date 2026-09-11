"""Módulo de logging e fila de streaming SSE para o servidor web."""
import logging
import queue
import re
from typing import Any

logger = logging.getLogger("rastreio.server")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Padrões para mascarar dados sensíveis nos logs do SSE
SENSITIVE_PATTERNS = [
    (re.compile(r"token=[a-zA-Z0-9_\-\.]+", re.IGNORECASE), "token=***"),
    (re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]+", re.IGNORECASE), "Bearer ***"),
    (re.compile(r"Basic\s+[a-zA-Z0-9_\-\=]+", re.IGNORECASE), "Basic ***"),
    (re.compile(r"api_key=[a-zA-Z0-9_\-]+", re.IGNORECASE), "api_key=***"),
]


def sanitize_log_message(message: str) -> str:
    """Mascara eventuais dados sensíveis antes de enviar para o cliente web."""
    sanitized = message
    for pattern, repl in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(repl, sanitized)
    return sanitized


class ServerLogQueue:
    """Gerencia a fila em memória de mensagens para streaming via Server-Sent Events (SSE)."""

    def __init__(self, maxsize: int = 1000):
        self._queue: queue.Queue = queue.Queue(maxsize=maxsize)

    def put(self, message: str) -> None:
        """Adiciona mensagem à fila se não for vazia."""
        text = str(message).strip()
        if text:
            clean = sanitize_log_message(text)
            try:
                self._queue.put_nowait(clean)
            except queue.Full:
                # Descarta mensagens antigas se a fila estiver lotada
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    pass
                self._queue.put_nowait(clean)

    def get(self, timeout: float | None = 1.0) -> str:
        """Obtém mensagem da fila ou levanta queue.Empty."""
        return self._queue.get(timeout=timeout)


class StreamToQueue:
    """Redireciona saídas de print/stdout para a fila SSE sem interromper o stdout original."""

    def __init__(self, original_stream: Any, log_queue: ServerLogQueue):
        self.original_stream = original_stream
        self.log_queue = log_queue

    def write(self, data: str) -> None:
        if self.original_stream and hasattr(self.original_stream, "write"):
            self.original_stream.write(data)
            if hasattr(self.original_stream, "flush"):
                self.original_stream.flush()
        if data and data.strip():
            self.log_queue.put(data)

    def flush(self) -> None:
        if self.original_stream and hasattr(self.original_stream, "flush"):
            self.original_stream.flush()
