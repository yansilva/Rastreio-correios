# ETAPA 5 — REFATORAÇÃO DO SERVIDOR E ORGANIZAÇÃO DO PAINEL

## Objetivo

Melhorar a arquitetura do servidor web e do painel do projeto:

```text id="3w5m5s"
Rastreio-correios
```

Arquivo principal atual:

```text id="lq1c7e"
Arquivos/servidor_rastreio.py
```

O objetivo desta etapa é transformar o servidor em uma camada responsável por:

- iniciar a aplicação;
- servir arquivos;
- controlar rotas;
- comunicar-se com os serviços internos;
- retornar dados de forma previsível.

O frontend deve ficar separado da lógica Python.

---

# REGRA PRINCIPAL

NÃO reescrever o servidor do zero.

NÃO modificar as integrações Tiny, Correios ou Frete sem necessidade.

NÃO alterar regras de negócio.

NÃO alterar o comportamento do rastreamento.

NÃO alterar o comportamento da consulta de frete.

NÃO redesenhar completamente o painel nesta etapa.

NÃO adicionar framework web pesado sem necessidade.

NÃO adicionar banco de dados.

NÃO adicionar autenticação de usuários nesta etapa.

O foco é:

```text id="c6bkn2"
ORGANIZAÇÃO
+
SEPARAÇÃO
+
ESTABILIDADE
+
TESTABILIDADE
```

---

# ETAPA 5.1 — Análise do servidor atual

Antes de modificar:

```text id="qr8v2k"
Arquivos/servidor_rastreio.py
```

analisar completamente.

Identificar:

- como o servidor é iniciado;
- qual porta utiliza;
- como abre o navegador;
- quais arquivos serve;
- quais rotas existem;
- como trata requisições;
- como chama outros scripts;
- como acessa relatórios;
- como identifica arquivos;
- como atualiza o painel;
- como trata erros;
- se existe código duplicado;
- se existe HTML dentro do Python;
- se existe JavaScript dentro do Python;
- se existem caminhos absolutos.

NÃO modificar durante a análise inicial.

---

# ETAPA 5.2 — Identificar responsabilidades

Separar conceitualmente o servidor em:

```text id="xj6r3d"
Servidor
│
├── inicialização
├── roteamento
├── arquivos estáticos
├── APIs/dados
├── relatórios
└── abertura do navegador
```

Criar funções pequenas e claras.

Exemplo:

```python id="e6hr7m"
def iniciar_servidor():
    ...


def abrir_navegador():
    ...


def servir_arquivo():
    ...


def processar_requisicao():
    ...
```

Adaptar ao código existente.

Não criar funções artificiais apenas para diminuir o tamanho do arquivo.

---

# ETAPA 5.3 — Criar configuração do servidor

Criar configuração centralizada para:

- host;
- porta;
- diretório web;
- nome da página principal.

Exemplo:

```python id="3s7i8k"
@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    porta: int = 8000
```

Não permitir que informações de configuração sejam espalhadas por vários lugares.

---

# ETAPA 5.4 — Caminhos usando pathlib

Revisar caminhos do projeto.

Preferir:

```python id="h0t6oe"
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
```

Em vez de:

```python id="cx2xy5"
"C:\\Users\\..."
```

ou concatenação manual de strings.

Os caminhos devem funcionar independentemente do computador do usuário.

---

# ETAPA 5.5 — Diretório de arquivos web

Verificar onde estão atualmente:

- HTML;
- CSS;
- JavaScript;
- relatórios.

Definir uma estrutura organizada.

Preferência:

```text id="nzz5sj"
web/
├── index.html
├── pages/
├── css/
│   └── style.css
├── js/
│   ├── app.js
│   ├── alerts.js
│   └── api.js
└── assets/
```

IMPORTANTE:

Não mover arquivos sem verificar quem os utiliza.

Se o painel atual depender de arquivos gerados pelo Python, preservar esse comportamento durante a migração.

---

# ETAPA 5.6 — HTML fora do Python

Identificar qualquer HTML gigantesco dentro de:

```python id="36nvrv"
servidor_rastreio.py
```

ou outros scripts.

Não reescrever o HTML ainda.

Apenas separar a responsabilidade:

```text id="vupx1p"
Python
→ dados

HTML
→ estrutura

CSS
→ aparência

JavaScript
→ interação
```

---

# ETAPA 5.7 — CSS

Caso o CSS esteja embutido diretamente no HTML Python:

separar progressivamente para:

```text id="8r9zya"
web/css/style.css
```

Preservar o visual atual.

Não realizar redesign.

Nesta etapa queremos organização, não mudança estética.

---

# ETAPA 5.8 — JavaScript

Separar scripts JavaScript que estejam:

- dentro do HTML;
- dentro do Python;
- duplicados.

Organizar inicialmente:

```text id="2v7k1k"
web/js/
├── app.js
├── alerts.js
└── api.js
```

Responsabilidades:

### app.js

- inicialização do painel;
- eventos;
- atualização da interface.

### alerts.js

- alertas;
- notificações;
- modais.

### api.js

- chamadas ao servidor;
- atualização dos dados.

Não obrigatoriamente criar todos os arquivos caso algum não seja necessário.

---

# ETAPA 5.9 — API interna do painel

Verificar se o painel atualmente depende diretamente da existência de:

```text id="93my6l"
CSV
HTML
arquivos temporários
```

Identificar essas dependências.

Quando for seguro, criar endpoints internos simples.

Exemplos conceituais:

```text
GET /api/status
GET /api/rastreios
GET /api/pedidos
GET /api/fretes
```

NÃO implementar endpoints que não sejam necessários ao funcionamento atual.

Não criar uma API REST enorme.

---

# ETAPA 5.10 — Respostas JSON

Quando o servidor fornecer dados para o JavaScript, utilizar JSON consistente.

Exemplo:

```json id="odwkwb"
{
    "sucesso": true,
    "dados": []
}
```

Para erro:

```json id="78zj4f"
{
    "sucesso": false,
    "erro": "Mensagem de erro"
}
```

Não colocar informações sensíveis nas respostas.

---

# ETAPA 5.11 — Tratamento de erros HTTP

Verificar respostas adequadas.

Exemplo:

```text id="p59c2m"
200 → sucesso
400 → requisição inválida
404 → recurso não encontrado
500 → erro interno
```

Evitar que um erro no servidor resulte em página vazia ou comportamento silencioso.

Mostrar erro compreensível quando apropriado.

---

# ETAPA 5.12 — Logging do servidor

Adicionar:

```python id="ez1m8t"
logger.info(...)
logger.warning(...)
logger.error(...)
```

Registrar:

- servidor iniciado;
- porta;
- requisição relevante;
- arquivo não encontrado;
- erro interno;
- falha ao carregar relatório.

NUNCA registrar:

- token;
- senha;
- credencial;
- código de acesso;
- conteúdo sensível.

---

# ETAPA 5.13 — Abertura do navegador

Localizar a lógica responsável por abrir:

```text id="an6ql1"
http://localhost:8000
```

Isolar isso:

```python id="ddo4m1"
def abrir_navegador(url: str):
    ...
```

O servidor não deve ficar diretamente acoplado à implementação da abertura do navegador.

---

# ETAPA 5.14 — Porta configurável

A porta padrão deve continuar:

```text id="89ttq5"
8000
```

Mas permitir configuração por variável de ambiente, por exemplo:

```env id="x3jr0u"
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
```

Com valores padrão caso não existam.

Não alterar o comportamento padrão.

---

# ETAPA 5.15 — Criar entry point principal

Depois de organizar o servidor, criar:

```text id="v0rx4u"
run.py
```

Objetivo:

```bash id="px8m8b"
python run.py
```

deve iniciar o painel.

O `run.py` deve ser pequeno.

Exemplo:

```python id="l6p0zi"
from Arquivos.servidor_rastreio import iniciar_servidor


if __name__ == "__main__":
    iniciar_servidor()
```

Adaptar ao pacote real usado pelo projeto.

---

# ETAPA 5.16 — Compatibilidade do script atual

Continuar permitindo:

```bash id="8h0f1o"
python Arquivos/servidor_rastreio.py
```

durante esta fase.

Não remover o comportamento anterior até ter certeza de que `run.py` funciona.

---

# ETAPA 5.17 — ABRIR_PAINEL.bat

Manter:

```text id="xkq2ms"
ABRIR_PAINEL.bat
```

Adaptar para usar o novo entry point quando for seguro.

Preferência:

```cmd id="3ls5kj"
python run.py
```

ou o Python do ambiente virtual.

O `.bat` deve continuar funcionando com duplo clique.

Não remover a compatibilidade com Windows.

---

# ETAPA 5.18 — Ambiente virtual

Garantir que a execução funcione tanto com:

```text id="9vcpw8"
venv
```

quanto com a configuração usada atualmente no projeto.

Não assumir um ambiente específico sem analisar o `.bat` atual.

---

# ETAPA 5.19 — Relatórios

Identificar como o servidor acessa:

```text id="3b7fyl"
relatorio_rastreio.html
pedidos_atrasados.html
opcoes_frete.html
```

Manter compatibilidade.

Não mudar nomes dos arquivos sem verificar dependências.

---

# ETAPA 5.20 — Arquivos gerados

Separar conceitualmente:

```text id="h5x2k8"
Código-fonte
```

de:

```text
Arquivos gerados
```

Se o projeto gerar:

```text
CSV
HTML
JSON
```

em tempo de execução, centralizar a localização desses arquivos quando possível.

Exemplo:

```text id="4maw1c"
runtime/
├── reports/
├── csv/
└── cache/
```

NÃO realizar essa mudança automaticamente se isso quebrar compatibilidade.

Nesta etapa, apenas melhorar quando seguro.

---

# ETAPA 5.21 — Testes do servidor

Criar:

```text id="3xpw2v"
tests/test_server.py
```

Testar:

- inicialização;
- configuração padrão;
- porta;
- host;
- caminho de arquivo;
- arquivo existente;
- arquivo inexistente;
- resposta 404;
- JSON;
- erro interno.

Os testes não devem realmente abrir uma janela do navegador.

Utilizar mocks.

---

# ETAPA 5.22 — Testar sem APIs externas

Os testes do servidor NÃO devem depender de:

- Tiny;
- Correios;
- internet;
- credenciais.

Mockar os serviços.

O teste do servidor deve verificar o servidor.

O teste dos serviços deve verificar os serviços.

---

# ETAPA 5.23 — Verificar integração

Depois da refatoração:

```text id="e3o7jd"
Tiny
 ↓
Correios
 ↓
Frete
 ↓
Servidor
 ↓
Painel
```

verificar se os módulos continuam funcionando individualmente.

Executar:

```bash id="c4o0in"
pytest
```

Depois:

```bash id="s6o5pk"
python -m compileall Arquivos
```

Depois:

```bash id="x3v3o6"
python run.py
```

E testar também:

```bash id="f0w4u4"
python Arquivos/servidor_rastreio.py
```

---

# ETAPA 5.24 — Não misturar lógica de negócio no servidor

Se encontrar algo como:

```python id="qonbkc"
if pedido["status"] == "...":
    ...
```

ou:

```python id="xwk5c9"
if prazo > 3:
    ...
```

verificar se essa regra pertence ao:

- Tiny;
- Correios;
- Frete;
- Service.

O servidor deve orquestrar.

Não deve concentrar regras de negócio.

---

# ETAPA 5.25 — Dependências entre módulos

A arquitetura desejada é:

```text id="f0b7u6"
             ┌─────────────┐
             │   Painel    │
             └──────┬──────┘
                    │
                    ▼
             ┌─────────────┐
             │   Server    │
             └──────┬──────┘
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
       Tiny     Correios    Frete
```

Evitar:

```text id="8x4e0r"
Tiny → Server
Correios → Server
Frete → Server
Server → Tiny
Server → Correios
Server → Frete
```

com dependências circulares.

O ideal é o servidor depender dos serviços, e não o contrário.

---

# ETAPA 5.26 — Imports

Revisar todos os imports.

Eliminar:

- imports não usados;
- duplicados;
- imports circulares.

Prestar atenção especial aos ajustes de:

```python id="jy7pyc"
sys.path
```

existentes nas etapas anteriores.

Não remover automaticamente.

Antes, verificar se são necessários para execução direta dos scripts.

---

# ETAPA 5.27 — Testes de regressão

Depois das mudanças, todos os testes das etapas anteriores devem continuar passando:

```text id="0c6zqy"
tests/test_tiny.py
tests/test_correios.py
tests/test_frete.py
tests/test_server.py
```

Nenhuma etapa anterior deve ser quebrada.

---

# ETAPA 5.28 — Revisão da estrutura

A estrutura desejada neste momento pode ser aproximadamente:

```text id="hx3y4m"
Rastreio-correios/
│
├── Arquivos/
│   │
│   ├── tiny/
│   ├── correios/
│   ├── frete/
│   │
│   ├── servidor_rastreio.py
│   ├── consulta_correios.py
│   ├── consulta_frete.py
│   └── tiny_rastreio.py
│
├── tests/
│   ├── test_tiny.py
│   ├── test_correios.py
│   ├── test_frete.py
│   └── test_server.py
│
├── web/
│   ├── index.html
│   ├── css/
│   └── js/
│
├── run.py
├── ABRIR_PAINEL.bat
├── requirements.txt
├── .env.example
└── README.md
```

Não considerar essa estrutura obrigatória.

A estrutura atual deve ser respeitada sempre que uma migração puder causar risco.

---

# ETAPA 5.29 — Documentação

Atualizar o README para refletir corretamente a nova forma de executar:

```bash
python run.py
```

e:

```text
ABRIR_PAINEL.bat
```

Explicar que o servidor inicia o painel local.

Não mencionar funcionalidades que não estejam realmente implementadas.

---

# ETAPA 5.30 — Arquitetura documentada

Criar ou atualizar:

```text id="8m6aqm"
docs/architecture.md
```

Adicionar:

## Visão geral

## Fluxo de execução

```text
Usuário
 ↓
Painel Web
 ↓
Servidor
 ↓
Services
 ↓
Tiny / Correios / Frete
```

## Responsabilidades

Explicar:

- Tiny;
- Correios;
- Frete;
- Server;
- Frontend.

## Fluxo de dados

Explicar como um pedido passa pelo sistema.

---

# ETAPA 5.31 — Verificação de segurança

Garantir que:

- tokens não apareçam no frontend;
- tokens não apareçam em JSON;
- credenciais não sejam impressas;
- `.env` continue ignorado;
- arquivos sensíveis não sejam servidos pelo servidor.

IMPORTANTE:

O servidor NÃO deve permitir acesso HTTP arbitrário a qualquer arquivo do computador.

Evitar vulnerabilidade de path traversal.

Exemplo perigoso:

```text
../../.env
```

Garantir que somente arquivos dentro do diretório permitido possam ser servidos.

---

# ETAPA 5.32 — Segurança de arquivos

Se o servidor utiliza caminhos vindos da URL, validar:

- `..`;
- caminhos absolutos;
- barras invertidas;
- caminhos fora do diretório permitido.

Não permitir que o usuário do navegador consiga solicitar:

```text
.env
```

ou:

```text
Arquivos/.env
```

ou qualquer arquivo fora da área pública.

---

# ETAPA 5.33 — Não adicionar framework sem necessidade

Não instalar:

```text
Flask
FastAPI
Django
```

apenas por estética.

Primeiro melhorar o servidor existente.

Um framework poderá ser considerado futuramente caso o projeto realmente precise de:

- API pública;
- autenticação;
- banco;
- deploy;
- múltiplas rotas;
- frontend separado.

---

# CRITÉRIO DE SUCESSO

A Etapa 5 estará concluída quando:

- servidor estiver mais organizado;
- configuração estiver centralizada;
- caminhos estiverem seguros;
- frontend estiver progressivamente separado;
- HTML/CSS/JS não estiverem misturados desnecessariamente com Python;
- servidor não contenha regras de negócio;
- `run.py` existir;
- `ABRIR_PAINEL.bat` continuar funcionando;
- testes do servidor existirem;
- testes anteriores continuarem passando;
- nenhum segredo estiver exposto;
- arquivos fora da área pública não puderem ser acessados pelo servidor.

---

# O QUE NÃO FAZER

Nesta etapa NÃO:

- criar banco de dados;
- criar autenticação;
- criar Docker;
- criar microserviços;
- criar Kubernetes;
- publicar na internet;
- reescrever frontend;
- mudar totalmente o layout;
- trocar a API dos Correios;
- mudar Tiny;
- mudar regras de negócio.

---

# RESULTADO ESPERADO

O projeto deverá caminhar para uma arquitetura:

```text id="t0go2j"
                  ┌───────────────────┐
                  │    Web / Painel   │
                  └─────────┬─────────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │      Server       │
                  └─────────┬─────────┘
                            │
                     ┌──────┼──────┐
                     ▼      ▼      ▼
                   Tiny  Correios  Frete
                     │      │      │
                     └──────┼──────┘
                            ▼
                     Dados processados
```

---

# RELATÓRIO FINAL

Ao concluir, apresentar:

## 1. Arquivos criados

## 2. Arquivos modificados

## 3. Arquivos removidos

## 4. Arquitetura antes

Explicar resumidamente como funcionava.

## 5. Arquitetura depois

Explicar como ficou.

## 6. Testes

Informar:

- total;
- aprovados;
- falhos;
- não executados.

## 7. Segurança

Informar as proteções adicionadas.

## 8. Compatibilidade

Confirmar:

```bash
python run.py
```

e:

```bash
python Arquivos/servidor_rastreio.py
```

e:

```text
ABRIR_PAINEL.bat
```

## 9. Problemas encontrados

Listar problemas que não puderam ser corrigidos com segurança.

## 10. Próxima etapa

Somente sugerir.

NÃO implementar automaticamente a Etapa 6.

---

# REGRA FINAL

Esta etapa deve melhorar a estrutura sem transformar o projeto em algo irreconhecível.

Sempre prefira:

```text
código simples
+
responsabilidade clara
+
baixo acoplamento
+
testes
```

em vez de:

```text
arquitetura complexa
+
muitas dependências
+
muitas abstrações
```

O projeto já possui Tiny, Correios e Frete modularizados.

Agora o objetivo é conectá-los de maneira organizada através do servidor e do painel.