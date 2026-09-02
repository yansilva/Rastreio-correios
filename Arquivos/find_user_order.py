import requests
import json
import time
from datetime import datetime, timedelta

TOKEN = "7ee0ee3913d3b55a68e234889da94aa5a4af6d5d"

# Correios credentials
ID_CORREIOS = "42715476000159"
CONTRATO = "9912705835"
CODIGO_ACESSO = "NuiZ79ZpfkGyzTzNnrDjv3iT0ufEVApjpmA4tROT"
URL_TOKEN = "https://api.correios.com.br/token/v1/autentica/contrato"
URL_PRAZO = "https://api.correios.com.br/prazo/v1/nacional/{coProduto}"

def obter_token_correios():
    import base64
    auth_str = f"{ID_CORREIOS}:{CODIGO_ACESSO}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()
    headers = {"Authorization": f"Basic {auth_b64}", "Content-Type": "application/json"}
    response = requests.post(URL_TOKEN, headers=headers, json={"numero": CONTRATO})
    return response.json().get("token")

token_correios = obter_token_correios()

data_final = datetime.now().strftime("%d/%m/%Y")
data_inicial = (datetime.now() - timedelta(days=30)).strftime("%d/%m/%Y")

print(f"Pesquisando todos os pedidos ativos de {data_inicial} ate {data_final}...")

pagina = 1
num_paginas = 1
pedidos_lista = []

while pagina <= num_paginas:
    params = {
        "token": TOKEN,
        "formato": "json",
        "dataInicial": data_inicial,
        "dataFinal": data_final,
        "pagina": pagina,
        "sort": "DESC"
    }
    r = requests.get("https://api.tiny.com.br/api2/pedidos.pesquisa.php", params=params)
    data = r.json()
    
    if data['retorno']['status'] == 'Erro':
        break
        
    pedidos_lista.extend(data['retorno'].get('pedidos', []))
    num_paginas = int(data['retorno'].get('numero_paginas', 1))
    pagina += 1
    time.sleep(0.3)

print(f"Total de pedidos encontrados: {len(pedidos_lista)}")

for item in pedidos_lista:
    p = item.get("pedido", {})
    numero = p.get("numero")
    rastreio = p.get("codigo_rastreamento", "")
    situacao = p.get("situacao", "").upper()
    
    if situacao in ["CANCELADO", "ENTREGUE"]:
        continue
        
    # Vamos verificar este pedido!
    pid = p.get("id")
    time.sleep(0.2)
    r_detail = requests.get("https://api.tiny.com.br/api2/pedido.obter.php", params={
        "token": TOKEN,
        "formato": "json",
        "id": pid
    })
    
    try:
        pedido = r_detail.json()["retorno"]["pedido"]
        cli = pedido.get("cliente", {})
        ee = pedido.get("endereco_entrega") or {}
        cep = ee.get("cep") or cli.get("cep")
        forma_envio = pedido.get("forma_envio", "")
        
        # 1. Se tem codigo de rastreio
        if rastreio:
            print(f"Pedido #{numero} (Com Rastreio: {rastreio}) | Situacao: {situacao} | Envio: {forma_envio} | CEP: {cep}")
        else:
            # 2. Se nao tem codigo de rastreio, vamos calcular o prazo de frete do SEDEX
            if cep:
                cep_limpo = "".join(filter(str.isdigit, str(cep)))
                headers = {"Authorization": f"Bearer {token_correios}"}
                res_params = {
                    "cepOrigem": "05617010",
                    "cepDestino": cep_limpo
                }
                res = requests.get(URL_PRAZO.format(coProduto="03220"), headers=headers, params=res_params)
                prazo = None
                if res.status_code == 200:
                    prazo = int(float(res.json().get("prazoEntrega", 0)))
                print(f"Pedido #{numero} (Sem Rastreio) | Situacao: {situacao} | Envio: {forma_envio} | CEP: {cep} | SEDEX: {prazo} dias")
            else:
                print(f"Pedido #{numero} (Sem Rastreio e Sem CEP) | Situacao: {situacao} | Envio: {forma_envio}")
    except Exception as e:
        print(f"Erro ao obter #{numero}: {e}")
