"""
Script de diagnóstico: Consulta o pedido 39837 no Tiny,
obtém o CEP de destino e consulta as APIs de PREÇO e PRAZO dos Correios.
Exibe a resposta COMPLETA (JSON) para verificar se há mensagens como:
  - "Este CEP é de uma cidade"
  - "Provisoriamente está com 5 dias adicionais"
"""

import requests
import json
import time
import base64
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# ======== Credenciais ========
TOKEN_TINY = os.getenv("TOKEN_TINY")

ID_CORREIOS = os.getenv("ID_CORREIOS")
CONTRATO = os.getenv("CONTRATO")
CODIGO_ACESSO = os.getenv("CODIGO_ACESSO")

URL_TOKEN = "https://api.correios.com.br/token/v1/autentica/contrato"
URL_PRECO = "https://api.correios.com.br/preco/v1/nacional/{coProduto}"
URL_PRAZO = "https://api.correios.com.br/prazo/v1/nacional/{coProduto}"

CEP_ORIGEM = "05617010"

SERVICOS = {
    "03220": "SEDEX",
    "03158": "SEDEX 10",
    "03140": "SEDEX 12",
}

NUMERO_PEDIDO = "39837"


def obter_token_correios():
    auth_str = f"{ID_CORREIOS}:{CODIGO_ACESSO}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()
    headers = {"Authorization": f"Basic {auth_b64}", "Content-Type": "application/json"}
    response = requests.post(URL_TOKEN, headers=headers, json={"numero": CONTRATO})
    if response.status_code == 201:
        return response.json().get("token")
    else:
        raise Exception(f"Erro ao obter token: {response.status_code} - {response.text}")


def buscar_pedido_tiny(numero):
    """Busca o pedido no Tiny e retorna o CEP de destino"""
    print(f"\n{'='*60}")
    print(f"  BUSCANDO PEDIDO #{numero} NO TINY")
    print(f"{'='*60}")

    # 1. Pesquisa
    r = requests.get("https://api.tiny.com.br/api2/pedidos.pesquisa.php", params={
        "token": TOKEN_TINY, "formato": "json", "numero": numero
    })
    data = r.json()
    pedidos = data["retorno"].get("pedidos", [])

    if not pedidos:
        print("Pedido NÃO encontrado na pesquisa!")
        return None

    p = pedidos[0].get("pedido", {})
    pid = p.get("id")
    print(f"  ID interno: {pid}")
    print(f"  Situação: {p.get('situacao')}")
    print(f"  Rastreio: {p.get('codigo_rastreamento', 'SEM RASTREIO')}")

    time.sleep(1)

    # 2. Detalhe completo
    r2 = requests.get("https://api.tiny.com.br/api2/pedido.obter.php", params={
        "token": TOKEN_TINY, "formato": "json", "id": pid
    })
    pedido = r2.json()["retorno"]["pedido"]

    # Extrair CEP
    ee = pedido.get("endereco_entrega") or {}
    cli = pedido.get("cliente", {})
    cep = (ee.get("cep") or cli.get("cep", "")).replace("-", "").replace(".", "").replace(" ", "").strip()
    cidade = ee.get("cidade") or cli.get("cidade", "")
    uf = ee.get("uf") or cli.get("uf", "")
    forma_envio = pedido.get("forma_envio", "")
    forma_frete = pedido.get("forma_frete", "")

    print(f"\n  Destino: {cidade}/{uf}")
    print(f"  CEP destino: {cep}")
    print(f"  Forma envio: {forma_envio}")
    print(f"  Forma frete: {forma_frete}")

    return cep


def consultar_correios_completo(token, cep_destino):
    """Consulta preço E prazo nos Correios e mostra a resposta COMPLETA"""

    print(f"\n{'='*60}")
    print(f"  CONSULTANDO API DOS CORREIOS")
    print(f"  CEP Origem: {CEP_ORIGEM}  ->  CEP Destino: {cep_destino}")
    print(f"{'='*60}")

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    params_preco = {
        "cepOrigem": CEP_ORIGEM,
        "cepDestino": cep_destino,
        "psObjeto": 1000,
        "tpObjeto": 2,
        "comprimento": 30,
        "largura": 20,
        "altura": 10,
    }

    params_prazo = {
        "cepOrigem": CEP_ORIGEM,
        "cepDestino": cep_destino,
    }

    for cod, nome in SERVICOS.items():
        print(f"\n{'─'*50}")
        print(f"  SERVIÇO: {nome} ({cod})")
        print(f"{'─'*50}")

        # === CONSULTA DE PREÇO ===
        print(f"\n  📦 CONSULTA DE PREÇO:")
        url_preco = URL_PRECO.format(coProduto=cod)
        try:
            resp_preco = requests.get(url_preco, headers=headers, params=params_preco, timeout=15)
            print(f"  Status HTTP: {resp_preco.status_code}")
            print(f"  URL: {resp_preco.url}")
            print(f"\n  RESPOSTA COMPLETA (JSON):")
            try:
                data_preco = resp_preco.json()
                print(json.dumps(data_preco, indent=4, ensure_ascii=False))
            except:
                print(f"  (Não é JSON) Texto: {resp_preco.text[:500]}")
        except Exception as e:
            print(f"  ERRO: {e}")

        time.sleep(0.3)

        # === CONSULTA DE PRAZO ===
        print(f"\n  📅 CONSULTA DE PRAZO:")
        url_prazo = URL_PRAZO.format(coProduto=cod)
        try:
            resp_prazo = requests.get(url_prazo, headers=headers, params=params_prazo, timeout=15)
            print(f"  Status HTTP: {resp_prazo.status_code}")
            print(f"  URL: {resp_prazo.url}")
            print(f"\n  RESPOSTA COMPLETA (JSON):")
            try:
                data_prazo = resp_prazo.json()
                print(json.dumps(data_prazo, indent=4, ensure_ascii=False))

                # === VERIFICAÇÃO DE MENSAGENS ESPECIAIS ===
                textos_para_buscar = [
                    "cep", "cidade", "adicional", "provisori",
                    "prazo", "dias", "msg", "observ", "mensagem", "aviso"
                ]
                print(f"\n  🔍 BUSCANDO MENSAGENS ESPECIAIS NA RESPOSTA:")
                json_str = json.dumps(data_prazo, ensure_ascii=False).lower()
                encontrou = False
                for campo, valor in data_prazo.items():
                    valor_str = str(valor).lower()
                    for termo in textos_para_buscar:
                        if termo in campo.lower() or termo in valor_str:
                            print(f"    ✅ Campo '{campo}' = '{valor}'")
                            encontrou = True
                            break
                if not encontrou:
                    print("    (nenhuma mensagem especial encontrada)")

            except:
                print(f"  (Não é JSON) Texto: {resp_prazo.text[:500]}")
        except Exception as e:
            print(f"  ERRO: {e}")

        time.sleep(0.3)


if __name__ == "__main__":
    print("=" * 60)
    print("  DIAGNÓSTICO COMPLETO - PEDIDO #39837")
    print("  Verificando mensagens dos Correios")
    print("=" * 60)

    # 1. Token Correios
    token = obter_token_correios()
    print(f"Token obtido com sucesso.")

    # 2. Buscar CEP do pedido no Tiny
    cep_destino = buscar_pedido_tiny(NUMERO_PEDIDO)

    if not cep_destino or len(cep_destino) < 8:
        print("\n❌ CEP de destino não encontrado ou inválido. Abortando.")
    else:
        # 3. Consultar Correios com resposta completa
        consultar_correios_completo(token, cep_destino)

    print(f"\n{'='*60}")
    print("  DIAGNÓSTICO FINALIZADO")
    print(f"{'='*60}")
