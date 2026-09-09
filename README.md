# Busca Rastreio & Gestão de Fretes

[![Secured by GitGuard](https://img.shields.io/badge/Secured%20by-GitGuard-success?style=flat-square)](https://www.gitguard.com.br/yansilva)

Sistema automatizado em Python para consulta de rastreamento de encomendas e cotação de prazos e opções de frete integrado ao **Tiny ERP** e às APIs oficiais dos **Correios**.

---

## 🚀 Funcionalidades

- **Integração Tiny ERP:** Busca pedidos ativos, verifica status e códigos de rastreamento pendentes.
- **Rastreamento Correios:** Monitora o status das encomendas, destacando objetos aguardando retirada ou com atrasos.
- **Cálculo de Prazos e Preços:** Simula prazos de entrega para pedidos sem rastreamento registrado.
- **Painel Web Local:** Servidor embutido com atualização automática e interface visual para acompanhamento em tempo real.
- **Notificações:** Alertas visuais para encomendas com prazos estendidos.

---

## ⚙️ Pré-requisitos e Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/yansilva/Rastreio-correios.git
   cd Rastreio-correios
   ```

2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv Arquivos/venv
   # Windows:
   Arquivos\venv\Scripts\activate
   ```

3. Instale as dependências:
   ```bash
   pip install requests python-dotenv
   ```

---

## 🔐 Configuração das Credenciais

Copie o arquivo de exemplo de ambiente e preencha com suas credenciais:

```bash
copy Arquivos\.env.example Arquivos\.env
```

Edite o arquivo `Arquivos/.env`:
```env
# Tiny ERP
TOKEN_TINY=seu_token_tiny_aqui

# Correios
ID_CORREIOS=seu_cnpj_aqui
CONTRATO=seu_contrato_aqui
CODIGO_ACESSO=seu_codigo_acesso_aqui
```

---

## ▶️ Como Executar

Execute o inicializador no Windows:
```cmd
ABRIR_PAINEL.bat
```

Ou execute diretamente pelo terminal:
```bash
python Arquivos/servidor_rastreio.py
```

O painel será aberto automaticamente no navegador em `http://localhost:8000`.
