import requests
import json

TOKEN = "7ee0ee3913d3b55a68e234889da94aa5a4af6d5d"

# Buscar o pedido 39546 pela pesquisa
r = requests.get("https://api.tiny.com.br/api2/pedidos.pesquisa.php", params={
    "token": TOKEN,
    "formato": "json",
    "numero": "39546"
})
data = r.json()
pedidos = data["retorno"].get("pedidos", [])

if not pedidos:
    print("Pedido nao encontrado na pesquisa!")
else:
    p = pedidos[0].get("pedido", {})
    pid = p.get("id")
    print(f"ID interno do pedido 39546: {pid}")
    
    import time
    time.sleep(1)
    
    # Obter detalhes completos
    r2 = requests.get("https://api.tiny.com.br/api2/pedido.obter.php", params={
        "token": TOKEN,
        "formato": "json",
        "id": pid
    })
    detail = r2.json()
    pedido = detail["retorno"].get("pedido", {})
    
    # Mostrar TODA a estrutura de endereco
    print("\n=== ENDERECO_ENTREGA (raw) ===")
    ee = pedido.get("endereco_entrega")
    print(f"Tipo: {type(ee)}")
    print(json.dumps(ee, indent=2, ensure_ascii=False) if ee else "VAZIO/NONE")
    
    print("\n=== CLIENTE (endereco) ===")
    cli = pedido.get("cliente", {})
    print(f"cep: {cli.get('cep')}")
    print(f"cidade: {cli.get('cidade')}")
    print(f"uf: {cli.get('uf')}")
    print(f"endereco: {cli.get('endereco')}")
    
    print("\n=== FRETE/ENVIO ===")
    print(f"forma_frete: {pedido.get('forma_frete')}")
    print(f"forma_envio: {pedido.get('forma_envio')}")
    print(f"total_pedido: {pedido.get('total_pedido')}")
    
    # Mostrar todas as chaves do pedido para referencia
    print("\n=== TODAS AS CHAVES DO PEDIDO ===")
    for k in sorted(pedido.keys()):
        v = pedido[k]
        if isinstance(v, (dict, list)):
            print(f"  {k}: ({type(v).__name__}) ...")
        else:
            print(f"  {k}: {v}")
