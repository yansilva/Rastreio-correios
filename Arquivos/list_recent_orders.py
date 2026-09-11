import json
import os
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

TOKEN = os.getenv("TOKEN_TINY")
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
