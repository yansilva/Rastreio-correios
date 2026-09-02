import requests  # type: ignore
import csv
import base64
import time
import os
from datetime import datetime

# Credenciais Correios
ID_CORREIOS = "42715476000159"
CONTRATO = "9912705835"
CODIGO_ACESSO = "NuiZ79ZpfkGyzTzNnrDjv3iT0ufEVApjpmA4tROT"

# Endpoints
URL_TOKEN = "https://api.correios.com.br/token/v1/autentica/contrato"
URL_RASTREIO = "https://api.correios.com.br/srorastro/v1/objetos/{objeto}?resultado=T"

# Arquivos
# Arquivos
CSV_ENTRADA = "rastreios_tiny.csv"
RELATORIO_HTML = "relatorio_rastreio.html"
RELATORIO_ATRASADOS = "pedidos_atrasados.html"

def obter_token():
    print("Obtendo novo token de acesso nos Correios...")
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

def consultar_objeto(objeto, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    url = URL_RASTREIO.format(objeto=objeto)
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if "objetos" in data and len(data["objetos"]) > 0:
            return data["objetos"][0]
    return None

def formatar_evento_html(evento):
    dt_iso = evento.get("dtHrCriado", "")
    desc = evento.get("descricao", "")
    unidade = evento.get("unidade", {})
    endereco = unidade.get("endereco", {})
    cidade = endereco.get("cidade", "")
    uf = endereco.get("uf", "")
    local = f"{cidade}/{uf}".strip("/")
    detalhe = evento.get("detalhe", "")
    
    try:
        dt_obj = datetime.fromisoformat(dt_iso)
        dt_br = dt_obj.strftime("%d/%m/%Y %H:%M")
    except:
        dt_br = dt_iso
    
    desc_upper = desc.upper()
    det_upper = detalhe.upper()
    
    status_class = ""
    badge = ""
    
    if "RETIRADA" in desc_upper or "RETIRADA" in det_upper:
        status_class = "status-critical"
        badge = '<span class="badge badge-red">AGUARDANDO RETIRADA</span>'
    elif "REMETENTE" in desc_upper:
        status_class = "status-devolvido"
        badge = '<span class="badge badge-purple">DEVOLVIDO AO REMETENTE</span>'
    elif "CANCELADA" in desc_upper or "CANCELADA" in det_upper:
        status_class = "status-warning"
        badge = '<span class="badge badge-yellow">ENTREGA CANCELADA</span>'
    elif "DEVOLVIDO" in desc_upper or "DEVOLUÇÃO" in desc_upper:
        status_class = "status-devolvido"
        badge = '<span class="badge badge-purple">DEVOLVIDO</span>'
    elif "POSTADO" in desc_upper:
        badge = '<span class="badge badge-green">POSTADO</span>'
    
    detalhe_html = f'<div class="event-detail">{detalhe}</div>' if detalhe else ''
    
    return f"""
    <div class="event {status_class}">
        <div class="event-header">
            <span class="event-date">{dt_br}</span>
            {badge}
        </div>
        <div class="event-desc">{desc} - <strong>{local}</strong></div>
        {detalhe_html}
    </div>
    """

def processar():
    try:
        token = obter_token()
        
        # Garante que procuramos o CSV na mesma pasta do script
        caminho_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)), CSV_ENTRADA)
        print(f"Lendo '{caminho_csv}'...")
        
        vendas = []
        with open(caminho_csv, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                vendas.append(row)
        
        if not vendas:
            print("Nenhum registro encontrado no CSV de entrada.")
            return

        print(f"\nConsultando {len(vendas)} objetos...")
        
        html_template = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Rastreio Correios</title>
    <style>
        :root {{
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #1e293b;
            --text-sub: #64748b;
            --border: #e2e8f0;
            --red: #ef4444;
            --yellow: #f59e0b;
            --green: #22c55e;
            --header-bg: #f1f5f9;
        }}

        /* Dark Mode Colors */
        [data-theme="dark"] {{
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text-main: #f1f5f9;
            --text-sub: #94a3b8;
            --border: #334155;
            --header-bg: #1e293b;
        }}

        body {{
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            margin: 0;
            padding: 20px;
            padding-bottom: 100px;
            line-height: 1.5;
            transition: background-color 0.3s ease, color 0.3s ease;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        header {{
            text-align: center;
            margin-bottom: 40px;
            position: relative;
        }}
        h1 {{ margin: 0; color: var(--primary); font-size: 2.5rem; }}
        .meta {{ color: var(--text-sub); margin-top: 10px; }}
        
        /* Botões Flutuantes */
        .floating-actions {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            display: flex;
            flex-direction: column;
            gap: 15px;
            z-index: 1000;
        }}

        .btn-action {{
            background: var(--primary);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 99px;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.4);
            display: flex;
            align-items: center;
            gap: 10px;
            transition: all 0.2s ease;
        }}
        
        .btn-theme {{
            background: var(--card-bg);
            color: var(--text-main);
            border: 2px solid var(--border);
            padding: 8px 16px;
            width: auto;
            min-width: 150px;
            height: 45px;
            justify-content: center;
            align-self: flex-end;
        }}

        .btn-action:hover {{
            transform: translateY(-2px);
            box-shadow: 0 20px 25px -5px rgba(37, 99, 235, 0.4);
        }}
        
        .btn-update:hover {{ background: var(--primary-dark); }}

        .btn-action:disabled {{
            background: var(--text-sub);
            cursor: not-allowed;
            transform: none;
        }}

        .spinner {{
            width: 18px;
            height: 18px;
            border: 3px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            display: none;
            animation: spin 1s linear infinite;
        }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}

        /* Toast Notifications */
        #toast {{
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #1e293b;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.2);
            display: none;
            z-index: 2000;
            font-weight: 500;
            animation: fadeIn 0.3s ease;
        }}
        @keyframes fadeIn {{ from {{ opacity: 0; top: 0; }} to {{ opacity: 1; top: 20px; }} }}
        
        .order-card {{
            background: var(--card-bg);
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
            overflow: hidden;
            border: 1px solid var(--border);
        }}
        .order-header {{
            background: var(--header-bg);
            padding: 15px 25px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .order-title {{ font-weight: bold; font-size: 1.2rem; }}
        .order-tiny-status {{ font-size: 0.9rem; color: var(--text-sub); }}
        
        .events-container {{ padding: 20px 25px; }}
        .event {{
            padding: 15px 0;
            border-left: 3px solid var(--border);
            padding-left: 20px;
            position: relative;
            margin-bottom: 10px;
        }}
        .event:last-child {{ margin-bottom: 0; }}
        .event::before {{
            content: '';
            position: absolute;
            left: -8px;
            top: 20px;
            width: 12px;
            height: 12px;
            background: var(--border);
            border-radius: 50%;
        }}
        
        .event-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 5px; }}
        .event-date {{ font-size: 0.85rem; color: var(--text-sub); font-weight: 500; }}
        .event-desc {{ font-size: 1rem; }}
        .event-detail {{ font-size: 0.9rem; color: var(--text-sub); margin-top: 5px; font-style: italic; }}
        
        .badge {{
            font-size: 0.7rem;
            padding: 2px 8px;
            border-radius: 99px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .badge-red {{ background: #fee2e2; color: var(--red); border: 1px solid #fecaca; }}
        .badge-yellow {{ background: #fef3c7; color: var(--yellow); border: 1px solid #fde68a; }}
        .badge-green {{ background: #dcfce7; color: var(--green); border: 1px solid #bbf7d0; }}
        .badge-purple {{ background: #f3e8ff; color: #9333ea; border: 1px solid #d8b4fe; }}

        /* Dashboard Summary Cards */
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
            margin-bottom: 35px;
        }}
        .dash-card {{
            background: var(--card-bg);
            border-radius: 14px;
            padding: 20px 22px;
            border: 1px solid var(--border);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
            display: flex;
            align-items: center;
            gap: 16px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .dash-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 10px 20px -5px rgba(0, 0, 0, 0.15);
        }}
        .dash-icon {{
            width: 52px;
            height: 52px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            flex-shrink: 0;
        }}
        .dash-icon-orange {{ background: linear-gradient(135deg, #fff7ed, #fed7aa); }}
        .dash-icon-blue {{ background: linear-gradient(135deg, #eff6ff, #bfdbfe); }}
        .dash-icon-green {{ background: linear-gradient(135deg, #f0fdf4, #bbf7d0); }}
        .dash-icon-red {{ background: linear-gradient(135deg, #fef2f2, #fecaca); }}
        .dash-icon-purple {{ background: linear-gradient(135deg, #faf5ff, #e9d5ff); }}
        .dash-info {{
            display: flex;
            flex-direction: column;
        }}
        .dash-number {{
            font-size: 1.8rem;
            font-weight: 800;
            line-height: 1.2;
            letter-spacing: -0.5px;
        }}
        .dash-number-orange {{ color: #ea580c; }}
        .dash-number-blue {{ color: #2563eb; }}
        .dash-number-green {{ color: #16a34a; }}
        .dash-number-red {{ color: #dc2626; }}
        .dash-number-purple {{ color: #9333ea; }}
        .dash-label {{
            font-size: 0.82rem;
            color: var(--text-sub);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        @keyframes countUp {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .dash-card {{
            animation: countUp 0.5s ease forwards;
        }}
        .dash-card:nth-child(2) {{ animation-delay: 0.1s; }}
        .dash-card:nth-child(3) {{ animation-delay: 0.2s; }}
        .dash-card:nth-child(4) {{ animation-delay: 0.3s; }}

        /* Clickable Dashboard Cards */
        .dash-card.dash-clickable {{
            cursor: pointer;
            user-select: none;
            position: relative;
        }}
        .dash-card.dash-clickable::after {{
            content: 'Clique para filtrar';
            position: absolute;
            bottom: 4px;
            right: 8px;
            font-size: 0.65rem;
            color: var(--text-sub);
            opacity: 0;
            transition: opacity 0.2s ease;
        }}
        .dash-card.dash-clickable:hover::after {{
            opacity: 1;
        }}
        .dash-card.active {{
            outline: 3px solid var(--primary);
            outline-offset: -3px;
            box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.3);
        }}
        .order-card.order-hidden {{
            display: none;
        }}
        .filter-banner {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 12px 20px;
            margin-bottom: 20px;
            display: none;
            align-items: center;
            justify-content: space-between;
            animation: countUp 0.3s ease;
        }}
        .filter-banner.visible {{
            display: flex;
        }}
        .filter-banner-text {{
            font-weight: 600;
            color: var(--text-main);
        }}
        .filter-banner-close {{
            background: none;
            border: none;
            font-size: 1.2rem;
            cursor: pointer;
            color: var(--text-sub);
            padding: 4px 8px;
            border-radius: 6px;
            transition: background 0.2s;
        }}
        .filter-banner-close:hover {{
            background: var(--border);
        }}
        
        .status-critical {{ border-left-color: var(--red); background: rgba(239, 68, 68, 0.05); border-radius: 0 8px 8px 0; }}
        .status-critical::before {{ background: var(--red); }}
        .status-warning {{ border-left-color: var(--yellow); }}
        .status-warning::before {{ background: var(--yellow); }}
        .status-devolvido {{ border-left-color: #9333ea; background: rgba(147, 51, 234, 0.08); border-radius: 0 8px 8px 0; }}
        .status-devolvido::before {{ background: #9333ea; }}

        /* Link para página de atrasados */
        .atrasados-link {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 14px;
            padding: 10px 22px;
            background: linear-gradient(135deg, #dc2626, #b91c1c);
            color: white;
            text-decoration: none;
            border-radius: 99px;
            font-weight: 700;
            font-size: 0.95rem;
            box-shadow: 0 4px 14px rgba(220, 38, 38, 0.4);
            transition: all 0.2s ease;
        }}
        .atrasados-link:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(220, 38, 38, 0.5);
        }}
        .atrasados-link .atrasados-count {{
            background: rgba(255,255,255,0.25);
            padding: 2px 10px;
            border-radius: 99px;
            font-size: 0.85rem;
        }}
        .frete-link {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 14px;
            margin-left: 10px;
            padding: 10px 22px;
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: white;
            text-decoration: none;
            border-radius: 99px;
            font-weight: 700;
            font-size: 0.95rem;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
            transition: all 0.2s ease;
        }}
        .frete-link:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(37, 99, 235, 0.5);
        }}
        
        /* Console Terminal */
        .console-container {{
            background: #0f172a;
            color: #38bdf8;
            border-radius: 12px;
            margin-top: 30px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
            overflow: hidden;
            display: none;
            border: 1px solid #1e293b;
        }}
        .console-header {{
            background: #1e293b;
            padding: 8px 15px;
            display: flex;
            align-items: center;
            gap: 10px;
            border-bottom: 1px solid #334155;
            font-family: monospace;
            font-size: 14px;
        }}
        .console-dot {{ width: 12px; height: 12px; border-radius: 50%; }}
        .dot-red {{ background: #ff5f56; }}
        .dot-yellow {{ background: #ffbd2e; }}
        .dot-green {{ background: #27c93f; }}
        .console-body {{
            padding: 20px;
            font-family: 'Fira Code', 'Courier New', monospace;
            font-size: 14px;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
        }}
        .log-line {{ margin-bottom: 4px; border-left: 2px solid transparent; padding-left: 8px; }}
        .log-info {{ border-left-color: #38bdf8; }}
        .log-success {{ border-left-color: #22c55e; color: #4ade80; }}
        .log-error {{ border-left-color: #ef4444; color: #f87171; }}

        @media (max-width: 600px) {{
            .order-header {{ flex-direction: column; align-items: flex-start; gap: 5px; }}
            .floating-actions {{ bottom: 20px; right: 20px; left: 20px; }}
            .btn-update {{ flex: 1; justify-content: center; }}
        }}
    </style>
</head>
<body>
    <div id="toast"></div>

    <div class="floating-actions">
        <button id="themeToggle" class="btn-action btn-theme" onclick="toggleTheme()">
            <span class="theme-icon">🌓</span>
            <span class="theme-text">Mudar Tema</span>
        </button>
        <button id="btnUpdate" class="btn-action btn-update" onclick="atualizarDados()">
            <div id="spinner" class="spinner"></div>
            <span>🔄 Atualizar Dados</span>
        </button>
    </div>

    <div class="container">
        <header>
            <h1>📦 Status de Entregas</h1>
            <div class="meta">
                Relatório gerado em: {data_geracao}
                <span id="next-check" style="margin-left: 10px; opacity: 0.85;">
                    | ⏰ Próxima verificação automática em: <strong id="countdown-timer">carregando...</strong>
                </span>
            </div>
            {atrasados_link}
            <a href="opcoes_frete.html" class="frete-link">📦 Opções de Frete</a>
        </header>

        {dashboard}

        <!-- Console Visual -->
        <div id="console" class="console-container">
            <div class="console-header">
                <div class="console-dot dot-red"></div>
                <div class="console-dot dot-yellow"></div>
                <div class="console-dot dot-green"></div>
                <span style="margin-left: 10px; color: #94a3b8;">Terminal de Atualização</span>
            </div>
            <div id="consoleBody" class="console-body"></div>
        </div>
        
        {content}
        
    </div>

    <script>
        console.log("Script de Rastreio carregado. Iniciando lógica de tema...");

        // Lógica do cronômetro da próxima verificação automática
        let remainingSeconds = 0;
        let nextTimeStr = "--:--";

        async function obterProximaVerificacao() {{
            try {{
                const baseUrl = window.location.protocol === 'file:' ? 'http://localhost:8000' : '';
                const response = await fetch(`${{baseUrl}}/proxima-atualizacao`);
                if (response.ok) {{
                    const data = await response.json();
                    remainingSeconds = data.remaining;
                    nextTimeStr = data.next_time;
                    atualizarElementoContador();
                }} else {{
                    const timerEl = document.getElementById('countdown-timer');
                    if (timerEl) {{
                        timerEl.textContent = "indisponível (erro do servidor)";
                    }}
                }}
            }} catch (err) {{
                console.error("Erro ao obter próxima verificação:", err);
                const timerEl = document.getElementById('countdown-timer');
                if (timerEl) {{
                    timerEl.textContent = "indisponível (servidor offline)";
                }}
            }}
        }}

        function atualizarElementoContador() {{
            const timerEl = document.getElementById('countdown-timer');
            if (!timerEl) return;

            if (remainingSeconds <= 0) {{
                timerEl.textContent = "iniciando verificação...";
            }} else {{
                const minutes = Math.floor(remainingSeconds / 60);
                const seconds = remainingSeconds % 60;
                timerEl.textContent = `${{minutes}}m ${{seconds}}s (às ${{nextTimeStr}})`;
            }}
        }}

        // Tenta buscar o valor exato a cada 10 segundos
        setInterval(obterProximaVerificacao, 10000);
        
        // E decrementa localmente a cada segundo para ficar fluido
        setInterval(() => {{
            if (remainingSeconds > 0) {{
                remainingSeconds--;
                atualizarElementoContador();
            }}
        }}, 1000);

        obterProximaVerificacao();
        
        // Solicita permissão para notificações
        if ("Notification" in window && Notification.permission !== "denied" && Notification.permission !== "granted") {{
            Notification.requestPermission();
        }}
        
        // A atualização automática foi desativada temporariamente a pedido do usuário.
        // setInterval(atualizarDados, 2700000);

        // Lógica de Tema
        function setTheme(theme) {{
            console.log("Definindo tema:", theme);
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
            
            // Atualiza o texto do botão para ser mais intuitivo
            const themeText = document.querySelector('.theme-text');
            if (themeText) {{
                themeText.textContent = theme === 'light' ? 'Modo Escuro' : 'Modo Claro';
            }}
        }}

        function toggleTheme() {{
            const current = localStorage.getItem('theme') || 'light';
            setTheme(current === 'light' ? 'dark' : 'light');
        }}

        // Inicializa o tema ao carregar a página
        setTheme(localStorage.getItem('theme') || 'light');

        function showToast(message, color = '#1e293b') {{
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.style.background = color;
            toast.style.display = 'block';
            setTimeout(() => {{ toast.style.display = 'none'; }}, 5000);
        }}

        function addLog(message) {{
            const body = document.getElementById('consoleBody');
            const line = document.createElement('div');
            line.className = 'log-line';
            
            if (message.includes('✅') || message.includes('Sucesso')) line.classList.add('log-success');
            else if (message.includes('❌') || message.includes('Erro')) line.classList.add('log-error');
            else line.classList.add('log-info');
            
            line.textContent = message;
            body.appendChild(line);
            body.scrollTop = body.scrollHeight;
        }}

        async function atualizarDados() {{
            const btn = document.getElementById('btnUpdate');
            const spinner = document.getElementById('spinner');
            const btnText = btn.querySelector('span');
            const consoleDiv = document.getElementById('console');
            const consoleBody = document.getElementById('consoleBody');
            
            // Limpa o cache de notificacoes de frete para forcar nova exibicao apos a atualizacao
            const keysToRemove = [];
            for (let i = 0; i < localStorage.length; i++) {{
                const key = localStorage.key(i);
                if (key && (key.startsWith('alerta_prazo_v2_') || key.startsWith('modal_frete_'))) {{
                    keysToRemove.push(key);
                }}
            }}
            keysToRemove.forEach(k => localStorage.removeItem(k));
            
            try {{
                btn.disabled = true;
                spinner.style.display = 'block';
                btnText.textContent = 'Iniciando...';
                
                // Limpa e mostra o console
                consoleBody.innerHTML = '';
                consoleDiv.style.display = 'block';
                addLog('>> Iniciando conexão com o servidor...');

                const baseUrl = window.location.protocol === 'file:' ? 'http://localhost:8000' : '';
                
                // Inicia o envio de comandos
                const response = await fetch(`${{baseUrl}}/atualizar`, {{ method: 'POST' }});
                
                if (response.status === 200) {{
                    // Conecta ao stream de logs
                    const eventSource = new EventSource(`${{baseUrl}}/logs`);
                    
                    eventSource.onmessage = function(event) {{
                        if (event.data === ': keep-alive') return;
                        
                        addLog(event.data);
                        
                        if (event.data.includes('✅ PROCESSO FINALIZADO')) {{
                            eventSource.close();
                            showToast('✅ Atualização concluída!', '#22c55e');
                            setTimeout(() => {{ window.location.reload(); }}, 2000);
                        }}
                    }};
                    
                    eventSource.onerror = function() {{
                        eventSource.close();
                    }};

                }} else if (response.status === 429) {{
                    const data = await response.json();
                    const minutes = Math.floor(data.remaining / 60);
                    const seconds = data.remaining % 60;
                    showToast(`⏳ Aguarde! Nova atualização em ${{minutes}}m ${{seconds}}s`, '#f59e0b');
                    consoleDiv.style.display = 'none';
                    btn.disabled = false;
                    spinner.style.display = 'none';
                    btnText.textContent = '🔄 Atualizar Dados';
                }} else {{
                    showToast('❌ Erro no servidor.', '#ef4444');
                    btn.disabled = false;
                    spinner.style.display = 'none';
                    btnText.textContent = '🔄 Atualizar Dados';
                }}
            }} catch (error) {{
                console.error('Erro:', error);
                showToast('❌ Servidor offline.', '#ef4444');
                btn.disabled = false;
                spinner.style.display = 'none';
                btnText.textContent = '🔄 Atualizar Dados';
            }}
        }}

        // Filtro para cards do dashboard
        let activeFilter = null;

        function filterOrders(status) {{
            const cards = document.querySelectorAll('.order-card');
            const dashCards = document.querySelectorAll('.dash-card');
            const banner = document.getElementById('filterBanner');
            const bannerText = document.getElementById('filterBannerText');

            const labels = {{
                'nao_enviado': '📭 Mostrando: Não Enviados',
                'em_transito': '🚚 Mostrando: Em Trânsito',
                'entregue': '✅ Mostrando: Entregues',

                'devolvido': '↩️ Mostrando: Devolvidos ao Remetente'
            }};

            if (status === activeFilter || status === null) {{
                activeFilter = null;
                cards.forEach(card => {{
                    card.classList.remove('order-hidden');
                }});
                dashCards.forEach(dc => dc.classList.remove('active'));
                banner.classList.remove('visible');
                return;
            }}

            activeFilter = status;

            cards.forEach(card => {{
                if (card.getAttribute('data-status') === status) {{
                    card.classList.remove('order-hidden');
                }} else {{
                    card.classList.add('order-hidden');
                }}
            }});

            dashCards.forEach(dc => {{
                if (dc.getAttribute('data-filter') === status) {{
                    dc.classList.add('active');
                }} else {{
                    dc.classList.remove('active');
                }}
            }});

            bannerText.textContent = labels[status];
            banner.classList.add('visible');

            const first = document.querySelector('.order-card[data-status="' + status + '"]:not(.order-hidden)');
            if (first) {{
                first.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }}
        }}

        if (window.location.search.includes('updated=true')) {{
            showToast('✅ Relatório atualizado com sucesso!', '#22c55e');
        }}
    </script>
    <script src="alert_frete.js?v={versao_cache}"></script>
</body>
</html>
        """

        orders_html = []
        atrasados_data = []
        entregues_count = 0
        devolvidos_count = 0
        nao_enviados_count = 0
        em_transito_count = 0
        
        PEDIDOS_IGNORADOS = ["39192"]

        for venda in vendas:
            pedido = venda.get("Número do Pedido no Tiny")
            if pedido in PEDIDOS_IGNORADOS:
                continue
                
            rastreio = venda.get("Código de Rastreio")
            situacao_tiny = venda.get("Situação")
            
            print(f"Processando {pedido}...")
            obj_data = consultar_objeto(rastreio, token)
            
            # Verificação de status
            is_entregue = False
            is_devolvido = False
            is_postado = False
            data_postagem_dt = None
            data_devolucao_dt = None
            data_entrega_dt = None
            ultimo_evento_desc = ""
            ultimo_local = ""
            events_html = []
            
            if obj_data and "eventos" in obj_data:
                for i, evento in enumerate(obj_data["eventos"]):
                    events_html.append(formatar_evento_html(evento))
                    desc_upper = evento.get("descricao", "").upper()
                    detalhe_upper = evento.get("detalhe", "").upper() if evento.get("detalhe") else ""
                    
                    # Captura info do evento mais recente (primeiro da lista)
                    if i == 0:
                        ultimo_evento_desc = evento.get("descricao", "")
                        unidade = evento.get("unidade", {})
                        endereco = unidade.get("endereco", {})
                        cidade = endereco.get("cidade", "")
                        uf = endereco.get("uf", "")
                        ultimo_local = f"{cidade}/{uf}".strip("/")
                    
                    if "REMETENTE" in desc_upper or "DEVOLVIDO" in desc_upper or "DEVOLUÇÃO" in desc_upper:
                        is_devolvido = True
                        if data_devolucao_dt is None:
                            try:
                                data_devolucao_dt = datetime.fromisoformat(evento.get("dtHrCriado", ""))
                            except:
                                pass
                    elif "ENTREGUE" in desc_upper:
                        is_entregue = True
                        if data_entrega_dt is None:
                            try:
                                data_entrega_dt = datetime.fromisoformat(evento.get("dtHrCriado", ""))
                            except:
                                pass

                    if "POSTADO" in desc_upper:
                        is_postado = True
                        try:
                            data_postagem_dt = datetime.fromisoformat(evento.get("dtHrCriado", ""))
                        except:
                            data_postagem_dt = None
            else:
                events_html.append('<div class="event"><em>Sem informações de rastreio disponíveis nos Correios para este objeto.</em></div>')
            
            # Classifica o status do pedido
            if is_devolvido:
                status_category = "devolvido"
                devolvidos_count += 1
                print(f">> Pedido #{pedido} ({rastreio}) — Status: DEVOLVIDO AO REMETENTE")
            elif is_entregue:
                status_category = "entregue"
                entregues_count += 1
                print(f">> Pedido #{pedido} ({rastreio}) — Status: Entregue")

            elif is_postado:
                status_category = "em_transito"
                em_transito_count += 1
            else:
                status_category = "nao_enviado"
                nao_enviados_count += 1

            # Calcula dias em trânsito e coleta dados de atrasados
            if data_postagem_dt and status_category in ("em_transito", "entregue", "devolvido"):
                if is_entregue and not is_devolvido:
                    # Para entregues, não mostra como atrasado
                    pass
                else:
                    dias_transito = (datetime.now() - data_postagem_dt).days
                    if dias_transito > 3:
                        atrasados_data.append({
                            "pedido": pedido,
                            "rastreio": rastreio,
                            "situacao_tiny": situacao_tiny,
                            "data_postagem": data_postagem_dt.strftime("%d/%m/%Y"),
                            "dias_transito": dias_transito,
                            "ultimo_evento": ultimo_evento_desc,
                            "ultimo_local": ultimo_local,
                            "status": status_category
                        })

            # Esconde entregues e devolvidos conforme nova regra
            hidden_class = ""
            now = datetime.now()

            if status_category == "devolvido":
                if data_devolucao_dt and (now - data_devolucao_dt).total_seconds() > 24 * 3600:
                    hidden_class = "order-hidden"
            elif status_category == "entregue":
                if data_entrega_dt:
                    delivered_this_week = (data_entrega_dt.isocalendar()[:2] == now.isocalendar()[:2])
                    if delivered_this_week:
                        after_friday_18 = (now.weekday() == 4 and now.hour >= 18) or (now.weekday() > 4)
                        if after_friday_18:
                            hidden_class = "order-hidden"
                    else:
                        hidden_class = "order-hidden"
                else:
                    hidden_class = "order-hidden"

            card = f"""
            <div class="order-card {hidden_class}" data-status="{status_category}">
                <div class="order-header">
                    <div class="order-title">Pedido Tiny #{pedido} — {rastreio}</div>
                    <div class="order-tiny-status">Status Tiny: {situacao_tiny}</div>
                </div>
                <div class="events-container">
                    {''.join(events_html)}
                </div>
            </div>
            """
            orders_html.append(card)
            time.sleep(0.2)
        
        print(f"\nRelatório gerado. Entregues: {entregues_count} | Devolvidos: {devolvidos_count}")

        # Monta o dashboard de resumo
        dashboard_html = f"""
        <div class="dashboard">
            <div class="dash-card dash-clickable" onclick="filterOrders('nao_enviado')" data-filter="nao_enviado">
                <div class="dash-icon dash-icon-orange">📭</div>
                <div class="dash-info">
                    <span class="dash-number dash-number-orange">{nao_enviados_count}</span>
                    <span class="dash-label">Não Enviados</span>
                </div>
            </div>
            <div class="dash-card dash-clickable" onclick="filterOrders('em_transito')" data-filter="em_transito">
                <div class="dash-icon dash-icon-blue">🚚</div>
                <div class="dash-info">
                    <span class="dash-number dash-number-blue">{em_transito_count}</span>
                    <span class="dash-label">Em Trânsito</span>
                </div>
            </div>
            <div class="dash-card dash-clickable" onclick="filterOrders('entregue')" data-filter="entregue">
                <div class="dash-icon dash-icon-green">✅</div>
                <div class="dash-info">
                    <span class="dash-number dash-number-green">{entregues_count}</span>
                    <span class="dash-label">Entregues</span>
                </div>
            </div>

            <div class="dash-card dash-clickable" onclick="filterOrders('devolvido')" data-filter="devolvido">
                <div class="dash-icon dash-icon-purple">↩️</div>
                <div class="dash-info">
                    <span class="dash-number dash-number-purple">{devolvidos_count}</span>
                    <span class="dash-label">Devolvidos</span>
                </div>
            </div>
        </div>
        <div id="filterBanner" class="filter-banner">
            <span class="filter-banner-text" id="filterBannerText"></span>
            <button class="filter-banner-close" onclick="filterOrders(null)">✕ Mostrar Todos</button>
        </div>
        """

        # Monta link para página de atrasados
        if len(atrasados_data) > 0:
            atrasados_link_html = f'<a href="pedidos_atrasados.html" class="atrasados-link">⏰ Pedidos Atrasados <span class="atrasados-count">{len(atrasados_data)}</span></a>'
        else:
            atrasados_link_html = ''

        final_html = html_template.format(
            data_geracao=time.strftime('%d/%m/%Y %H:%M:%S'),
            dashboard=dashboard_html,
            content=''.join(orders_html),
            atrasados_link=atrasados_link_html,
            versao_cache=int(time.time())
        )
            
        # Salva o relatório na raiz do projeto (um nível acima de Arquivos/)
        pasta_projeto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caminho_html = os.path.join(pasta_projeto, RELATORIO_HTML)
        
        with open(caminho_html, mode='w', encoding='utf-8') as f:
            f.write(final_html)
            
        print(f"\nSucesso! Relatório HTML premium salvo em '{caminho_html}'.")

        # ===== GERA PÁGINA DE PEDIDOS ATRASADOS =====
        atrasados_data.sort(key=lambda x: x["dias_transito"], reverse=True)

        data_geracao_atrasados = time.strftime('%d/%m/%Y %H:%M:%S')
        total_atrasados = len(atrasados_data)

        # Calcula contagens por urgência
        criticos = len([x for x in atrasados_data if x["dias_transito"] >= 7])
        altos = len([x for x in atrasados_data if 5 <= x["dias_transito"] < 7])
        atencao = len([x for x in atrasados_data if x["dias_transito"] < 5])

        rows_html = ""
        for item in atrasados_data:
            dias = item["dias_transito"]
            if dias >= 7:
                urgencia_class = "urgencia-alta"
                urgencia_label = "CRÍTICO"
            elif dias >= 5:
                urgencia_class = "urgencia-media"
                urgencia_label = "ALTO"
            else:
                urgencia_class = "urgencia-baixa"
                urgencia_label = "ATENÇÃO"
            
            status_label = {"em_transito": "Em Trânsito", "devolvido": "Devolvido"}.get(item["status"], item["status"])

            rows_html += f"""
            <tr class="{urgencia_class}">
                <td><strong>#{item["pedido"]}</strong></td>
                <td><code>{item["rastreio"]}</code></td>
                <td>{item["data_postagem"]}</td>
                <td><span class="dias-badge {urgencia_class}">{dias} dias</span></td>
                <td><span class="urgencia-tag {urgencia_class}">{urgencia_label}</span></td>
                <td>{item["ultimo_evento"]}</td>
                <td>{item["ultimo_local"]}</td>
                <td>{status_label}</td>
            </tr>
            """

        if total_atrasados > 0:
            tabela_conteudo = f"""
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Pedido</th>
                        <th>Rastreio</th>
                        <th>Postagem</th>
                        <th>Dias</th>
                        <th>Urgência</th>
                        <th>Último Evento</th>
                        <th>Local</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>"""
        else:
            tabela_conteudo = """
        <div class="table-wrapper">
            <div class="empty-state">
                <div class="emoji">🎉</div>
                <h2>Nenhum pedido atrasado!</h2>
                <p>Todos os pedidos estão dentro do prazo de 3 dias.</p>
            </div>
        </div>"""

        atrasados_html_page = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pedidos Atrasados — Mais de 3 Dias</title>
    <style>
        :root {{
            --primary: #dc2626;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #1e293b;
            --text-sub: #64748b;
            --border: #e2e8f0;
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
        .container {{ max-width: 1100px; margin: 0 auto; }}
        header {{ text-align: center; margin-bottom: 30px; }}
        h1 {{ margin: 0; font-size: 2.2rem; background: linear-gradient(135deg, #dc2626, #b91c1c); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
        .meta {{ color: var(--text-sub); margin-top: 8px; }}

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
        .num-total {{ color: #dc2626; }}
        .num-critico {{ color: #b91c1c; }}
        .num-alto {{ color: #ea580c; }}
        .num-atencao {{ color: #f59e0b; }}

        /* Table */
        .table-wrapper {{
            background: var(--card-bg);
            border-radius: 14px;
            border: 1px solid var(--border);
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.08);
        }}
        table {{ width: 100%; border-collapse: collapse; }}
        thead th {{
            background: var(--border);
            padding: 14px 16px;
            text-align: left;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-sub);
            font-weight: 700;
        }}
        tbody td {{
            padding: 14px 16px;
            border-bottom: 1px solid var(--border);
            font-size: 0.9rem;
        }}
        tbody tr:last-child td {{ border-bottom: none; }}
        tbody tr {{ transition: background 0.15s; }}
        tbody tr:hover {{ background: rgba(37, 99, 235, 0.04); }}
        code {{
            background: var(--border);
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.85rem;
        }}

        /* Urgency Tags */
        .dias-badge {{
            padding: 4px 12px;
            border-radius: 99px;
            font-weight: 700;
            font-size: 0.82rem;
            display: inline-block;
        }}
        .urgencia-tag {{
            padding: 3px 10px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .urgencia-alta {{ }}
        .urgencia-alta .dias-badge, .dias-badge.urgencia-alta {{ background: #fee2e2; color: #b91c1c; }}
        .urgencia-tag.urgencia-alta {{ background: #dc2626; color: white; }}
        .urgencia-media {{ }}
        .dias-badge.urgencia-media {{ background: #fff7ed; color: #ea580c; }}
        .urgencia-tag.urgencia-media {{ background: #ea580c; color: white; }}
        .urgencia-baixa {{ }}
        .dias-badge.urgencia-baixa {{ background: #fef9c3; color: #ca8a04; }}
        .urgencia-tag.urgencia-baixa {{ background: #f59e0b; color: white; }}

        tr.urgencia-alta {{ border-left: 4px solid #dc2626; }}
        tr.urgencia-media {{ border-left: 4px solid #ea580c; }}
        tr.urgencia-baixa {{ border-left: 4px solid #f59e0b; }}

        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: var(--text-sub);
        }}
        .empty-state .emoji {{ font-size: 3rem; margin-bottom: 10px; }}

        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .table-wrapper {{ animation: fadeIn 0.5s ease; }}
        .summary-card {{ animation: fadeIn 0.4s ease forwards; }}
        .summary-card:nth-child(2) {{ animation-delay: 0.1s; }}
        .summary-card:nth-child(3) {{ animation-delay: 0.2s; }}
        .summary-card:nth-child(4) {{ animation-delay: 0.3s; }}

        @media (max-width: 700px) {{
            table {{ font-size: 0.8rem; }}
            thead th, tbody td {{ padding: 10px 8px; }}
        }}
    </style>
</head>
<body>
    <button class="btn-theme" onclick="toggleTheme()">🌓 Tema</button>
    <div class="container">
        <header>
            <h1>⏰ Pedidos Atrasados</h1>
            <div class="meta">Pedidos com mais de 3 dias em trânsito — Gerado em: {data_geracao_atrasados}</div>
            <a href="relatorio_rastreio.html" class="back-link">← Voltar ao Painel Principal</a>
        </header>

        <div class="summary">
            <div class="summary-card">
                <div class="summary-number num-total">{total_atrasados}</div>
                <div class="summary-label">Total Atrasados</div>
            </div>
            <div class="summary-card">
                <div class="summary-number num-critico">{criticos}</div>
                <div class="summary-label">Crítico (7+ dias)</div>
            </div>
            <div class="summary-card">
                <div class="summary-number num-alto">{altos}</div>
                <div class="summary-label">Alto (5-6 dias)</div>
            </div>
            <div class="summary-card">
                <div class="summary-number num-atencao">{atencao}</div>
                <div class="summary-label">Atenção (4-3 dias)</div>
            </div>
        </div>

        {tabela_conteudo}
    </div>

    <script>
        function setTheme(theme) {{
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
        }}
        function toggleTheme() {{
            const current = localStorage.getItem('theme') || 'light';
            setTheme(current === 'light' ? 'dark' : 'light');
        }}
        setTheme(localStorage.getItem('theme') || 'light');
    </script>
    <script src="alert_frete.js?v={int(time.time())}"></script>
</body>
</html>"""

        caminho_atrasados = os.path.join(pasta_projeto, RELATORIO_ATRASADOS)
        with open(caminho_atrasados, mode='w', encoding='utf-8') as f:
            f.write(atrasados_html_page)

        print(f"Página de atrasados salva em '{caminho_atrasados}' ({len(atrasados_data)} pedido(s) com mais de 3 dias).")
                
    except Exception as e:
        print(f"Erro no processamento: {e}")

if __name__ == "__main__":
    processar()
