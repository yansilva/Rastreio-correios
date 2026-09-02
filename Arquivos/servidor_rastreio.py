import http.server
import socketserver
import os
import executar_rastreio  # type: ignore
import webbrowser
import time
import sys
import threading
import queue
from threading import Timer

PORT = 8000
HTML_FILE = "relatorio_rastreio.html"
LAST_UPDATE_TIME = 0
COOLDOWN_SECONDS = 150  # 2.5 minutos
AUTO_UPDATE_INTERVAL = 2700  # 45 minutos em segundos
NEXT_UPDATE_TIME = 0

# Fila para armazenar logs e enviar via SSE
log_queue = queue.Queue()

class StreamToQueue:
    def __init__(self, original_stream):
        self.original_stream = original_stream

    def write(self, data):
        self.original_stream.write(data)
        self.original_stream.flush()
        if data.strip():
            log_queue.put(data.strip())

    def flush(self):
        self.original_stream.flush()

# Redireciona stdout para capturar logs
sys.stdout = StreamToQueue(sys.stdout) # type: ignore

class RastreioHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        print(f"[DEBUG] do_GET path: '{self.path}'")
        if self.path == '/logs':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()
            
            # Streaming de logs
            try:
                while True:
                    try:
                        message = log_queue.get(timeout=1)
                        self.wfile.write(f"data: {message}\n\n".encode())
                        self.wfile.flush()
                    except queue.Empty:
                        # Envia keep-alive
                        self.wfile.write(b": keep-alive\n\n")
                        self.wfile.flush()
            except Exception:
                pass
            return

        if self.path == '/proxima-atualizacao':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            remaining = max(0, int(NEXT_UPDATE_TIME - time.time()))
            from datetime import datetime as dt_cls
            next_time_str = dt_cls.fromtimestamp(NEXT_UPDATE_TIME).strftime("%H:%M") if NEXT_UPDATE_TIME > 0 else "--:--"
            self.wfile.write(f'{{"remaining": {remaining}, "next_time": "{next_time_str}"}}'.encode())
            return

        # Serve o arquivo HTML da raiz do projeto (um nível acima)
        if self.path == '/' or self.path == f'/{HTML_FILE}':
            dir_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            caminho_html = os.path.join(dir_raiz, HTML_FILE)
            if os.path.exists(caminho_html):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                with open(caminho_html, 'rb') as f:
                    self.wfile.write(f.read())
                return

        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        global LAST_UPDATE_TIME
        if self.path == '/atualizar':
            current_time = time.time()
            time_passed = current_time - LAST_UPDATE_TIME
            
            if time_passed < COOLDOWN_SECONDS:
                remaining = int(COOLDOWN_SECONDS - time_passed)
                self.send_response(429)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(f'{{"remaining": {remaining}}}'.encode())
                return

            print("\n" + "="*40)
            print("[ATUALIZACAO] SOLICITACAO DE ATUALIZACAO VIA WEB")
            print("="*40)
            
            def run_update():
                global LAST_UPDATE_TIME, NEXT_UPDATE_TIME
                try:
                    import importlib
                    import consulta_correios
                    import executar_rastreio
                    importlib.reload(consulta_correios)
                    importlib.reload(executar_rastreio)
                    executar_rastreio.main()
                    LAST_UPDATE_TIME = time.time()
                    NEXT_UPDATE_TIME = time.time() + AUTO_UPDATE_INTERVAL
                    log_queue.put("✅ PROCESSO FINALIZADO")
                except Exception as e:
                    print(f"[ERRO] Erro na atualizacao: {e}")
                    log_queue.put(f"[ERRO] Erro: {e}")

            threading.Thread(target=run_update).start()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "started"}')
        else:
            self.send_response(404)
            self.end_headers()

def open_browser():
    webbrowser.open(f"http://localhost:{PORT}")

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == "__main__":
    import sys
    # Define o diretório onde o script do servidor está localizado (pasta 'Arquivos')
    dir_arquivos = os.path.dirname(os.path.abspath(__file__))
    # Define o diretório raiz (um nível acima) onde está o HTML
    dir_raiz = os.path.dirname(dir_arquivos)
    
    # Adiciona 'Arquivos' ao path do sistema para importar 'executar_rastreio'
    if dir_arquivos not in sys.path:
        sys.path.append(dir_arquivos)
    
    # MUITO IMPORTANTE: Mudar para o diretório raiz para que o SimpleHTTPRequestHandler
    # encontre o relatorio_rastreio.html na pasta correta ao ser acessado.
    os.chdir(dir_raiz)
    
    # Atualização automática a cada 45 minutos
    def auto_update_loop():
        global NEXT_UPDATE_TIME, LAST_UPDATE_TIME
        NEXT_UPDATE_TIME = time.time() + AUTO_UPDATE_INTERVAL
        while True:
            time.sleep(AUTO_UPDATE_INTERVAL)
            print("\n" + "="*40)
            print("[ATUALIZACAO] ATUALIZACAO AUTOMATICA (45 MIN)")
            print("="*40)
            try:
                import importlib
                import consulta_correios
                import executar_rastreio as exec_rastreio
                importlib.reload(consulta_correios)
                importlib.reload(exec_rastreio)
                exec_rastreio.main()
                LAST_UPDATE_TIME = time.time()
                NEXT_UPDATE_TIME = time.time() + AUTO_UPDATE_INTERVAL
                log_queue.put("✅ ATUALIZAÇÃO AUTOMÁTICA FINALIZADA")
            except Exception as e:
                print(f"[ERRO] Erro na atualizacao automatica: {e}")
                NEXT_UPDATE_TIME = time.time() + AUTO_UPDATE_INTERVAL

    threading.Thread(target=auto_update_loop, daemon=True).start()
    print(f"[TIMER] Atualizacao automatica configurada a cada 45 minutos.")

    with ThreadedTCPServer(("", PORT), RastreioHandler) as httpd:
        print(f"\n[SERVIDOR] Painel de Rastreio Rodando em: http://localhost:{PORT}")
        print(f"[SERVIDOR] Servindo arquivos de: {os.getcwd()}")
        print("Mantenha esta janela aberta para o botão 'Atualizar' funcionar.")
        
        Timer(1.5, open_browser).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor encerrado.")
            httpd.server_close()
