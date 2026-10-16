"""Gerenciamento de atualizações periódicas e manuais do painel."""
import importlib
import sys
import threading
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

from .config import ServerConfig
from .logger import ServerLogQueue, logger


class UpdateManager:
    """Controla cooldown, disparos de atualização e agendamento automático."""

    def __init__(
        self,
        config: ServerConfig,
        log_queue: ServerLogQueue,
        runner_fn: Callable[[], Any] | None = None,
        regenerator_fn: Callable[[], Any] | None = None,
    ):
        self.config = config
        self.log_queue = log_queue
        self.runner_fn = runner_fn or self._default_runner
        self.regenerator_fn = regenerator_fn or self._default_regenerator
        self.last_update_time: float = 0.0
        self.next_update_time: float = time.time() + self.config.auto_update_interval
        self._is_updating: bool = False
        self._lock = threading.Lock()
        self._auto_thread: threading.Thread | None = None
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

    def get_proxima_atualizacao_info(self) -> dict[str, Any]:
        """Retorna dados estruturados sobre a próxima atualização automática."""
        remaining = max(0, int(self.next_update_time - time.time()))
        if self.next_update_time > 0:
            next_time_str = datetime.fromtimestamp(self.next_update_time).strftime("%H:%M")
        else:
            next_time_str = "--:--"
        return {"remaining": remaining, "next_time": next_time_str}

    def get_status_info(self) -> dict[str, Any]:
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

    def regenerate(self) -> tuple[bool, str]:
        """Reconstrói o relatório a partir do último retorno em cache, sem chamar o Tiny nem os Correios.

        Não usa o cooldown (não consome APIs), mas não roda junto de uma atualização em andamento.
        """
        with self._lock:
            if self._is_updating:
                return False, "Há uma atualização em andamento. Tente de novo quando ela terminar."
            self._is_updating = True

        try:
            self.log_queue.put("🔁 REGERANDO O RELATÓRIO A PARTIR DO CACHE")
            self.regenerator_fn()
            self.log_queue.put("✅ RELATÓRIO REGERADO")
            logger.info("Relatório regerado a partir do cache.")
            return True, "Relatório regerado a partir dos últimos dados consultados."
        except Exception as exc:
            logger.error(f"Erro ao regerar o relatório: {exc}")
            self.log_queue.put(f"❌ [ERRO] Não foi possível regerar o relatório: {exc}")
            return False, str(exc)
        finally:
            with self._lock:
                self._is_updating = False

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
    def _default_regenerator() -> None:
        """Regera o HTML com os dados em cache, recarregando os módulos para aplicar mudanças de template."""
        dir_arquivos = str(ServerConfig.from_env().base_dir / "Arquivos")
        if dir_arquivos not in sys.path:
            sys.path.append(dir_arquivos)

        import consulta_correios

        importlib.reload(consulta_correios)
        if consulta_correios.processar(usar_cache=True) is False:
            raise RuntimeError("não há dados em cache; clique em Atualizar Dados primeiro")

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
        if executar_rastreio.main() is False:
            raise RuntimeError("a atualização falhou; veja as mensagens de erro acima no console")
