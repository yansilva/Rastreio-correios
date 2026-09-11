"""Cliente HTTP para consulta de preço e prazo de frete nos Correios.

Responsabilidade exclusiva: comunicação HTTP.
NÃO monta HTML, NÃO escolhe melhor opção, NÃO gera relatório.
"""
import logging
from typing import Any, Dict, Optional

import requests

from correios.client import CorreiosClient
from .config import FreteConfig
from .exceptions import (
    FreteAPIError,
    FreteConnectionError,
    FreteServicoIndisponivelError,
    FreteTimeoutError,
)

logger = logging.getLogger("frete.client")


class FreteClient:
    """Comunicação HTTP com as APIs de preço e prazo dos Correios.

    Reutiliza o CorreiosClient da Etapa 3 para autenticação (token Bearer),
    evitando duplicação de credenciais e lógica de token.
    """

    def __init__(
        self,
        correios_client: Optional[CorreiosClient] = None,
        config: Optional[FreteConfig] = None,
    ):
        self.correios_client = correios_client or CorreiosClient()
        self.config = config or FreteConfig()

    def _headers(self) -> Dict[str, str]:
        """Monta headers com token Bearer atualizado."""
        token = self.correios_client.gerar_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    def _fazer_requisicao(self, url: str, params: Dict[str, Any], timeout: Optional[float] = None) -> Dict[str, Any]:
        """Executa GET com tratamento de erro padronizado.

        Retorna o JSON da resposta ou levanta exceção apropriada.
        """
        timeout = timeout or self.config.timeout_segundos

        try:
            response = requests.get(url, headers=self._headers(), params=params, timeout=timeout)
        except requests.exceptions.Timeout as exc:
            logger.error("Timeout de %ss ao consultar %s", timeout, url)
            raise FreteTimeoutError(
                f"Tempo limite de {timeout}s excedido ao consultar frete."
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            logger.error("Erro de conexão ao consultar %s: %s", url, exc)
            raise FreteConnectionError(f"Falha de conexão ao consultar frete: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            logger.error("Erro HTTP inesperado ao consultar %s: %s", url, exc)
            raise FreteConnectionError(f"Erro de rede ao consultar frete: {exc}") from exc

        # Serviço indisponível para esta rota
        if response.status_code in (400, 422):
            logger.info("Serviço indisponível para rota (HTTP %d): %s", response.status_code, url)
            raise FreteServicoIndisponivelError(
                f"Serviço indisponível para esta rota (HTTP {response.status_code})"
            )

        # Token expirado — tenta renovar uma vez
        if response.status_code == 401:
            logger.warning("Token expirado na consulta de frete. Renovando...")
            self.correios_client.gerar_token(forcar_renovacao=True)
            try:
                response = requests.get(url, headers=self._headers(), params=params, timeout=timeout)
            except requests.exceptions.RequestException as exc:
                raise FreteConnectionError(f"Falha na retentativa: {exc}") from exc

            if response.status_code == 401:
                raise FreteAPIError("Falha de autenticação persistente (HTTP 401)", status_code=401)

        # Erros HTTP genéricos
        if response.status_code == 403:
            raise FreteAPIError("Acesso negado à API de frete (HTTP 403)", status_code=403)
        if response.status_code == 429:
            raise FreteAPIError("Limite de requisições excedido (HTTP 429)", status_code=429)
        if response.status_code >= 500:
            raise FreteAPIError(
                f"Erro interno na API dos Correios (HTTP {response.status_code})",
                status_code=response.status_code,
                detalhes=response.text[:500],
            )
        if response.status_code != 200:
            raise FreteAPIError(
                f"Resposta inesperada da API de frete (HTTP {response.status_code})",
                status_code=response.status_code,
                detalhes=response.text[:500],
            )

        # Parse do JSON
        try:
            return response.json()
        except Exception as exc:
            logger.error("JSON inválido na resposta de frete: %s", exc)
            raise FreteAPIError("Resposta da API de frete não é JSON válido.") from exc

    def obter_preco(self, cep_destino: str, codigo_servico: str) -> Dict[str, Any]:
        """Consulta o preço de um serviço para um CEP de destino.

        Retorna o dicionário bruto da API com campos como pcFinal, pcBase, etc.
        """
        logger.info("Consultando preço para serviço %s, destino CEP %s", codigo_servico, cep_destino)

        url = self.config.url_preco.format(coProduto=codigo_servico)
        params = {
            "cepOrigem": self.config.cep_origem,
            "cepDestino": cep_destino,
            "psObjeto": self.config.peso_gramas,
            "tpObjeto": self.config.tipo_objeto,
            "comprimento": self.config.comprimento,
            "largura": self.config.largura,
            "altura": self.config.altura,
        }

        return self._fazer_requisicao(url, params)

    def obter_prazo(self, cep_destino: str, codigo_servico: str) -> Dict[str, Any]:
        """Consulta o prazo de entrega de um serviço para um CEP de destino.

        Retorna o dicionário bruto da API com campos como prazoEntrega, msgPrazo, etc.
        """
        logger.info("Consultando prazo para serviço %s, destino CEP %s", codigo_servico, cep_destino)

        url = self.config.url_prazo.format(coProduto=codigo_servico)
        params = {
            "cepOrigem": self.config.cep_origem,
            "cepDestino": cep_destino,
        }

        return self._fazer_requisicao(url, params)
