# 📦 Rastreio Correios & Tiny ERP

[![CI](https://github.com/yansilva/Rastreio-correios/actions/workflows/ci.yml/badge.svg)](https://github.com/yansilva/Rastreio-correios/actions/workflows/ci.yml)
[![Secured by GitGuard](https://img.shields.io/badge/Secured%20by-GitGuard-success?style=flat-square)](https://www.gitguard.com.br/yansilva)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue?style=flat-square)]()
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg?style=flat-square)](https://github.com/astral-sh/ruff)

Sistema automatizado em Python para consulta de rastreamento de encomendas, auditoria de prazos de entrega e cálculo/cotação de fretes via API dos Correios, integrado ao **Tiny ERP**.

---

## 🚀 Funcionalidades

- **Sincronização com Tiny ERP:** Busca pedidos ativos, verifica status e códigos de rastreamento pendentes ou expedidos recentemente.
- **Rastreamento Correios em Lote:** Consulta automática via API oficial dos Correios (autenticação por contrato e token), destacando objetos aguardando retirada ou com atrasos.
- **Auditoria de Entregas & Prazos:** Identificação e destaque de pedidos com atraso na entrega em relação ao prazo prometido.
- **Painel Web Local:** Dashboard embutido com interface visual moderna, busca instantânea client-side por pedido/cliente/rastreio/cidade, filtros dinâmicos de status, modo escuro e atualização em tempo real (Server-Sent Events).
- **Cotação e Comparação de Fretes:** Simulação e conferência de preços/prazos (SEDEX, PAC, Mini Envios) direto com a API dos Correios.
- **Alertas Automatizados:** Geração de relatórios com alertas visuais e sonoros para divergências e prazos estendidos.
- **Validação e Qualidade Contínua (CI):** Pipeline automatizado no GitHub Actions para cada push e pull request validando compilação, lint (Ruff) e testes em matriz Python 3.11 e 3.12.

---

## 📁 Estrutura do Projeto

```text
Rastreio-correios/
├── .github/
│   └── workflows/
│       └── ci.yml           # Pipeline automatizado de CI (Python 3.11 e 3.12)
├── run.py                   # Ponto de entrada principal da aplicação
├── ABRIR_PAINEL.bat         # Inicializador rápido para Windows (com suporte a venv)
├── pyproject.toml           # Configurações do projeto, Ruff, Pytest e Cobertura
├── requirements.txt         # Dependências de produção
├── requirements-dev.txt     # Ferramentas de desenvolvimento, lint e testes
├── .env.example             # Modelo de configuração das variáveis de ambiente
├── .gitignore               # Arquivos e pastas ignorados pelo Git
├── README.md                # Documentação do projeto
├── docs/
│   └── architecture.md      # Documentação detalhada da arquitetura e fluxos
├── web/                     # Frontend estático modular (HTML, CSS e JavaScript)
│   ├── css/
│   │   ├── main.css         # Design tokens, variáveis CSS (:root / dark), tipografia e reset
│   │   └── components.css   # Cards de status, tabela de atrasados, timeline, console SSE e toasts
│   └── js/
│       ├── app.js           # Gerenciamento de tema claro/escuro e sistema Toast
│       ├── dashboard.js     # Busca instantânea e filtros dinâmicos por status
│       └── logs.js          # Streaming SSE de logs, cooldown e contagem regressiva
├── tests/                   # Suíte de testes automatizados (143 testes mockados)
│   ├── test_tiny.py         # Testes da camada Tiny ERP (11 testes)
│   ├── test_correios.py     # Testes da camada Correios SRO (20 testes)
│   ├── test_frete.py        # Testes da camada de Frete (67 testes)
│   ├── test_server.py       # Testes da camada do Servidor (35 testes)
│   └── test_frontend.py     # Testes dos assets web e integração de templates (7 testes)
└── Arquivos/
    ├── tiny/                # Pacote modular Tiny ERP (client, service, models, config)
    ├── correios/            # Pacote modular Correios SRO (client, tracking, models)
    ├── frete/               # Pacote modular Frete (client, service, report, models)
    ├── server/              # Pacote modular Servidor HTTP (config, security, handler, service)
    ├── servidor_rastreio.py # Fachada de compatibilidade do servidor
    ├── consulta_correios.py # Orquestrador de rastreamento
    ├── consulta_frete.py    # Orquestrador de frete
    ├── tiny_rastreio.py     # Orquestrador de coleta do Tiny
    └── ABRIR_PAINEL.sh      # Inicializador para sistemas Unix (Linux/macOS)
```

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.11 / 3.12**
- **Requests** (consumo de APIs REST com timeout explícito)
- **Python-dotenv** (gerenciamento seguro de configurações e credenciais)
- **Pytest** e **unittest.mock** (136 testes automatizados rápidos e isolados)
- **Pytest-cov** (relatórios de cobertura de código)
- **Ruff** (linter e formatador de código estático de alta performance)
- **GitHub Actions** (integração contínua e validação automática em matriz multi-versão)
- **HTML5 / CSS3 / JavaScript / SSE** (Dashboard local com streaming de logs em tempo real)

---

## ⚙️ Configuração e Instalação

### 1. Pré-requisitos
- Python 3.11 ou superior instalado.
- Acesso à API do Tiny ERP (Token de API).
- Cartão de postagem / contrato ativo nos Correios e código de acesso à API dos Correios.

### 2. Clonar o Repositório
```bash
git clone https://github.com/yansilva/Rastreio-correios.git
cd Rastreio-correios
```

### 3. Criar e Ativar Ambiente Virtual (Recomendado)
No Windows:
```cmd
python -m venv venv
venv\Scripts\activate
```

No Linux/macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Instalar as Dependências

Para executar o sistema em produção/operação:
```bash
pip install -r requirements.txt
```

Para desenvolvimento, execução de testes e lint:
```bash
pip install -r requirements-dev.txt
```

### 5. Configurar as Variáveis de Ambiente
Copie o arquivo `.env.example` para `.env` e preencha com suas credenciais:
```bash
copy .env.example .env
```

Edite o arquivo `.env`:
```env
# Tiny ERP
TOKEN_TINY=seu_token_aqui

# Correios API
ID_CORREIOS=seu_id_ou_cnpj_aqui
CONTRATO=seu_numero_contrato_aqui
CODIGO_ACESSO=seu_codigo_de_acesso_aqui

# Configuração de envio
CEP_ORIGEM=seu_cep_origem_aqui

# Pedidos que ficam fora do painel (números separados por vírgula; padrão 39192; vazio não ignora nada)
PEDIDOS_IGNORADOS=39192

# Servidor (Opcional - padrão: 127.0.0.1:8000)
SERVER_HOST=127.0.0.1
SERVER_PORT=8000

# Abre o navegador ao iniciar (padrão 1; use 0 para não abrir). O Docker já define 0.
# ABRIR_NAVEGADOR=1
```

---

## 🖥️ Como Usar

### Inicialização Principal (Recomendada)
A partir da raiz do projeto:
```bash
python run.py
```
- **Windows:** Duplo clique no arquivo `ABRIR_PAINEL.bat`.
- **Linux/macOS:** Execute `./Arquivos/ABRIR_PAINEL.sh`.

O painel será aberto automaticamente no navegador em `http://localhost:8000`.

### Rodar com Docker
Alternativa ao `ABRIR_PAINEL.bat`: o painel roda num container, reinicia sozinho e fica acessível no PC e no celular pelo Wi-Fi. Requer o Docker Desktop aberto e o `.env` preenchido na pasta do projeto.

Na pasta do projeto:
```powershell
docker compose up -d --build
```

- **Acesso:** `http://localhost:8000` no PC e `http://IP-do-PC:8000` no celular (o IP aparece no `ipconfig`).
- **Parar:** `docker compose down`. **Logs:** `docker compose logs -f painel`.
- **Só este PC:** em `docker-compose.yml`, troque `"0.0.0.0:8000:8000"` por `"127.0.0.1:8000:8000"`. Com isso, o celular não alcança o painel.
- **Por que a porta precisa do IP:** o servidor só aceita cliente de rede local (`ip_na_rede_local`) e confere o cabeçalho Host. Com Docker, o IP de origem que o servidor vê é sempre o gateway da rede do Docker (ex.: `172.20.0.1`), e não o IP do celular. Assim, a checagem de IP não separa um aparelho do outro. O que limita o acesso é a porta publicada: `0.0.0.0:8000` escuta só no IPv4 da rede (Wi-Fi e cabo) e `127.0.0.1` só neste PC. Sem o `0.0.0.0:` o Docker também publica em IPv6 (`[::]:8000`), e o IPv6 global do Wi-Fi chega ao painel sem a checagem de IP fazer efeito.
- **Porta 8000 obrigatória no PC:** o servidor recusa um cabeçalho Host com outra porta. Por isso, publicar em outra porta do PC (ex.: `8010:8000`) não funciona no painel.
- **Segurança do container:** sistema de arquivos só de leitura (`read_only`), exceto a pasta do projeto e `/tmp`; sem capacidades do Linux (`cap_drop: ALL`); `no-new-privileges`. `.git`, `.equipe` e `.env` entram como somente leitura.
- **Reinício:** `restart: unless-stopped`. Para voltar após reiniciar o PC, o Docker Desktop precisa abrir sozinho (Configurações do Docker Desktop, "Start Docker Desktop when you log in").
- **Dados:** a pasta do projeto entra no container (`.:/app`). O `.env`, as páginas HTML e `Arquivos/rastreios_cache.json`, `Arquivos/rastreios_tiny.csv` e `Arquivos/entregas_historico.json` continuam na pasta, como antes. O `.env` não entra na imagem (`**/.env` no `.dockerignore`) e, no container, é somente leitura.
- **Fuso:** `TZ=America/Sao_Paulo` (a imagem traz `tzdata`). Datas e "Dados de" saem no horário de Brasília.
- **Navegador:** não abre dentro do container (`ABRIR_NAVEGADOR=0`). Fora do Docker, o comportamento não muda.
- **Um de cada vez:** não rode o container e o `ABRIR_PAINEL.bat` (ou `ABRIR_PAINEL_CELULAR.bat`) juntos; os dois disputam a porta 8000.
- **IP no log:** no Docker, o log mostra o IP interno do gateway (172.x), e não o IP do aparelho. Por isso a checagem de IP privado não restringe nada no Docker. A proteção fica com a porta publicada só em IPv4 (`0.0.0.0`, ou `127.0.0.1` para só o PC) e com o firewall do Windows, que é responsabilidade do usuário.

### Voltar para o `.bat`
1. No PowerShell, na pasta do projeto: `docker compose down`.
2. Confira que a porta 8000 ficou livre.
3. Só então abra `ABRIR_PAINEL.bat` (só este PC) ou `ABRIR_PAINEL_CELULAR.bat` (celular pelo Wi-Fi).

### Execução dos Módulos Individuais via CLI
1. **Buscar pedidos no Tiny ERP:**
   ```bash
   python Arquivos/tiny_rastreio.py
   ```
2. **Atualizar status de rastreamento nos Correios e gerar relatório:**
   ```bash
   python Arquivos/consulta_correios.py
   ```
3. **Simular/Cotar fretes:**
   ```bash
   python Arquivos/consulta_frete.py
   ```
4. **Execução legada do servidor:**
   ```bash
   python Arquivos/servidor_rastreio.py
   ```

---

## 🧪 Qualidade e Testes Automatizados

O projeto conta com suíte de testes automatizados abrangente e 100% mockada (sem chamadas de rede ou credenciais reais), validada continuamente pelo GitHub Actions:

### 1. Executar os Testes Unitários
```bash
python -m pytest tests/ -v
```

### 2. Executar Cobertura de Código
```bash
python -m pytest tests/ --cov=Arquivos --cov-report=term-missing
```

### 3. Executar Análise Estática (Ruff)
```bash
ruff check .
```

### 4. Validar Sintaxe de Todos os Arquivos
```bash
python -m compileall Arquivos run.py tests
```

---

## 🔒 Segurança e Arquitetura

- **Integração Contínua Segura:** O pipeline no GitHub Actions não requer e não armazena nenhuma credencial ou secret real, pois toda a suíte é executada sobre mocks.
- **Proteção Anti-Path Traversal:** O servidor HTTP valida canonicamente os caminhos e bloqueia acesso a arquivos fora da raiz, arquivos ocultos (`.env`, `.git`) ou código-fonte (`.py`).
- **Sanitização de Streaming:** Tokens e chaves de API são interceptados e mascarados antes do envio ao navegador via SSE.
- **Credenciais Seguras:** Nenhuma credencial trafega ou é gravada no versionamento.
- Para detalhes arquiteturais completos, consulte [docs/architecture.md](docs/architecture.md).

---

## 📄 Licença

Projeto desenvolvido para uso operacional e portfólio profissional.
