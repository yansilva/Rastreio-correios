"""Cliente HTTP para comunicação exclusiva com as APIs dos Correios."""
import base64
import logging
import time
from collections.abc import Callable
from typing import Any

import requests

from .config import CorreiosConfig
from .exceptions import (
    CorreiosAPIError,
    CorreiosAuthError,
    CorreiosConnectionError,
    CorreiosTimeoutError,
)

logger = logging.getLogger("correios.client")


class CorreiosClient:
    """Responsável unicamente pela autenticação e comunicação HTTP com a API dos Correios."""

    def __init__(self, config: CorreiosConfig | None = None):
        self.config = config or CorreiosConfig()
        self._token: str | None = None

    def _com_tentativas(self, chamada: Callable[[], requests.Response], descricao: str) -> requests.Response:
        """Repete a chamada quando a conexão cai (reset, abortada); outros erros sobem na hora."""
        tentativas = max(1, self.config.tentativas_conexao)
        for numero in range(1, tentativas + 1):
            try:
                return chamada()
            except requests.exceptions.ConnectionError:
                if numero == tentativas:
                    raise
                espera = self.config.espera_entre_tentativas * numero
                logger.warning(
                    "Conexão com os Correios interrompida (%s). Nova tentativa %d/%d em %.0fs.",
                    descricao,
                    numero + 1,
                    tentativas,
                    espera,
                )
                time.sleep(espera)
        raise AssertionError("inalcançável")  # pragma: no cover

    def gerar_token(self, forcar_renovacao: bool = False) -> str:
        """
        Obtém token de acesso (Bearer) autenticando o contrato nos Correios via Basic Auth.
        
        Reutiliza o token em memória caso já tenha sido gerado, a menos que forçar_renovação seja True.
        """
        if self._token and not forcar_renovacao:
            return self._token

        if not self.config.credenciais_preenchidas():
            logger.error("Credenciais obrigatórias dos Correios não configuradas no ambiente.")
            raise CorreiosAuthError(
                "Credenciais dos Correios não configuradas. Verifique ID_CORREIOS, CONTRATO e CODIGO_ACESSO no .env."
            )

        logger.info("Iniciando autenticação nos Correios...")
        auth_str = f"{self.config.id_correios}:{self.config.codigo_acesso}"
        auth_b64 = base64.b64encode(auth_str.encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/json",
        }
        payload = {"numero": self.config.contrato}

        try:
            response = self._com_tentativas(
                lambda: requests.post(
                    self.config.url_token,
                    headers=headers,
                    json=payload,
                    timeout=self.config.timeout_segundos,
                ),
                "autenticação",
            )
        except requests.exceptions.Timeout as exc:
            logger.error("Tempo limite excedido na autenticação dos Correios (%ss)", self.config.timeout_segundos)
            raise CorreiosTimeoutError(
                f"Tempo limite de {self.config.timeout_segundos}s excedido ao autenticar nos Correios."
            ) from exc
        except requests.exceptions.RequestException as exc:
            # nosemgrep: python-logger-credential-disclosure, rules.python.lang.security.audit.logging.logger-credential-leak.python-logger-credential-disclosure
            logger.error("Falha de rede ao conectar com o serviço de autenticação dos Correios")  # nosemgrep
            raise CorreiosConnectionError(
                f"Falha de conexão com os Correios após {max(1, self.config.tentativas_conexao)} tentativas: {exc}"
            ) from exc

        if response.status_code == 201:
            try:
                dados = response.json()
                token = dados.get("token")
                if not token:
                    raise CorreiosAuthError("Resposta da API de token não contém o campo 'token'.")
                self._token = token
                logger.info("Autenticação nos Correios realizada com sucesso.")
                return token
            except Exception as exc:
                if isinstance(exc, CorreiosAuthError):
                    raise
                raise CorreiosAPIError("Falha ao deserializar JSON da resposta de autenticação.") from exc
        elif response.status_code in (401, 403):
            logger.error("Autenticação rejeitada pelos Correios (HTTP %d)", response.status_code)
            raise CorreiosAuthError(
                f"Falha de autenticação nos Correios (HTTP {response.status_code})."
            )
        else:
            # nosemgrep: python-logger-credential-disclosure, rules.python.lang.security.audit.logging.logger-credential-leak.python-logger-credential-disclosure
            logger.error("Resposta inesperada no serviço de autenticação dos Correios (HTTP %d)", int(response.status_code))  # nosemgrep
            raise CorreiosAPIError(
                f"Erro ao obter token dos Correios (HTTP {response.status_code}).",
                status_code=response.status_code,
            )

    def _consultar_com_token(self, url: str, objeto: str, token: str) -> requests.Response:
        """Uma consulta de rastreio com o token dado, com novas tentativas e erros de rede traduzidos."""
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        try:
            return self._com_tentativas(
                lambda: requests.get(
                    url,
                    headers=headers,
                    timeout=self.config.timeout_segundos,
                ),
                f"rastreio de {objeto}",
            )
        except requests.exceptions.Timeout as exc:
            logger.error("Tempo limite excedido ao rastrear objeto %s", objeto)
            raise CorreiosTimeoutError(f"Tempo limite excedido ao rastrear {objeto}.") from exc
        except requests.exceptions.RequestException as exc:
            logger.error("Erro de conexão ao rastrear objeto %s", objeto)
            raise CorreiosConnectionError(f"Falha de conexão ao rastrear {objeto}: {exc}") from exc

    def consultar_objeto(self, objeto: str, token: str | None = None) -> dict[str, Any] | None:
        """
        Consulta os eventos de rastreamento de um objeto na API SRO dos Correios.
        
        Retorna o dicionário de dados do objeto ou None caso não haja informações.
        """
        token_usado = token or self.gerar_token()
        url = self.config.url_rastreio.format(objeto=objeto)

        logger.debug("Consultando rastreamento do objeto %s", objeto)

        response = self._consultar_com_token(url, objeto, token_usado)

        # Sessão expirou (401): renova o token uma vez e repete. Se o token usado já ficou para trás
        # (outro rastreio renovou antes), basta usar o token guardado, sem nova autenticação
        if response.status_code == 401:
            # nosemgrep: python-logger-credential-disclosure, rules.python.lang.security.audit.logging.logger-credential-leak.python-logger-credential-disclosure
            logger.warning("Sessão expirada ao consultar objeto %s. Renovando autorização...", objeto)  # nosemgrep
            if self._token and token_usado != self._token:
                token_usado = self._token
            else:
                token_usado = self.gerar_token(forcar_renovacao=True)
            response = self._consultar_com_token(url, objeto, token_usado)
            if response.status_code == 401:
                logger.error("Acesso não autorizado ao rastrear %s mesmo após renovar o token", objeto)
                raise CorreiosAuthError(f"Acesso negado ao rastrear {objeto} após renovar o token (HTTP 401).")

        if response.status_code == 200:
            try:
                data = response.json()
                if "objetos" in data and len(data["objetos"]) > 0:
                    return data["objetos"][0]
            except Exception as exc:
                logger.error("Erro ao decodificar JSON de rastreio de %s: %s", objeto, exc)
                raise CorreiosAPIError(f"Resposta de rastreio inválida para {objeto}.") from exc
            return None
        elif response.status_code == 404:
            logger.debug("Objeto %s não encontrado na base dos Correios (HTTP 404)", objeto)
            return None
        elif response.status_code in (401, 403):
            logger.error("Acesso não autorizado ao rastrear %s (HTTP %d)", objeto, response.status_code)
            raise CorreiosAuthError(f"Acesso negado ao rastrear {objeto} (HTTP {response.status_code})")
        else:
            logger.warning("Resposta com status HTTP %d para objeto %s", response.status_code, objeto)
            raise CorreiosAPIError(
                f"Erro na consulta de rastreamento de {objeto} (HTTP {response.status_code})",
                status_code=response.status_code,
                detalhes=response.text,
            )
