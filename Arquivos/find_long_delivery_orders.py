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
data_inicial = (datetime.now() - timedelta(days=10)).strftime("%d/%m/%Y")

print(f"Buscando pedidos de {data_inicial} ate {data_final}...")

params = {
    "token": TOKEN,
    "formato": "json",
    "dataInicial": data_inicial,
    "dataFinal": data_final,
    "sort": "DESC"
}

r = requests.get("https://api.tiny.com.br/api2/pedidos.pesquisa.php", params=params)
data = r.json()
pedidos_res = data["retorno"].get("pedidos", [])

print(f"Encontrados {len(pedidos_res)} pedidos.")

count = 0
for item in pedidos_res:
    p_summary = item.get("pedido", {})
    numero = p_summary.get("numero")
    rastreio = p_summary.get("codigo_rastreamento")
    situacao = p_summary.get("situacao", "").upper()
    
    if rastreio or situacao in ["CANCELADO", "ENTREGUE"]:
        continue
        
    pid = p_summary["id"]
    time.sleep(0.3)
    r2 = requests.get("https://api.tiny.com.br/api2/pedido.obter.php", params={
        "token": TOKEN,
        "formato": "json",
        "id": pid
    })
    
    try:
        pedido = r2.json()["retorno"]["pedido"]
        cli = pedido.get("cliente", {})
        ee = pedido.get("endereco_entrega") or {}
        cep = ee.get("cep") or cli.get("cep")
        forma_envio = pedido.get("forma_envio", "")
        
        if "MOTOBOY" in forma_envio.upper() or "RETIRADA" in forma_envio.upper():
            continue
            
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
                
            print(f"Pedido #{numero} | Situacao: {situacao} | CEP: {cep} | Envio: {forma_envio} | SEDEX Prazo: {prazo} dias")
            count += 1
    except Exception as e:
        print(f"Erro no pedido #{numero}: {e}")

print(f"Total de pedidos sem rastreio analisados: {count}")
