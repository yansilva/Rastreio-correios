"""Serviço de gerenciamento e regras de negócio de pedidos do Tiny ERP."""
import csv
import logging
import os
from datetime import datetime, timedelta

from .client import TinyClient
from .config import TinyConfig
from .models import PedidoTiny

logger = logging.getLogger("tiny.orders")


class TinyOrderService:
    """Aplica as regras de negócio de pedidos, filtragens e exportação de relatórios."""

    def __init__(self, client: TinyClient | None = None, config: TinyConfig | None = None):
        self.config = config or TinyConfig()
        self.client = client or TinyClient(config=self.config)

    def buscar_pedidos_recentes(self, dias_atras: int | None = None) -> list[PedidoTiny]:
        """Busca os pedidos expedidos no intervalo de dias informado (padrão 30 dias)."""
        dias = dias_atras if dias_atras is not None else self.config.dias_atras_padrao
        data_final = datetime.now().strftime("%d/%m/%Y")
        data_inicial = (datetime.now() - timedelta(days=dias)).strftime("%d/%m/%Y")

        logger.info("Buscando pedidos no período de %s até %s (%d dias)...", data_inicial, data_final, dias)
        pedidos_brutos = self.client.pesquisar_todos_pedidos(data_inicial, data_final)

        pedidos_convertidos = [PedidoTiny.de_dicionario(p) for p in pedidos_brutos]
        logger.info("Total de pedidos convertidos para PedidoTiny: %d", len(pedidos_convertidos))
        return pedidos_convertidos

    @staticmethod
    def filtrar_pedidos_para_rastreio(pedidos: list[PedidoTiny]) -> list[PedidoTiny]:
        """
        Filtra os pedidos relevantes para rastreamento nos Correios:
        1. Possui código de rastreamento preenchido.
        2. Situação diferente de 'ENTREGUE' e 'CANCELADO' (case insensitive).
        3. Código de rastreamento iniciando com 'A' (padrão Correios PAC/SEDEX).
        """
        pedidos_filtrados: list[PedidoTiny] = []
        for p in pedidos:
            rastreio = (p.codigo_rastreamento or "").strip()
            situacao = (p.situacao or "").strip().upper()

            if rastreio and situacao not in ["ENTREGUE", "CANCELADO"] and rastreio.startswith("A"):
                pedidos_filtrados.append(p)

        logger.info(
            "Filtragem concluída: %d pedidos mantidos de um total de %d",
            len(pedidos_filtrados),
            len(pedidos),
        )
        return pedidos_filtrados

    def exportar_csv(
        self,
        pedidos: list[PedidoTiny],
        caminho_saida: str | None = None,
    ) -> tuple[str, int]:
        """
        Exporta a lista de pedidos filtrados para o arquivo CSV de compatibilidade.
        
        Mantém o cabeçalho original: ['Número do Pedido no Tiny', 'Situação', 'Código de Rastreio'].
        """
        if not caminho_saida:
            pasta_arquivos = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            caminho_saida = os.path.join(pasta_arquivos, "rastreios_tiny.csv")

        # Garante diretório pai existente
        os.makedirs(os.path.dirname(os.path.abspath(caminho_saida)), exist_ok=True)

        pedidos_validos = self.filtrar_pedidos_para_rastreio(pedidos)

        with open(caminho_saida, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Número do Pedido no Tiny", "Situação", "Código de Rastreio"])

            for p in pedidos_validos:
                writer.writerow([p.numero, p.situacao, p.codigo_rastreamento])

        logger.info("Arquivo CSV gerado com sucesso em '%s' com %d registros.", caminho_saida, len(pedidos_validos))
        return caminho_saida, len(pedidos_validos)

    def executar_fluxo_extracao(self, caminho_saida: str | None = None) -> bool:
        """Executa o fluxo completo de busca, filtragem e exportação."""
        try:
            pedidos = self.buscar_pedidos_recentes()
            if not pedidos:
                logger.warning("Nenhum pedido retornado pelo Tiny no período.")
                print("Nenhum pedido encontrado no período.")
                return False

            csv_file, total = self.exportar_csv(pedidos, caminho_saida=caminho_saida)
            msg = f"Sucesso! Arquivo '{csv_file}' gerado com {total} rastreios encontrados."
            logger.info(msg)
            print(msg)
            return True
        except Exception as exc:
            logger.error("Erro no processamento de extração do Tiny: %s", exc)
            print(f"Ocorreu um erro no Tiny: {exc}")
            return False
