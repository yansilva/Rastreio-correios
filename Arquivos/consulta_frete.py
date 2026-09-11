"""Consulta de frete dos Correios — Ponto de entrada.

Busca pedidos em aberto no Tiny ERP, consulta preço e prazo nos Correios
e gera o relatório HTML com as opções de frete.

Uso direto:
    python Arquivos/consulta_frete.py
"""
import logging
import os
import sys
import time
from datetime import datetime, timedelta

import requests  # type: ignore
from dotenv import load_dotenv

# Garante que o diretório Arquivos/ esteja no PYTHONPATH
_dir_atual = os.path.dirname(os.path.abspath(__file__))
if _dir_atual not in sys.path:
    sys.path.insert(0, _dir_atual)

# Carrega variáveis de ambiente do .env na raiz do projeto ou em Arquivos/
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# --- Módulos refatorados ---
from correios import CorreiosClient
from frete import (
    FreteClient,
    FreteConfig,
    FreteReportGenerator,
    FreteService,
)

# ============== CONFIGURAÇÃO ==============

# Tiny ERP (integração não alterada)
TOKEN_TINY = os.getenv("TOKEN_TINY", "")
URL_PESQUISA_TINY = "https://api.tiny.com.br/api2/pedidos.pesquisa.php"
URL_OBTER_TINY = "https://api.tiny.com.br/api2/pedido.obter.php"

# Configuração de frete (delega para o módulo frete/)
_frete_config = FreteConfig()
DIAS_ATRAS = _frete_config.dias_atras

logger = logging.getLogger("consulta_frete")

# ============== FUNÇÕES TINY (não alteradas) ==============


def buscar_pedidos_abertos():
    """Busca pedidos no Tiny que estão em aberto (sem código de rastreio)"""
    print("Buscando pedidos em aberto no Tiny...")

    data_final = datetime.now().strftime("%d/%m/%Y")
    data_inicial = (datetime.now() - timedelta(days=DIAS_ATRAS)).strftime("%d/%m/%Y")

    pagina = 1
    num_paginas = 1
    pedidos_abertos = []

    while pagina <= num_paginas:
        params = {
            "token": TOKEN_TINY,
            "formato": "json",
            "dataInicial": data_inicial,
            "dataFinal": data_final,
            "pagina": pagina,
            "sort": "DESC"
        }

        response = requests.get(URL_PESQUISA_TINY, params=params)
        data = response.json()

        if data['retorno']['status'] == 'Erro':
            erros = data['retorno'].get('erros', [])
            if any(erro['erro'] == 'A consulta não retornou registros' for erro in erros):
                break
            else:
                print(f"Erro na API Tiny: {data['retorno']['erros']}")
                break

        pedidos_pagina = data['retorno'].get('pedidos', [])

        for item in pedidos_pagina:
            pedido = item.get('pedido', {})
            rastreio = pedido.get('codigo_rastreamento', '')
            situacao = pedido.get('situacao', '').upper()

            # Filtra: apenas pedidos pendentes sem rastreio e com status Aberto
            if not rastreio and situacao in ["ABERTO", "EM ABERTO"]:
                pedidos_abertos.append({
                    "id": pedido.get('id'),
                    "numero": pedido.get('numero'),
                    "situacao": pedido.get('situacao'),
                    "data_pedido": pedido.get('data_pedido', ''),
                    "nome_cliente": pedido.get('nome', ''),
                    "valor": pedido.get('valor', 0)
                })

        num_paginas = int(data['retorno'].get('numero_paginas', 1))
        if pagina >= num_paginas:
            break
        pagina += 1
        time.sleep(0.5)

    print(f"Encontrados {len(pedidos_abertos)} pedidos pendentes sem rastreio.")
    return pedidos_abertos


def obter_cep_destino(pedido_id):
    """Obtém o CEP de destino e info de localização via Tiny API"""
    params = {
        "token": TOKEN_TINY,
        "formato": "json",
        "id": pedido_id
    }

    try:
        response = requests.get(URL_OBTER_TINY, params=params)
        data = response.json()

        if data['retorno']['status'] == 'OK':
            pedido = data['retorno'].get('pedido', {})
            forma_frete = (pedido.get('forma_frete') or '').upper()
            forma_envio = (pedido.get('forma_envio') or '').upper()
            frete_por = (pedido.get('frete_por') or '').upper()

            # Combina os campos para facilitar a checagem
            metodo_envio = f"{forma_frete} {forma_envio} {frete_por}"

            # Tenta endereço de entrega
            endereco = pedido.get('endereco_entrega', {})
            if endereco and endereco.get('cep'):
                cep = endereco.get('cep', '').replace('-', '').replace('.', '').replace(' ', '').strip()
                cidade = endereco.get('cidade', '')
                uf = endereco.get('uf', '')
                if len(cep) >= 8:
                    return cep[:8], f"{cidade}/{uf}", metodo_envio

            # Fallback: endereço do cliente
            cliente = pedido.get('cliente', {})
            if cliente and cliente.get('cep'):
                cep = cliente.get('cep', '').replace('-', '').replace('.', '').replace(' ', '').strip()
                cidade = cliente.get('cidade', '')
                uf = cliente.get('uf', '')
                if len(cep) >= 8:
                    return cep[:8], f"{cidade}/{uf}", metodo_envio
    except Exception as e:
        print(f"  Erro ao obter CEP: {e}")

    return None, "", ""


# ============== ORQUESTRAÇÃO ==============


def processar():
    """Ponto de entrada principal: busca pedidos, consulta frete e gera relatório."""
    try:
        # 1. Inicializa clientes (autenticação reutilizada do módulo correios/)
        logger.info("Iniciando consulta de frete")
        correios_client = CorreiosClient()
        frete_client = FreteClient(correios_client=correios_client, config=_frete_config)
        frete_service = FreteService(client=frete_client, config=_frete_config)
        report_generator = FreteReportGenerator(config=_frete_config)

        # Obtém token (reaproveitado para todas as consultas)
        print("Obtendo token dos Correios...")
        correios_client.gerar_token()

        # 2. Buscar pedidos em aberto no Tiny
        pedidos = buscar_pedidos_abertos()

        if not pedidos:
            print("Nenhum pedido em aberto encontrado.")
            report_generator.gerar_html([])
            return

        # 3. Para cada pedido, obter CEP e consultar fretes
        pedidos_com_frete = []
        alertas_motoboy = []  # Pedidos Motoboy/Retirada com prazo > 3 dias (só para alerta)

        for i, pedido in enumerate(pedidos):
            print(f"\n[{i+1}/{len(pedidos)}] Pedido #{pedido['numero']}...")

            # Obter CEP de destino e forma de envio
            cep_destino, destino_label, metodo_envio = obter_cep_destino(pedido['id'])
            time.sleep(1)  # Rate limit Tiny

            # Pedidos Ocultos: Mercado Envios, Shopee, Motoboy e Retirada
            # Não exibe card e NÃO gera alerta — o frete é gerenciado pela plataforma
            # O Tiny indica Mercado Envios usando "M" isolado na forma_envio
            metodo_envio_words = metodo_envio.split()
            if any(m in metodo_envio for m in ["MOTOBOY", "RETIRADA", "MERCADO ENVIOS", "SHOPEE"]) or "M" in metodo_envio_words:
                print(f"  [--] Oculto ({metodo_envio.strip()}). Sem alerta.")
                continue

            if not cep_destino or len(cep_destino) < 8:
                print("  [!] CEP de destino nao encontrado. Pulando...")
                continue

            print(f"  Destino: {destino_label} - CEP {cep_destino}")

            # Consultar preço e prazo para cada serviço (usa FreteService)
            opcoes = frete_service.consultar_opcoes(cep_destino)

            # Converte para formato de dicionário legado (compatibilidade com report)
            servicos = {}
            for opcao in opcoes:
                servicos[opcao.codigo] = opcao.to_dict()

                if opcao.disponivel:
                    prazo_txt = f" ({opcao.prazo_dias} dias)" if opcao.prazo_dias else ""
                    print(f"  [OK] {opcao.nome}: {opcao.preco_formatado}{prazo_txt}")
                else:
                    print(f"  [X] {opcao.nome}: Indisponivel")

            pedido["cep_destino"] = cep_destino
            pedido["destino_label"] = destino_label
            pedido["servicos"] = servicos
            pedidos_com_frete.append(pedido)

        # 4. Gerar HTML (passa alertas de Motoboy/Retirada separadamente)
        report_generator.gerar_html(pedidos_com_frete, alertas_extras=alertas_motoboy)

    except Exception as e:
        import traceback
        logger.error("Erro no processamento: %s", e)
        print(f"Erro no processamento: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    processar()
