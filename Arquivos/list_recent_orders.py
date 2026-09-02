import requests
import json
from datetime import datetime, timedelta

TOKEN = "7ee0ee3913d3b55a68e234889da94aa5a4af6d5d"
URL_PESQUISA = "https://api.tiny.com.br/api2/pedidos.pesquisa.php"

data_final = datetime.now().strftime("%d/%m/%Y")
data_inicial = (datetime.now() - timedelta(days=5)).strftime("%d/%m/%Y")

print(f"Buscando todos os pedidos de {data_inicial} ate {data_final}...")

params = {
    "token": TOKEN,
    "formato": "json",
    "dataInicial": data_inicial,
    "dataFinal": data_final,
    "sort": "DESC"
}

r = requests.get(URL_PESQUISA, params=params)
data = r.json()
pedidos = data["retorno"].get("pedidos", [])

print(f"Total encontrados: {len(pedidos)}")
for item in pedidos:
    p = item.get("pedido", {})
    print(f"Pedido #{p.get('numero')} - ID: {p.get('id')} - Situacao: {p.get('situacao')} - Rastreio: {p.get('codigo_rastreamento')}")
