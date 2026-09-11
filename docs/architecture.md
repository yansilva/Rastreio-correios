# Arquitetura do Sistema — Rastreio Correios & Frete

## 1. Visão Geral

O **Rastreio-correios** é uma aplicação em Python desenhada para automação logística operacional, auditoria de prazos e cotação de fretes. O sistema integra-se ao **Tiny ERP** e às APIs oficiais dos **Correios** (SRO - Rastreamento e Precificação/Prazos), disponibilizando um servidor HTTP local com painel web interativo para os operadores.

A arquitetura adota um design modular em camadas concêntricas com separação estrita de responsabilidades, alta testabilidade (100% mockada) e segurança defensiva contra vazamento de credenciais e *path traversal*.

---

## 2. Diagrama da Arquitetura

```text
               ┌────────────────────────────────────────────────────────┐
               │              Interface Web / Operador                  │
               │   (Dashboard HTML, Abas, Alertas JS, Streaming SSE)   │
               └───────────────────────────┬────────────────────────────┘
                                           │ HTTP / SSE
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │                     Camada Server                      │
               │               (Arquivos/server/ / run.py)              │
               │                                                        │
               │  - ServerConfig: Host, Porta (8000), Cooldown, Paths   │
               │  - Security: Anti-Path Traversal & Whitelist de Assets │
               │  - UpdateManager: Cooldown 150s & Loop Auto (45 min)   │
               │  - RastreioRequestHandler: GET, POST /atualizar, SSE   │
               │  - ThreadedTCPServer: Concorrência multi-cliente       │
               └───────────────────────────┬────────────────────────────┘
                                           │
                        ┌──────────────────┼──────────────────┐
                        │                  │                  │
                        ▼                  ▼                  ▼
             ┌────────────────────┐ ┌──────────────┐ ┌────────────────┐
             │    Camada Tiny     │ │ Camada Correios│ │  Camada Frete  │
             │  (Arquivos/tiny/)  │ │(Arquivos/correios)│ (Arquivos/frete)│
             └──────────┬─────────┘ └──────┬───────┘ └────────┬───────┘
                        │                  │                  │
                        ▼                  ▼                  ▼
                 API REST Tiny       API REST SRO       API Preço/Prazo
                    (JSON)           (Bearer Token)     (Bearer Token)
```

---

## 3. Responsabilidades por Módulo

### 3.1 Camada Server (`Arquivos/server/` & `run.py`)
- **`run.py`**: Ponto de entrada canônico na raiz da aplicação.
- **`config.py` (`ServerConfig`)**: Centralização de configurações (porta padrão `8000`, host `127.0.0.1`, diretório base, arquivos estáticos permitidos, leitura opcional de `SERVER_HOST` e `SERVER_PORT`).
- **`security.py` (`resolve_safe_path`)**: Validação canônica de arquivos, impedindo *directory traversal* (`../`), bloqueando acesso a arquivos confidenciais (`.env`, `.git`) e extensões executáveis (`.py`, `.bat`).
- **`service.py` (`UpdateManager`)**: Controle de estado, trava de concorrência, cooldown entre atualizações manuais (150 segundos) e agendamento de atualizações periódicas automáticas a cada 45 minutos.
- **`logger.py` (`ServerLogQueue`, `StreamToQueue`)**: Fila thread-safe de eventos em tempo real para streaming SSE (`/logs`), sanitizando tokens e credenciais antes da exibição.
- **`handler.py` (`RastreioRequestHandler`)**: Roteamento HTTP, entrega de relatórios HTML, preflight CORS e endpoints REST internos (`/proxima-atualizacao`, `/api/status`, `/atualizar`).
- **`launcher.py`**: Gerenciamento do ciclo de vida do servidor socket multithreaded e abertura segura do navegador padrão.

### 3.2 Camada Tiny ERP (`Arquivos/tiny/`)
- **`client.py` (`TinyClient`)**: Comunicação HTTP isolada com timeout explícito (30s), paginação de pedidos e detecção de erros da API Tiny.
- **`service.py` (`TinyOrderService`)**: Regras de negócio puras (filtragem de pedidos em aberto, extração de código de rastreamento e exportação segura para CSV).
- **`config.py` & `models.py`**: Configuração e tipagem dos pedidos.

### 3.3 Camada Correios Rastreamento (`Arquivos/correios/`)
- **`client.py` (`CorreiosClient`)**: Autenticação HTTP Basic para obtenção e auto-renovação de tokens Bearer em memória, chamadas GET ao SRO com timeout (30s) e tratamento de erros 401/403/429.
- **`tracking.py` (`TrackingService`)**: Normalização de status (entregue, aguardando retirada, devolvido, em trânsito) e cálculo de urgência de atrasos.
- **`models.py` & `exceptions.py`**: Representações tipadas de eventos e exceções especializadas.

### 3.4 Camada de Cotação de Frete (`Arquivos/frete/`)
- **`client.py` (`FreteClient`)**: Comunicação com os endpoints oficiais de cálculo de preço e prazo nacional dos Correios.
- **`service.py` (`FreteService`)**: Sanitização e validação de CEP, cálculo de cubagem, resolução de dimensões mínimas, classificação por menor custo/prazo e tolerância graciosa a indisponibilidade pontual de prazos.
- **`report.py` (`FreteReportGenerator`)**: Geração dos relatórios `opcoes_frete.html` e alertas em `alert_frete.js`.

---

## 4. Fluxo de Dados Operacional

1. **Inicialização:**
   - O operador inicia o painel executando `python run.py` (ou com duplo clique em `ABRIR_PAINEL.bat`).
   - O servidor inicia na porta `8000` e agenda a abertura do navegador padrão.
   - Uma thread daemon inicia o ciclo de atualização automática a cada 45 minutos.

2. **Ciclo de Atualização de Dados:**
   - O operador clica em **Atualizar** no painel (ou o timer dispara automaticamente).
   - O `UpdateManager` verifica o cooldown de 150s. Se liberado, responde `200 {"status": "started"}` e inicia uma thread assíncrona.
   - **Passo 1 (Tiny):** Busca pedidos com status aberto e extrai códigos de rastreio e dados de destinatário/CEP.
   - **Passo 2 (Correios Rastreio):** Consulta o status atual de cada código no SRO dos Correios e gera o `relatorio_rastreio.html` e `pedidos_atrasados.html`.
   - **Passo 3 (Correios Frete):** Realiza a cotação de PAC, SEDEX e Mini Envios para cada pedido, gerando `opcoes_frete.html` e `alert_frete.js`.
   - Conclusão é notificada via SSE para o painel atualizar as tabelas e contadores.

---

## 5. Diretrizes de Segurança

- **Segregação de Credenciais:** Tokens e códigos de acesso são lidos exclusivamente via variáveis de ambiente (`.env`).
- **Sanitização de Logs:** A fila SSE intercepta e mascara tokens em tempo real (`token=***`, `Bearer ***`).
- **Defesa em Profundidade HTTP:** O servidor rejeita qualquer tentativa de navegação fora da raiz do projeto (`..`), requisições a arquivos `.env`, `.git` ou código Python (`.py`), respondendo com códigos `403` ou `404`.
