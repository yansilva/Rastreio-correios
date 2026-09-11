"""
Fachada de retrocompatibilidade para o módulo de integração com Tiny ERP.

Este script mantém a interface histórica (buscar_pedidos, gerar_csv, processar)
para total compatibilidade com `executar_rastreio.py` e execuções diretas via terminal,
delegando as regras para a camada modular `tiny/`.
"""
import os
import sys
from datetime import datetime, timedelta
from typing import Any

# Garante que o diretório Arquivos/ esteja no PYTHONPATH caso executado isoladamente
_dir_atual = os.path.dirname(os.path.abspath(__file__))
if _dir_atual not in sys.path:
    sys.path.insert(0, _dir_atual)

from tiny import PedidoTiny, TinyAuthError, TinyClient, TinyConfig, TinyOrderService

# Variáveis globais para compatibilidade retroativa com código legado
_config = TinyConfig()
TOKEN = _config.token
URL_PESQUISA = _config.url_pesquisa
FORMATO = _config.formato
DIAS_ATRAS = _config.dias_atras_padrao


def buscar_pedidos() -> list[dict[str, Any]]:
    """
    Busca pedidos brutos no Tiny ERP no período dos últimos DIAS_ATRAS.
    
    Retorna a lista de dicionários no formato original {'pedido': {...}}.
    """
    config = TinyConfig()
    if not config.token:
        print("Erro: Token do Tiny ERP não configurado. Verifique o arquivo .env.")
        return []

    client = TinyClient(config=config)
    data_final = datetime.now().strftime("%d/%m/%Y")
    data_inicial = (datetime.now() - timedelta(days=config.dias_atras_padrao)).strftime("%d/%m/%Y")

    print(f"Buscando pedidos de {data_inicial} até {data_final}...")
    try:
        pedidos = client.pesquisar_todos_pedidos(data_inicial, data_final)
        return pedidos
    except TinyAuthError as e:
        print(f"Erro de autenticação: {e}")
        return []
    except Exception as e:
        print(f"Erro na consulta de pedidos do Tiny: {e}")
        return []


def gerar_csv(pedidos: list[dict[str, Any]]) -> tuple[str, int]:
    """
    Gera o arquivo CSV 'rastreios_tiny.csv' aplicando os filtros de negócio.
    
    Mantém o contrato de retorno: (caminho_arquivo, total_gravados).
    """
    service = TinyOrderService()
    pedidos_convertidos = [PedidoTiny.de_dicionario(p) for p in pedidos]
    caminho_csv = os.path.join(_dir_atual, "rastreios_tiny.csv")
    return service.exportar_csv(pedidos_convertidos, caminho_saida=caminho_csv)


def processar() -> bool:
    """
    Ponto de entrada principal chamado por `executar_rastreio.py` e pela CLI.
    
    Executa busca, filtragem e geração de CSV com tratamento seguro de erros.
    """
    config = TinyConfig()
    if not config.token:
        print("Erro: Token do Tiny ERP não configurado. Defina TOKEN_TINY no arquivo .env.")
        return False

    try:
        pedidos_extraidos = buscar_pedidos()
        if pedidos_extraidos:
            csv_file, total = gerar_csv(pedidos_extraidos)
            print(f"Sucesso! Arquivo '{csv_file}' gerado com {total} rastreios encontrados.")
            return True
        else:
            print("Nenhum pedido encontrado no período.")
            return False
    except Exception as e:
        print(f"Ocorreu um erro no Tiny: {e}")
        return False


if __name__ == "__main__":
    processar()
