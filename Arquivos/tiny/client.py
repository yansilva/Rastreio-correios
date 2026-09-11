"""Cliente HTTP para comunicação exclusiva com a API do Tiny ERP."""
import logging
import time
from typing import Any

import requests

from .config import TinyConfig
from .exceptions import (
    TinyAPIError,
    TinyAuthError,
    TinyConnectionError,
    TinyTimeoutError,
)

logger = logging.getLogger("tiny.client")


class TinyClient:
    """Responsável unicamente pela comunicação HTTP com a API do Tiny ERP."""

    def __init__(self, config: TinyConfig | None = None):
        self.config = config or TinyConfig()
        if not self.config.token:
            logger.error("Tentativa de inicializar TinyClient sem credencial de acesso configurada.")
            raise TinyAuthError(
                "Token do Tiny ERP não configurado. Defina a variável de ambiente TOKEN_TINY ou passe explicitamente na configuração."
            )

    def pesquisar_pedidos(
        self,
        data_inicial: str,
        data_final: str,
        pagina: int = 1,
        sort: str = "DESC",
    ) -> dict[str, Any]:
        """
        Consulta uma página de pedidos no Tiny ERP no intervalo de datas informado.
        
        Retorna o dicionário completo deserializado do JSON da API.
        """
        params = {
            "token": self.config.token,
            "formato": self.config.formato,
            "dataInicial": data_inicial,
            "dataFinal": data_final,
            "pagina": pagina,
            "sort": sort,
        }

        logger.debug(
            "Enviando requisição para Tiny pedidos.pesquisa.php (página %d, período: %s a %s)",
            pagina,
            data_inicial,
            data_final,
        )

        try:
            response = requests.get(
                self.config.url_pesquisa,
                params=params,
                timeout=self.config.timeout_segundos,
            )
        except requests.exceptions.Timeout as exc:
            logger.error("Timeout de %ss excedido na chamada ao Tiny ERP", self.config.timeout_segundos)
            raise TinyTimeoutError(
                f"Tempo limite de {self.config.timeout_segundos}s excedido ao consultar o Tiny ERP."
            ) from exc
        except requests.exceptions.RequestException as exc:
            logger.error("Erro de conexão com o Tiny ERP: %s", exc)
            raise TinyConnectionError(f"Falha de conexão com a API do Tiny ERP: {exc}") from exc

        if response.status_code != 200:
            logger.error("Tiny API retornou status HTTP %d: %s", response.status_code, response.text[:200])
            raise TinyAPIError(
                f"Erro na resposta HTTP da API do Tiny (código {response.status_code})",
                status_code=response.status_code,
            )

        try:
            data = response.json()
        except Exception as exc:
            logger.error("Resposta do Tiny ERP não pôde ser deserializada como JSON: %s", exc)
            raise TinyAPIError("Resposta do Tiny ERP não é um JSON válido.") from exc

        return data

    def pesquisar_todos_pedidos(
        self,
        data_inicial: str,
        data_final: str,
    ) -> list[dict[str, Any]]:
        """
        Itera automaticamente pelas páginas da API do Tiny coletando todos os pedidos do período.
        
        Trata o erro padrão da API quando uma consulta não contém registros adicionais.
        """
        logger.info("Iniciando busca de pedidos no Tiny ERP de %s até %s", data_inicial, data_final)
        pagina = 1
        num_paginas = 1
        todos_pedidos: list[dict[str, Any]] = []

        while pagina <= num_paginas:
            data = self.pesquisar_pedidos(data_inicial, data_final, pagina=pagina)
            retorno = data.get("retorno", {})

            if retorno.get("status") == "Erro":
                erros = retorno.get("erros", [])
                # Se não houver registros, o Tiny retorna o erro: 'A consulta não retornou registros'
                if any("A consulta não retornou registros" in str(e.get("erro", "")) for e in erros):
                    logger.debug("Nenhum outro registro encontrado na página %d. Fim da paginação.", pagina)
                    break
                else:
                    logger.error("Erro reportado pela API do Tiny: %s", erros)
                    raise TinyAPIError(f"Erro na API do Tiny: {erros}", detalhes=erros)

            pedidos_pagina = retorno.get("pedidos", [])
            todos_pedidos.extend(pedidos_pagina)

            try:
                num_paginas = int(retorno.get("numero_paginas", 1))
            except (ValueError, TypeError):
                num_paginas = 1

            if pagina >= num_paginas:
                break

            pagina += 1
            time.sleep(self.config.delay_paginacao_segundos)

        logger.info("Consulta ao Tiny finalizada com sucesso. Total de pedidos coletados: %d", len(todos_pedidos))
        return todos_pedidos
