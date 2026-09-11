"""Cliente HTTP para comunicação exclusiva com as APIs dos Correios."""
import base64
import logging
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
            response = requests.post(
                self.config.url_token,
                headers=headers,
                json=payload,
                timeout=self.config.timeout_segundos,
            )
        except requests.exceptions.Timeout as exc:
            logger.error("Tempo limite excedido na autenticação dos Correios (%ss)", self.config.timeout_segundos)
            raise CorreiosTimeoutError(
                f"Tempo limite de {self.config.timeout_segundos}s excedido ao autenticar nos Correios."
            ) from exc
        except requests.exceptions.RequestException as exc:
            logger.error("Falha de rede ao conectar com o serviço de autenticação dos Correios")
            raise CorreiosConnectionError(f"Falha de conexão com os Correios: {exc}") from exc

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
                f"Falha de autenticação nos Correios (HTTP {response.status_code}): {response.text}"
            )
        else:
            logger.error("Resposta inesperada no serviço de autenticação dos Correios (HTTP %d)", response.status_code)
            raise CorreiosAPIError(
                f"Erro ao obter token dos Correios: {response.status_code} - {response.text}",
                status_code=response.status_code,
                detalhes=response.text,
            )

    def consultar_objeto(self, objeto: str, token: str | None = None) -> dict[str, Any] | None:
        """
        Consulta os eventos de rastreamento de um objeto na API SRO dos Correios.
        
        Retorna o dicionário de dados do objeto ou None caso não haja informações.
        """
        token_ativo = token or self.gerar_token()
        headers = {
            "Authorization": f"Bearer {token_ativo}",
            "Accept": "application/json",
        }
        url = self.config.url_rastreio.format(objeto=objeto)

        logger.debug("Consultando rastreamento do objeto %s", objeto)

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=self.config.timeout_segundos,
            )
        except requests.exceptions.Timeout as exc:
            logger.error("Tempo limite excedido ao rastrear objeto %s", objeto)
            raise CorreiosTimeoutError(f"Tempo limite excedido ao rastrear {objeto}.") from exc
        except requests.exceptions.RequestException as exc:
            logger.error("Erro de conexão ao rastrear objeto %s", objeto)
            raise CorreiosConnectionError(f"Falha de conexão ao rastrear {objeto}: {exc}") from exc

        # Se a sessão expirou (401), tenta renovar uma vez
        if response.status_code == 401 and token is None:
            logger.warning("Sessão expirada ao consultar objeto %s. Renovando autorização...", objeto)
            novo_token = self.gerar_token(forcar_renovacao=True)
            headers["Authorization"] = f"Bearer {novo_token}"
            response = requests.get(url, headers=headers, timeout=self.config.timeout_segundos)

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
