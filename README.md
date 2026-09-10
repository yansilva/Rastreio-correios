# 📦 Rastreio Correios & Tiny ERP

[![Secured by GitGuard](https://img.shields.io/badge/Secured%20by-GitGuard-success?style=flat-square)](https://www.gitguard.com.br/yansilva)

Sistema automatizado em Python para consulta de rastreamento de encomendas, auditoria de prazos de entrega e cálculo/cotação de fretes via API dos Correios, integrado ao **Tiny ERP**.

---

## 🚀 Funcionalidades

- **Sincronização com Tiny ERP:** Busca pedidos ativos, verifica status e códigos de rastreamento pendentes ou expedidos recentemente.
- **Rastreamento Correios em Lote:** Consulta automática via API oficial dos Correios (autenticação por contrato e token), destacando objetos aguardando retirada ou com atrasos.
- **Auditoria de Entregas & Prazos:** Identificação e destaque de pedidos com atraso na entrega em relação ao prazo prometido.
- **Painel Web Local:** Dashboard embutido com interface visual amigável e atualização em tempo real via navegador.
- **Cotação e Comparação de Fretes:** Simulação e conferência de preços/prazos (SEDEX, PAC, etc.) direto com a API dos Correios.
- **Alertas Automatizados:** Geração de relatórios com alertas visuais e sonoros para divergências e prazos estendidos.

---

## 📁 Estrutura do Projeto

```text
Rastreio-correios/
├── .env.example             # Modelo de configuração das variáveis de ambiente
├── .gitignore               # Arquivos e pastas ignorados pelo Git
├── requirements.txt         # Dependências do projeto Python
├── ABRIR_PAINEL.bat         # Inicializador rápido para Windows
├── README.md                # Documentação do projeto
└── Arquivos/
    ├── consulta_correios.py # Consulta de status de rastreamento na API dos Correios
    ├── consulta_frete.py    # Consulta e cálculo de frete e prazos nos Correios
    ├── tiny_rastreio.py     # Coleta e exportação de pedidos do Tiny ERP
    ├── servidor_rastreio.py # Servidor HTTP local para servir o dashboard
    ├── ABRIR_PAINEL.sh      # Inicializador para sistemas Unix (Linux/macOS)
    └── ...                  # Scripts auxiliares e ferramentas de análise
```

---

## 🛠️ Tecnologias Utilizadas

- **Python 3**
- **Requests** (consumo de APIs REST)
- **Python-dotenv** (gerenciamento seguro de configurações e credenciais)
- **HTML5 / CSS3 / JavaScript** (Dashboard local e alertas sonoros)

---

## ⚙️ Configuração e Instalação

### 1. Pré-requisitos
- Python 3.8 ou superior instalado.
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
```bash
pip install -r requirements.txt
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
```

---

## 🖥️ Como Usar

### Inicialização Rápida
- **Windows:** Dê um duplo clique no arquivo `ABRIR_PAINEL.bat`.
- **Linux/macOS:** Execute `./Arquivos/ABRIR_PAINEL.sh`.

O painel será aberto no navegador em `http://localhost:8000`.

### Execução dos Módulos via Linha de Comando
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
4. **Abrir o servidor do painel local:**
   ```bash
   python Arquivos/servidor_rastreio.py
   ```

---

## 🔒 Segurança

- **Credenciais Seguras:** Chaves de API e tokens não são expostos no código-fonte nem versionados no repositório.
- **Ambiente Isolado:** O arquivo `.env` e artefatos de build/execução são ignorados pelo `.gitignore`.
- **Verificado por GitGuard:** Repositório higienizado contra vazamento de segredos.

---

## 📄 Licença

Projeto desenvolvido para uso operacional e portfólio profissional.
