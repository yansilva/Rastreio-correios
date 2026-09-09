import requests  # type: ignore
import base64
import time
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# ============== CONFIGURAÇÃO ==============

# Tiny ERP
TOKEN_TINY = os.getenv("TOKEN_TINY")
URL_PESQUISA_TINY = "https://api.tiny.com.br/api2/pedidos.pesquisa.php"
URL_OBTER_TINY = "https://api.tiny.com.br/api2/pedido.obter.php"

# Correios
ID_CORREIOS = os.getenv("ID_CORREIOS")
CONTRATO = os.getenv("CONTRATO")
CODIGO_ACESSO = os.getenv("CODIGO_ACESSO")
URL_TOKEN = "https://api.correios.com.br/token/v1/autentica/contrato"
URL_PRECO = "https://api.correios.com.br/preco/v1/nacional/{coProduto}"
URL_PRAZO = "https://api.correios.com.br/prazo/v1/nacional/{coProduto}"

# Configuração de envio
CEP_ORIGEM = "05617010"
PESO_GRAMAS = 1000
COMPRIMENTO = 30
LARGURA = 20
ALTURA = 10
TIPO_OBJETO = 2  # 2 = Pacote

# Serviços Correios (código: nome)
SERVICOS = {
    "03220": "SEDEX",
    "03158": "SEDEX 10",
    "03140": "SEDEX 12",
}

# Saída
RELATORIO_HTML = "opcoes_frete.html"
DIAS_ATRAS = 30

# ============== FUNÇÕES ==============

def obter_token_correios():
    """Autentica na API dos Correios e retorna o token"""
    print("Obtendo token dos Correios...")
    auth_str = f"{ID_CORREIOS}:{CODIGO_ACESSO}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }
    payload = {"numero": CONTRATO}
    response = requests.post(URL_TOKEN, headers=headers, json=payload)
    if response.status_code == 201:
        return response.json().get("token")
    else:
        raise Exception(f"Erro ao obter token: {response.status_code} - {response.text}")


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


def consultar_preco_servico(token, cep_destino, co_produto):
    """Consulta preço de um serviço Correios para um CEP destino"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    params = {
        "cepOrigem": CEP_ORIGEM,
        "cepDestino": cep_destino,
        "psObjeto": PESO_GRAMAS,
        "tpObjeto": TIPO_OBJETO,
        "comprimento": COMPRIMENTO,
        "largura": LARGURA,
        "altura": ALTURA,
    }

    url_preco = URL_PRECO.format(coProduto=co_produto)
    url_prazo = URL_PRAZO.format(coProduto=co_produto)

    try:
        response = requests.get(url_preco, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            # O campo de preço pode variar conforme a versão da API
            preco_str = str(data.get('pcFinal', data.get('pcBase', data.get('vlBaseCalculoImposto', '0'))))
            preco_str = preco_str.replace('.', '').replace(',', '.')
            try:
                preco = float(preco_str)
            except:
                preco = 0.0
                
            prazo = None
            msg_prazo = None
            try:
                # Tenta buscar o prazo em uma segunda requisição
                params_prazo = {
                    "cepOrigem": CEP_ORIGEM,
                    "cepDestino": cep_destino
                }
                resp_prazo = requests.get(url_prazo, headers=headers, params=params_prazo, timeout=10)
                if resp_prazo.status_code == 200:
                    data_prazo = resp_prazo.json()
                    prazo = data_prazo.get('prazoEntrega')
                    msg_prazo = data_prazo.get('msgPrazo') or data_prazo.get('txObservacao') or data_prazo.get('msgObservacao') or data_prazo.get('observacao') or data_prazo.get('txMsgObs')
                    # Tenta converter para int para remover .0 se houver
                    if prazo is not None:
                        prazo = int(float(prazo))
            except Exception as e:
                print(f"  Aviso: Não foi possível obter o prazo para {co_produto} - {e}")
                
            return {
                "disponivel": True,
                "preco": preco,
                "preco_fmt": f"R$ {preco:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                "prazo": prazo,
                "msg_prazo": msg_prazo,
                "erro": None
            }
        elif response.status_code == 422 or response.status_code == 400:
            # Serviço indisponível para essa rota
            return {
                "disponivel": False,
                "preco": None,
                "preco_fmt": None,
                "prazo": None,
                "msg_prazo": None,
                "erro": "Indisponível para esta rota"
            }
        else:
            return {
                "disponivel": False,
                "preco": None,
                "preco_fmt": None,
                "prazo": None,
                "msg_prazo": None,
                "erro": f"HTTP {response.status_code}"
            }
    except Exception as e:
        return {
            "disponivel": False,
            "preco": None,
            "preco_fmt": None,
            "prazo": None,
            "msg_prazo": None,
            "erro": str(e)
        }


def gerar_html(pedidos_com_frete, alertas_extras=None):
    """Gera a página HTML premium com opções de frete"""

    data_geracao = time.strftime('%d/%m/%Y %H:%M:%S')
    total_pedidos = len(pedidos_com_frete)

    # Conta pedidos com pelo menos 1 serviço disponível
    com_opcoes = sum(1 for p in pedidos_com_frete if any(s["disponivel"] for s in p.get("servicos", {}).values()))

    tem_prazo_longo = False
    pedidos_com_prazo_longo = []

    # Inclui alertas de pedidos Motoboy/Retirada com prazo longo (não exibidos nos cards)
    if alertas_extras:
        pedidos_com_prazo_longo.extend(alertas_extras)
        if alertas_extras:
            tem_prazo_longo = True

    # Monta os cards de pedido
    cards_html = ""
    for pedido in pedidos_com_frete:
        try:
            valor_float = float(pedido.get('valor', 0))
            valor_fmt = f"R$ {valor_float:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            valor_fmt = "R$ 0,00"

        servicos_html = ""
        for cod in SERVICOS.keys():
            nome = SERVICOS[cod]
            info = pedido.get("servicos", {}).get(cod, {"disponivel": False})

            if info["disponivel"]:
                preco_display = info.get("preco_fmt", "—")
                prazo_display = f'{info["prazo"]} dias úteis' if info.get("prazo") else "—"
                if info.get("prazo") and info["prazo"] > 3:
                    tem_prazo_longo = True
                    if str(pedido['numero']) not in pedidos_com_prazo_longo:
                        pedidos_com_prazo_longo.append(str(pedido['numero']))

                msg_prazo_html = ""
                if info.get("msg_prazo"):
                    msg_prazo_html = f'\n                    <div class="servico-msg-prazo" title="{info["msg_prazo"]}">⚠️ {info["msg_prazo"]}</div>'

                servicos_html += f"""
                <div class="servico-card disponivel">
                    <div class="servico-nome">{nome}</div>
                    <div class="servico-preco">{preco_display}</div>
                    <div class="servico-prazo">📅 {prazo_display}</div>{msg_prazo_html}
                </div>"""
            else:
                erro = info.get("erro", "Indisponível")
                servicos_html += f"""
                <div class="servico-card indisponivel">
                    <div class="servico-nome">{nome}</div>
                    <div class="servico-status">Indisponível</div>
                </div>"""

        cards_html += f"""
        <div class="pedido-card" data-valor="{valor_float}">
            <div class="pedido-header">
                <div class="pedido-left">
                    <span class="pedido-numero">Pedido #{pedido['numero']} <span style="font-size: 0.9rem; font-weight: normal; color: #16a34a; margin-left: 8px;">{valor_fmt}</span></span>
                    <span class="pedido-cliente">{pedido.get('nome_cliente', '—')}</span>
                </div>
                <div class="pedido-right">
                    <span class="pedido-badge">{pedido['situacao']}</span>
                    <span class="pedido-destino">📍 {pedido.get('destino_label', '—')} — CEP {pedido.get('cep_destino', '—')}</span>
                </div>
            </div>
            <div class="servicos-grid">
                {servicos_html}
            </div>
        </div>"""

    # Estado vazio
    if not pedidos_com_frete:
        cards_html = """
        <div class="empty-state">
            <div class="emoji">📭</div>
            <h2>Nenhum pedido em aberto</h2>
            <p>Todos os pedidos do período já foram enviados ou não possuem CEP de destino.</p>
        </div>"""

    html_page = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Opções de Frete — Correios</title>
    <style>
        :root {{
            --primary: #2563eb;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #1e293b;
            --text-sub: #64748b;
            --border: #e2e8f0;
            --green: #16a34a;
            --red: #dc2626;
        }}
        [data-theme="dark"] {{
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text-main: #f1f5f9;
            --text-sub: #94a3b8;
            --border: #334155;
        }}
        body {{
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text-main);
            margin: 0;
            padding: 20px;
            line-height: 1.5;
            transition: background-color 0.3s ease, color 0.3s ease;
        }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        header {{ text-align: center; margin-bottom: 30px; }}
        h1 {{
            margin: 0;
            font-size: 2.2rem;
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .meta {{ color: var(--text-sub); margin-top: 8px; }}
        .config-info {{
            display: inline-block;
            margin-top: 10px;
            padding: 6px 16px;
            background: var(--border);
            border-radius: 8px;
            font-size: 0.82rem;
            color: var(--text-sub);
        }}

        .back-link {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 22px;
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: white;
            text-decoration: none;
            border-radius: 99px;
            font-weight: 600;
            font-size: 0.9rem;
            margin-top: 14px;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
            transition: all 0.2s ease;
        }}
        .back-link:hover {{ transform: translateY(-2px); box-shadow: 0 8px 20px rgba(37, 99, 235, 0.45); }}

        .btn-theme {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: var(--card-bg);
            color: var(--text-main);
            border: 2px solid var(--border);
            padding: 8px 16px;
            border-radius: 99px;
            font-weight: 600;
            cursor: pointer;
            z-index: 1000;
            transition: all 0.2s ease;
        }}
        .btn-theme:hover {{ transform: translateY(-2px); }}

        /* Filter Bar */
        .filter-bar {{
            display: flex;
            align-items: center;
            gap: 16px;
            background: var(--card-bg);
            padding: 16px 24px;
            border-radius: 14px;
            border: 1px solid var(--border);
            margin-bottom: 24px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.06);
            flex-wrap: wrap;
        }}
        .filter-group {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .filter-group label {{
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-sub);
        }}
        .filter-group input {{
            padding: 8px 12px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--bg);
            color: var(--text-main);
            font-size: 0.95rem;
            width: 120px;
            outline: none;
            transition: border-color 0.2s;
        }}
        .filter-group input:focus {{
            border-color: var(--primary);
        }}
        .filter-count {{
            margin-left: auto;
            font-size: 0.9rem;
            color: var(--text-sub);
            font-weight: 600;
        }}

        /* Summary Cards */
        .summary {{
            display: flex;
            gap: 16px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }}
        .summary-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px 28px;
            flex: 1;
            min-width: 180px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.06);
            text-align: center;
        }}
        .summary-number {{ font-size: 2.5rem; font-weight: 800; line-height: 1.2; }}
        .summary-label {{ font-size: 0.82rem; color: var(--text-sub); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }}
        .num-blue {{ color: #2563eb; }}
        .num-green {{ color: #16a34a; }}

        /* Pedido Cards */
        .pedido-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 14px;
            margin-bottom: 20px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.06);
            animation: fadeIn 0.4s ease forwards;
        }}
        .pedido-header {{
            padding: 18px 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .pedido-left {{ display: flex; flex-direction: column; gap: 4px; }}
        .pedido-numero {{ font-weight: 800; font-size: 1.15rem; }}
        .pedido-cliente {{ color: var(--text-sub); font-size: 0.9rem; }}
        .pedido-right {{ display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }}
        .pedido-badge {{
            background: linear-gradient(135deg, #eff6ff, #bfdbfe);
            color: #2563eb;
            padding: 3px 12px;
            border-radius: 99px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
        }}
        [data-theme="dark"] .pedido-badge {{
            background: linear-gradient(135deg, #1e3a5f, #1e40af);
            color: #93c5fd;
        }}
        .pedido-destino {{
            color: var(--text-sub);
            font-size: 0.85rem;
        }}

        /* Serviços Grid */
        .servicos-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            padding: 18px 24px;
        }}
        .servico-card {{
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            transition: all 0.2s ease;
        }}
        .servico-card.disponivel {{
            background: linear-gradient(135deg, #f0fdf4, #dcfce7);
            border-color: #bbf7d0;
        }}
        [data-theme="dark"] .servico-card.disponivel {{
            background: linear-gradient(135deg, #052e16, #14532d);
            border-color: #166534;
        }}
        .servico-card.disponivel:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(22, 163, 74, 0.2);
        }}
        .servico-card.indisponivel {{
            background: var(--bg);
            opacity: 0.6;
        }}
        .servico-nome {{
            font-weight: 800;
            font-size: 1rem;
            margin-bottom: 8px;
            color: var(--text-main);
        }}
        .servico-preco {{
            font-size: 1.4rem;
            font-weight: 800;
            color: var(--green);
            margin-bottom: 4px;
        }}
        [data-theme="dark"] .servico-preco {{
            color: #4ade80;
        }}
        .servico-prazo {{
            font-size: 0.82rem;
            color: var(--text-sub);
            font-weight: 500;
        }}
        .servico-status {{
            color: var(--text-sub);
            font-size: 0.85rem;
            font-style: italic;
        }}
        .servico-msg-prazo {{
            font-size: 0.72rem;
            color: #d97706;
            margin-top: 8px;
            padding: 6px 10px;
            background: rgba(217, 119, 6, 0.08);
            border: 1px solid rgba(217, 119, 6, 0.15);
            border-radius: 6px;
            text-align: left;
            word-break: break-word;
            line-height: 1.3;
        }}
        [data-theme="dark"] .servico-msg-prazo {{
            color: #f59e0b;
            background: rgba(245, 158, 11, 0.08);
            border-color: rgba(245, 158, 11, 0.15);
        }}

        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: var(--text-sub);
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 14px;
        }}
        .empty-state .emoji {{ font-size: 3rem; margin-bottom: 10px; }}

        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .summary-card {{ animation: fadeIn 0.4s ease forwards; }}
        .summary-card:nth-child(2) {{ animation-delay: 0.1s; }}

        @media (max-width: 600px) {{
            .pedido-header {{ flex-direction: column; align-items: flex-start; }}
            .pedido-right {{ align-items: flex-start; }}
            .servicos-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <button class="btn-theme" onclick="toggleTheme()">🌓 Tema</button>
    <div class="container">
        <header>
            <h1>📦 Opções de Frete Correios</h1>
            <div class="meta">Consulta de serviços disponíveis para pedidos em aberto — Gerado em: {data_geracao}</div>
            <div class="config-info">📐 Pacote padrão: {PESO_GRAMAS/1000:.1f}kg — {COMPRIMENTO}x{LARGURA}x{ALTURA} cm — Origem CEP: {CEP_ORIGEM}</div>
            <br>
            <a href="relatorio_rastreio.html" class="back-link">← Voltar ao Painel Principal</a>
        </header>

        <div class="summary">
            <div class="summary-card">
                <div class="summary-number num-blue">{total_pedidos}</div>
                <div class="summary-label">Pedidos em Aberto</div>
            </div>
            <div class="summary-card">
                <div class="summary-number num-green">{com_opcoes}</div>
                <div class="summary-label">Com Opções Disponíveis</div>
            </div>
        </div>

        <div class="filter-bar">
            <div class="filter-group">
                <label for="valMin">Valor Mínimo (R$):</label>
                <input type="number" id="valMin" placeholder="0" oninput="filtrarPorValor()">
            </div>
            <div class="filter-group">
                <label for="valMax">Valor Máximo (R$):</label>
                <input type="number" id="valMax" placeholder="Sem limite" oninput="filtrarPorValor()">
            </div>
            <span class="filter-count" id="filterCount"></span>
        </div>

        {cards_html}
    </div>

    <script>
        // Lógica de Tema
        function setTheme(theme) {{
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
        }}
        function toggleTheme() {{
            const current = localStorage.getItem('theme') || 'light';
            setTheme(current === 'light' ? 'dark' : 'light');
        }}
        setTheme(localStorage.getItem('theme') || 'light');

        // Lógica de Filtro
        function filtrarPorValor() {{
            const minVal = parseFloat(document.getElementById('valMin').value) || 0;
            const maxInput = document.getElementById('valMax').value;
            const maxVal = maxInput ? parseFloat(maxInput) : Infinity;
            
            const cards = document.querySelectorAll('.pedido-card');
            let visiveis = 0;
            
            cards.forEach(card => {{
                const val = parseFloat(card.getAttribute('data-valor')) || 0;
                if (val >= minVal && val <= maxVal) {{
                    card.style.display = '';
                    visiveis++;
                }} else {{
                    card.style.display = 'none';
                }}
            }});
            
            const countSpan = document.getElementById('filterCount');
            if (minVal > 0 || maxInput) {{
                countSpan.textContent = `Mostrando ${{visiveis}} de ${{cards.length}}`;
            }} else {{
                countSpan.textContent = '';
            }}
        }}
    </script>
    <script src="alert_frete.js?v={int(time.time())}"></script>
</body>
</html>"""

    # Salva o HTML
    pasta_projeto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    caminho_html = os.path.join(pasta_projeto, RELATORIO_HTML)

    with open(caminho_html, mode='w', encoding='utf-8') as f:
        f.write(html_page)

    # Gera o alert_frete.js
    js_content = f"""(function() {{
    const pedidosComPrazo = {str(pedidos_com_prazo_longo)};
    if (pedidosComPrazo.length > 0) {{
        const cacheKey = "alerta_prazo_v2_" + pedidosComPrazo.join("_");
        if (!localStorage.getItem(cacheKey)) {{
            
            // 1. Mostrar o Modal Visual no Centro da Tela
            const overlay = document.createElement('div');
            overlay.style.position = 'fixed';
            overlay.style.top = '0';
            overlay.style.left = '0';
            overlay.style.width = '100vw';
            overlay.style.height = '100vh';
            overlay.style.backgroundColor = 'rgba(0,0,0,0.5)';
            overlay.style.display = 'flex';
            overlay.style.alignItems = 'center';
            overlay.style.justifyContent = 'center';
            overlay.style.zIndex = '99999';
            overlay.style.backdropFilter = 'blur(4px)';

            const modal = document.createElement('div');
            modal.style.backgroundColor = 'var(--card-bg, #ffffff)';
            modal.style.padding = '30px';
            modal.style.borderRadius = '16px';
            modal.style.boxShadow = '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)';
            modal.style.maxWidth = '400px';
            modal.style.textAlign = 'center';
            modal.style.color = 'var(--text-main, #1e293b)';
            modal.style.fontFamily = 'system-ui, -apple-system, sans-serif';

            const icon = document.createElement('div');
            icon.innerHTML = '&#9888;&#65039;'; // Unicode HTML Entity for Warning sign to avoid encoding bugs
            icon.style.fontSize = '3rem';
            icon.style.marginBottom = '15px';

            const title = document.createElement('h2');
            title.innerText = 'Atencao aos Prazos';
            title.style.margin = '0 0 10px 0';
            title.style.fontSize = '1.4rem';

            const text = document.createElement('p');
            text.innerText = "Os pedidos " + pedidosComPrazo.join(", ") + " possuem prazos de entrega superiores a 3 dias uteis.";
            text.style.margin = '0 0 20px 0';
            text.style.lineHeight = '1.5';
            text.style.color = 'var(--text-sub, #64748b)';

            const btnWrap = document.createElement('div');
            btnWrap.style.display = 'flex';
            btnWrap.style.gap = '10px';
            btnWrap.style.justifyContent = 'center';

            const btnFechar = document.createElement('button');
            btnFechar.innerText = 'Fechar';
            btnFechar.style.padding = '10px 20px';
            btnFechar.style.border = '1px solid var(--border, #e2e8f0)';
            btnFechar.style.borderRadius = '8px';
            btnFechar.style.backgroundColor = 'transparent';
            btnFechar.style.color = 'var(--text-main, #1e293b)';
            btnFechar.style.cursor = 'pointer';
            btnFechar.onclick = function() {{
                document.body.removeChild(overlay);
            }};

            const btnIr = document.createElement('button');
            btnIr.innerText = 'Ver Opcoes de Frete';
            btnIr.style.padding = '10px 20px';
            btnIr.style.border = 'none';
            btnIr.style.borderRadius = '8px';
            btnIr.style.backgroundColor = '#ea580c';
            btnIr.style.color = 'white';
            btnIr.style.fontWeight = 'bold';
            btnIr.style.cursor = 'pointer';
            btnIr.onclick = function() {{
                window.location.href = 'opcoes_frete.html';
            }};

            btnWrap.appendChild(btnFechar);
            btnWrap.appendChild(btnIr);

            modal.appendChild(icon);
            modal.appendChild(title);
            modal.appendChild(text);
            modal.appendChild(btnWrap);
            overlay.appendChild(modal);

            document.body.appendChild(overlay);

            // 2. Mostrar a Notificacao do Windows / Navegador
            if ("Notification" in window) {{
                function showNotif() {{
                    let n = new Notification("Alerta de Frete: Prazo Longo (>3 dias)", {{
                        body: "Os pedidos " + pedidosComPrazo.join(", ") + " possuem prazos superiores a 3 dias uteis.",
                        icon: "https://cdn-icons-png.flaticon.com/512/1055/1055065.png"
                    }});
                    n.onclick = function() {{
                        window.location.href = "opcoes_frete.html";
                    }};
                }}
                
                if (Notification.permission === "granted") {{
                    showNotif();
                }} else if (Notification.permission !== "denied") {{
                    Notification.requestPermission().then(function(p) {{
                        if (p === "granted") showNotif();
                    }});
                }}
            }}

            // Registrar que ja avisamos sobre esse grupo de pedidos
            localStorage.setItem(cacheKey, "true");
        }}
    }}
}})();"""

    caminho_js = os.path.join(pasta_projeto, "alert_frete.js")
    with open(caminho_js, mode='w', encoding='utf-8') as f:
        f.write(js_content)

    print(f"\nSucesso! Página de opções de frete salva em '{caminho_html}'.")


def processar():
    try:
        # 1. Token Correios
        token = obter_token_correios()

        # 2. Buscar pedidos em aberto no Tiny
        pedidos = buscar_pedidos_abertos()

        if not pedidos:
            print("Nenhum pedido em aberto encontrado.")
            gerar_html([])
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
                print(f"  [!] CEP de destino nao encontrado. Pulando...")
                continue

            print(f"  Destino: {destino_label} - CEP {cep_destino}")

            # Consultar preço para cada serviço
            servicos = {}
            for cod, nome in SERVICOS.items():
                resultado = consultar_preco_servico(token, cep_destino, cod)
                servicos[cod] = resultado

                if resultado["disponivel"]:
                    prazo_txt = f" ({resultado['prazo']} dias)" if resultado.get('prazo') else ""
                    print(f"  [OK] {nome}: {resultado['preco_fmt']}{prazo_txt}")
                else:
                    print(f"  [X] {nome}: Indisponivel")

                time.sleep(0.3)

            pedido["cep_destino"] = cep_destino
            pedido["destino_label"] = destino_label
            pedido["servicos"] = servicos
            pedidos_com_frete.append(pedido)

        # 4. Gerar HTML (passa alertas de Motoboy/Retirada separadamente)
        gerar_html(pedidos_com_frete, alertas_extras=alertas_motoboy)

    except Exception as e:
        import traceback
        print(f"Erro no processamento: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    processar()
