"""Serviço de consulta de frete — regras de negócio e comparação de opções.

Combina preço e prazo, normaliza resultados e aplica regras de comparação.
"""
import logging
import time

from .client import FreteClient
from .config import FreteConfig
from .exceptions import FreteError, FreteServicoIndisponivelError
from .models import OpcaoFrete

logger = logging.getLogger("frete.service")


class FreteService:
    """Orquestra consultas de preço e prazo e produz OpcaoFrete normalizados."""

    def __init__(self, client: FreteClient | None = None, config: FreteConfig | None = None):
        self.config = config or FreteConfig()
        self.client = client or FreteClient(config=self.config)

    def _consultar_servico(self, cep_destino: str, codigo: str, nome: str) -> OpcaoFrete:
        """Consulta preço e prazo de um único serviço, retornando OpcaoFrete."""

        # --- Preço ---
        try:
            dados_preco = self.client.obter_preco(cep_destino, codigo)
        except FreteServicoIndisponivelError:
            logger.info("Serviço %s (%s) indisponível para CEP %s", nome, codigo, cep_destino)
            return OpcaoFrete(
                codigo=codigo,
                nome=nome,
                disponivel=False,
                erro="Indisponível para esta rota",
            )
        except FreteError as exc:
            logger.error("Erro ao consultar preço do serviço %s: %s", codigo, exc)
            return OpcaoFrete(
                codigo=codigo,
                nome=nome,
                disponivel=False,
                erro=str(exc),
            )

        # Extrai preço da resposta (chain de fallbacks conforme API)
        preco_str = str(
            dados_preco.get("pcFinal",
                dados_preco.get("pcBase",
                    dados_preco.get("vlBaseCalculoImposto", "0")))
        )
        preco = OpcaoFrete.parse_preco(preco_str)

        # --- Prazo ---
        prazo_dias = None
        msg_prazo = None

        try:
            dados_prazo = self.client.obter_prazo(cep_destino, codigo)
            prazo_dias = OpcaoFrete.parse_prazo(dados_prazo.get("prazoEntrega"))

            # Mensagem de observação do prazo (vários campos possíveis)
            msg_prazo = (
                dados_prazo.get("msgPrazo")
                or dados_prazo.get("txObservacao")
                or dados_prazo.get("msgObservacao")
                or dados_prazo.get("observacao")
                or dados_prazo.get("txMsgObs")
            )
        except FreteServicoIndisponivelError:
            logger.info("Prazo indisponível para serviço %s, CEP %s", codigo, cep_destino)
        except FreteError as exc:
            logger.warning("Não foi possível obter prazo para serviço %s: %s", codigo, exc)

        return OpcaoFrete(
            codigo=codigo,
            nome=nome,
            disponivel=True,
            preco=preco,
            prazo_dias=prazo_dias,
            msg_prazo=msg_prazo,
            erro=None,
        )

    def consultar_opcoes(self, cep_destino: str, intervalo_segundos: float = 0.3) -> list[OpcaoFrete]:
        """Consulta preço e prazo de todos os serviços configurados para um CEP.

        Args:
            cep_destino: CEP de destino (8 dígitos, sem hífen).
            intervalo_segundos: Pausa entre consultas para respeitar rate limit.

        Returns:
            Lista de OpcaoFrete com todos os serviços (disponíveis ou não).
        """
        logger.info("Iniciando consulta de frete para CEP %s", cep_destino)
        opcoes: list[OpcaoFrete] = []

        for i, (codigo, nome) in enumerate(self.config.servicos.items()):
            opcao = self._consultar_servico(cep_destino, codigo, nome)
            opcoes.append(opcao)

            # Rate limit entre consultas (exceto na última)
            if i < len(self.config.servicos) - 1 and intervalo_segundos > 0:
                time.sleep(intervalo_segundos)

        disponiveis = sum(1 for o in opcoes if o.disponivel)
        if disponiveis == 0:
            logger.warning("Nenhuma opção de frete retornada para CEP %s", cep_destino)
        else:
            logger.info("%d opção(ões) disponível(is) para CEP %s", disponiveis, cep_destino)

        return opcoes

    @staticmethod
    def filtrar_disponiveis(opcoes: list[OpcaoFrete]) -> list[OpcaoFrete]:
        """Retorna apenas as opções com disponivel=True."""
        return [o for o in opcoes if o.disponivel]

    @staticmethod
    def mais_barato(opcoes: list[OpcaoFrete]) -> OpcaoFrete | None:
        """Retorna a opção disponível com menor preço, ou None se nenhuma disponível."""
        disponiveis = [o for o in opcoes if o.disponivel and o.preco is not None]
        if not disponiveis:
            return None
        return min(disponiveis, key=lambda o: o.preco)

    @staticmethod
    def mais_rapido(opcoes: list[OpcaoFrete]) -> OpcaoFrete | None:
        """Retorna a opção disponível com menor prazo, ou None se nenhuma disponível."""
        disponiveis = [o for o in opcoes if o.disponivel and o.prazo_dias is not None]
        if not disponiveis:
            return None
        return min(disponiveis, key=lambda o: o.prazo_dias)
