"""Módulo de logging e fila de streaming SSE para o servidor web."""
import logging
import queue
import re
import threading
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
    """Mensagens do servidor para o streaming SSE.

    Cada conexão SSE se inscreve com `inscrever()` e recebe uma cópia de cada mensagem: com duas abas
    abertas (PC e celular), as duas veem todas as linhas. `put()` nunca levanta exceção, nem com várias
    threads gravando ao mesmo tempo, porque a cópia para as filas é feita inteira dentro da trava.
    """

    def __init__(self, maxsize: int = 1000):
        self._maxsize = maxsize
        self._assinantes: list[queue.Queue] = []
        self._trava = threading.Lock()

    def inscrever(self) -> queue.Queue:
        """Cria uma fila para uma conexão SSE, que recebe as mensagens a partir de agora."""
        inscrita: queue.Queue = queue.Queue(maxsize=self._maxsize)
        with self._trava:
            self._assinantes.append(inscrita)
        return inscrita

    def cancelar(self, inscrita: queue.Queue) -> None:
        """Remove a fila de uma conexão encerrada; não recebe mais mensagens."""
        with self._trava:
            if inscrita in self._assinantes:
                self._assinantes.remove(inscrita)

    def assinantes(self) -> int:
        """Quantas conexões SSE estão inscritas agora."""
        with self._trava:
            return len(self._assinantes)

    def put(self, message: str) -> None:
        """Copia a mensagem para cada assinante, se não for vazia. Não levanta exceção."""
        text = str(message).strip()
        if not text:
            return
        clean = sanitize_log_message(text)
        with self._trava:
            for fila in self._assinantes:
                _colocar_descartando_antiga(fila, clean)


def _colocar_descartando_antiga(fila: queue.Queue, mensagem: str) -> None:
    """Coloca na fila; se estiver cheia, descarta a mensagem mais antiga. Nunca levanta exceção."""
    try:
        fila.put_nowait(mensagem)
        return
    except queue.Full:
        pass
    try:
        fila.get_nowait()
    except queue.Empty:
        pass
    try:
        fila.put_nowait(mensagem)
    except queue.Full:
        pass


class StreamToQueue:
    """Redireciona saídas de print/stdout para a fila SSE sem interromper o stdout original."""

    def __init__(self, original_stream: Any, log_queue: ServerLogQueue):
        self.original_stream = original_stream
        self.log_queue = log_queue

    def write(self, data: str) -> int:
        if self.original_stream and hasattr(self.original_stream, "write"):
            try:
                self.original_stream.write(data)
                if hasattr(self.original_stream, "flush"):
                    self.original_stream.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                # O pipe de saída padrão foi desconectado pelo processo pai ou terminal
                self.original_stream = None

        if data and str(data).strip():
            self.log_queue.put(data)
        return len(data) if isinstance(data, str) else 0

    def flush(self) -> None:
        if self.original_stream and hasattr(self.original_stream, "flush"):
            try:
                self.original_stream.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                self.original_stream = None

    @property
    def encoding(self) -> str:
        if self.original_stream and hasattr(self.original_stream, "encoding"):
            return getattr(self.original_stream, "encoding", "utf-8") or "utf-8"
        return "utf-8"

    @property
    def errors(self) -> str:
        if self.original_stream and hasattr(self.original_stream, "errors"):
            return getattr(self.original_stream, "errors", "replace") or "replace"
        return "replace"

    def isatty(self) -> bool:
        if self.original_stream and hasattr(self.original_stream, "isatty"):
            try:
                return bool(self.original_stream.isatty())
            except Exception:
                return False
        return False
