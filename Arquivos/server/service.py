"""Gerenciamento de atualizações periódicas e manuais do painel."""
from datetime import datetime
import importlib
import sys
import threading
import time
from typing import Any, Callable, Dict, Optional

from .config import ServerConfig
from .logger import ServerLogQueue, logger


class UpdateManager:
    """Controla cooldown, disparos de atualização e agendamento automático."""

    def __init__(
        self,
        config: ServerConfig,
        log_queue: ServerLogQueue,
        runner_fn: Optional[Callable[[], Any]] = None,
    ):
        self.config = config
        self.log_queue = log_queue
        self.runner_fn = runner_fn or self._default_runner
        self.last_update_time: float = 0.0
        self.next_update_time: float = time.time() + self.config.auto_update_interval
        self._is_updating: bool = False
        self._lock = threading.Lock()
        self._auto_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def remaining_cooldown(self) -> int:
        """Retorna os segundos restantes de cooldown (0 se livre)."""
        time_passed = time.time() - self.last_update_time
        if time_passed < self.config.cooldown_seconds:
            return max(0, int(self.config.cooldown_seconds - time_passed))
        return 0

    def can_update(self) -> bool:
        """Indica se uma nova atualização pode ser solicitada."""
        return self.remaining_cooldown() == 0 and not self._is_updating

    def get_proxima_atualizacao_info(self) -> Dict[str, Any]:
        """Retorna dados estruturados sobre a próxima atualização automática."""
        remaining = max(0, int(self.next_update_time - time.time()))
        if self.next_update_time > 0:
            next_time_str = datetime.fromtimestamp(self.next_update_time).strftime("%H:%M")
        else:
            next_time_str = "--:--"
        return {"remaining": remaining, "next_time": next_time_str}

    def get_status_info(self) -> Dict[str, Any]:
        """Retorna o status geral do servidor e serviços."""
        prox = self.get_proxima_atualizacao_info()
        return {
            "sucesso": True,
            "status": "atualizando" if self._is_updating else "pronto",
            "is_updating": self._is_updating,
            "cooldown_remaining": self.remaining_cooldown(),
            "proxima_atualizacao": prox,
            "html_disponivel": (self.config.base_dir / self.config.html_file).is_file(),
            "servidor_url": self.config.url,
        }

    def trigger_update(self, motivo: str = "MANUAL VIA WEB") -> bool:
        """Dispara atualização em background se o cooldown permitir."""
        with self._lock:
            if not self.can_update():
                return False
            self._is_updating = True

        logger.info(f"Iniciando atualização de pedidos e fretes ({motivo})...")

        def _worker():
            try:
                self.log_queue.put(f"🚀 INICIANDO PROCESSO: {motivo}")
                self.runner_fn()
                now = time.time()
                self.last_update_time = now
                self.next_update_time = now + self.config.auto_update_interval
                self.log_queue.put("✅ PROCESSO FINALIZADO COM SUCESSO")
                logger.info("Atualização concluída com sucesso.")
            except Exception as exc:
                erro_msg = f"Erro na atualização ({motivo}): {exc}"
                logger.error(erro_msg)
                self.log_queue.put(f"❌ [ERRO] {erro_msg}")
            finally:
                with self._lock:
                    self._is_updating = False

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return True

    def start_auto_update_loop(self) -> None:
        """Inicia loop de atualização automática periódica em thread daemon."""
        if self._auto_thread and self._auto_thread.is_alive():
            return

        def _loop():
            logger.info(
                f"Atualização automática agendada a cada {self.config.auto_update_interval // 60} minutos."
            )
            while not self._stop_event.is_set():
                # Dorme em passos curtos para permitir interrupção rápida
                sleep_start = time.time()
                while (
                    time.time() - sleep_start < self.config.auto_update_interval
                    and not self._stop_event.is_set()
                ):
                    time.sleep(1.0)

                if self._stop_event.is_set():
                    break

                logger.info("Disparando ciclo de atualização automática...")
                self.trigger_update(motivo="AUTOMÁTICA (INTERVALO)")

        self._auto_thread = threading.Thread(target=_loop, daemon=True)
        self._auto_thread.start()

    def stop(self) -> None:
        """Sinaliza parada do loop de atualização."""
        self._stop_event.set()

    @staticmethod
    def _default_runner() -> None:
        """Execução padrão dos serviços integrados."""
        dir_arquivos = str(ServerConfig.from_env().base_dir / "Arquivos")
        if dir_arquivos not in sys.path:
            sys.path.append(dir_arquivos)

        import consulta_correios
        import executar_rastreio

        importlib.reload(consulta_correios)
        importlib.reload(executar_rastreio)
        executar_rastreio.main()
