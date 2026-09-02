import requests
import json
import time

TOKEN = "7ee0ee3913d3b55a68e234889da94aa5a4af6d5d"

# Correios credentials
ID_CORREIOS = "42715476000159"
CONTRATO = "9912705835"
CODIGO_ACESSO = "NuiZ79ZpfkGyzTzNnrDjv3iT0ufEVApjpmA4tROT"
URL_TOKEN = "https://api.correios.com.br/token/v1/autentica/contrato"
URL_PRECO = "https://api.correios.com.br/preco/v1/nacional/{coProduto}"
URL_PRAZO = "https://api.correios.com.br/prazo/v1/nacional/{coProduto}"

def obter_token_correios():
    import base64
    auth_str = f"{ID_CORREIOS}:{CODIGO_ACESSO}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()
    headers = {"Authorization": f"Basic {auth_b64}", "Content-Type": "application/json"}
    response = requests.post(URL_TOKEN, headers=headers, json={"numero": CONTRATO})
    return response.json().get("token")

token_correios = obter_token_correios()

pedidos_a_testar = [39545, 39538]
for num in pedidos_a_testar:
    print(f"\n--- Detalhes do Pedido #{num} ---")
    r = requests.get("https://api.tiny.com.br/api2/pedidos.pesquisa.php", params={
        "token": TOKEN,
        "formato": "json",
        "numero": str(num)
    })
    p_data = r.json()["retorno"].get("pedidos", [])
    if not p_data:
        print("Nao encontrado!")
        continue
    pid = p_data[0]["pedido"]["id"]
    
    time.sleep(1)
    r2 = requests.get("https://api.tiny.com.br/api2/pedido.obter.php", params={
        "token": TOKEN,
        "formato": "json",
        "id": pid
    })
    pedido = r2.json()["retorno"]["pedido"]
    
    # Endereco e Frete
    cli = pedido.get("cliente", {})
    ee = pedido.get("endereco_entrega") or {}
    cep = ee.get("cep") or cli.get("cep")
    cidade = ee.get("cidade") or cli.get("cidade")
    uf = ee.get("uf") or cli.get("uf")
    forma_envio = pedido.get("forma_envio", "")
    
    print(f"Situacao: {pedido.get('situacao')}")
    print(f"Metodo envio: {forma_envio}")
    print(f"CEP: {cep} ({cidade}/{uf})")
    
    if "MOTOBOY" in forma_envio.upper() or "RETIRADA" in forma_envio.upper():
        print("Ignorado (Motoboy/Retirada)")
        continue
        
    if cep:
        cep_limpo = "".join(filter(str.isdigit, str(cep)))
        headers = {"Authorization": f"Bearer {token_correios}"}
        # Consultar SEDEX
        res_params = {
            "cepOrigem": "05617010",
            "cepDestino": cep_limpo
        }
        res = requests.get(URL_PRAZO.format(coProduto="03220"), headers=headers, params=res_params)
        if res.status_code == 200:
            prazo = int(float(res.json().get("prazoEntrega", 0)))
            print(f"SEDEX Prazo: {prazo} dias")
        else:
            print(f"Erro Correios: {res.status_code} - {res.text}")
