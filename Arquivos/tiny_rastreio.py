import requests  # type: ignore
import csv
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# Configurações
TOKEN = os.getenv("TOKEN_TINY")
URL_PESQUISA = "https://api.tiny.com.br/api2/pedidos.pesquisa.php"
FORMATO = "json"
DIAS_ATRAS = 30

def buscar_pedidos():
    data_final = datetime.now().strftime("%d/%m/%Y")
    data_inicial = (datetime.now() - timedelta(days=DIAS_ATRAS)).strftime("%d/%m/%Y")
    
    print(f"Buscando pedidos de {data_inicial} até {data_final}...")
    
    pagina = 1
    num_paginas = 1
    todos_pedidos = []
    
    while pagina <= num_paginas:
        params = {
            "token": TOKEN,
            "formato": FORMATO,
            "dataInicial": data_inicial,
            "dataFinal": data_final,
            "pagina": pagina,
            "sort": "DESC"
        }
        
        response = requests.get(URL_PESQUISA, params=params)
        data = response.json()
        
        if data['retorno']['status'] == 'Erro':
            # Se não houver registros na página, o Tiny retorna erro 6 (A consulta não retornou registros)
            erros = data['retorno'].get('erros', [])
            if any(erro['erro'] == 'A consulta não retornou registros' for erro in erros):
                break
            else:
                print(f"Erro na API: {data['retorno']['erros']}")
                break
        
        pedidos_pagina = data['retorno'].get('pedidos', [])
        todos_pedidos.extend(pedidos_pagina)
        
        num_paginas = int(data['retorno'].get('numero_paginas', 1))
        
        if pagina >= num_paginas:
            break
            
        pagina += 1  # type: ignore
        # Pequeno delay para evitar bloqueio por excesso de requisições
        time.sleep(0.5)
        
    return todos_pedidos

def gerar_csv(pedidos):
    # Caminho absoluto relativo a este script
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rastreios_tiny.csv")
    count = 0
    
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Número do Pedido no Tiny", "Situação", "Código de Rastreio"])
        
        for item in pedidos:
            pedido = item.get('pedido', {})
            # Verificamos se há código de rastreamento
            rastreio = pedido.get('codigo_rastreamento')
            situacao = pedido.get('situacao', '').upper()
            
            # Filtros solicitados:
            # 1. Remover pedidos com situação ENTREGUE ou CANCELADO (case insensitive)
            # 2. Código de rastreio deve começar com A
            if rastreio and situacao not in ["ENTREGUE", "CANCELADO"] and rastreio.startswith("A"):
                writer.writerow([
                    pedido.get('numero'),
                    pedido.get('situacao'),
                    rastreio
                ])
                count += 1
                
    return filename, count

def processar():
    try:
        pedidos_extraidos = buscar_pedidos()
        if pedidos_extraidos:
            csv_file, total = gerar_csv(pedidos_extraidos)
            print(f"Sucesso! Arquivo '{csv_file}' gerado com {total} rastreios encontrados.")
            return True
        else:
            print("Nenhum pedido encontrado no período.")
    except Exception as e:
        print(f"Ocorreu um erro no Tiny: {e}")
    return False

if __name__ == "__main__":
    processar()
