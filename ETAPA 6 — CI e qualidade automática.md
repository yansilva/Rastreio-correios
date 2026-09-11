# ETAPA 6 — CI E QUALIDADE AUTOMÁTICA

## Objetivo

Transformar o projeto `Rastreio-correios` em um projeto com validação automática no GitHub.

A partir desta etapa, cada `push` e `pull request` para a branch principal deverá executar automaticamente:

- instalação das dependências;
- verificação de sintaxe;
- suíte completa de testes;
- análise estática/lint;
- validações básicas de qualidade.

O objetivo é detectar erros antes que uma alteração seja considerada pronta.

IMPORTANTE:

- Não alterar a lógica de negócio das integrações Tiny, Correios ou Frete.
- Não fazer nova grande refatoração arquitetural.
- Não criar deploy.
- Não fazer chamadas reais às APIs durante o CI.
- Os testes continuam sendo isolados e mockados.
- Preservar o funcionamento atual do projeto.

---

# 1. ANALISAR O PROJETO ANTES DE ALTERAR

Antes de modificar qualquer arquivo:

1. verificar a estrutura atual;
2. verificar `requirements.txt`;
3. verificar todos os testes existentes;
4. verificar a versão de Python indicada no README;
5. verificar se já existe `.github/`;
6. verificar se já existe alguma configuração de lint, pytest ou CI;
7. verificar se existe `pyproject.toml`.

Não duplicar configurações que já existam.

---

# 2. CRIAR GITHUB ACTIONS

Criar:

```text
.github/
└── workflows/
    └── ci.yml
```

O workflow deve executar em:

```yaml
on:
  push:
    branches:
      - main

  pull_request:
    branches:
      - main
```

Usar Python:

- 3.11
- 3.12

O projeto já documenta essas versões como referência principal.

Criar uma estratégia de matrix para testar ambas:

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12"]
```

---

# 3. FLUXO DO CI

O workflow deverá realizar aproximadamente:

```text
Checkout
↓
Configurar Python
↓
Atualizar pip
↓
Instalar dependências
↓
Executar validação de sintaxe
↓
Executar lint
↓
Executar testes
↓
Gerar cobertura
```

O workflow deve falhar quando uma dessas etapas falhar.

---

# 4. INSTALAÇÃO DE DEPENDÊNCIAS

Manter as dependências de produção separadas das ferramentas de desenvolvimento quando isso fizer sentido.

Avaliar a criação de:

```text
requirements.txt
requirements-dev.txt
```

### requirements.txt

Deve conter somente dependências necessárias para executar o sistema.

Exemplo atual:

```text
requests
python-dotenv
```

### requirements-dev.txt

Pode conter ferramentas utilizadas durante desenvolvimento e CI:

```text
pytest
pytest-cov
ruff
```

Evitar adicionar bibliotecas sem necessidade.

Se houver uma razão técnica para manter `pytest` no `requirements.txt`, preservar a estrutura atual.

---

# 5. CONFIGURAÇÃO DE LINT

Adicionar Ruff como ferramenta de análise estática.

Criar:

```text
pyproject.toml
```

Centralizar nele as configurações do projeto relacionadas ao Ruff e, quando apropriado, ao pytest.

Configurar o Ruff para:

- verificar código Python;
- detectar imports incorretos;
- detectar variáveis ou código suspeito;
- detectar problemas comuns de estilo;
- trabalhar com Python 3.11+.

Não tentar corrigir automaticamente centenas de problemas apenas para "zerar" o lint.

Primeiro analisar os problemas reais existentes.

Caso existam problemas simples e seguros de corrigir, corrigir.

Caso o código legado exija alguma exceção de regra, documentar/configurar a exceção de forma consciente.

Não usar configurações que simplesmente desativem a maior parte das regras.

---

# 6. VALIDAÇÃO DE SINTAXE

Adicionar uma etapa explícita para verificar se todos os arquivos Python compilam corretamente.

Usar uma abordagem equivalente a:

```bash
python -m compileall .
```

ou uma alternativa equivalente e segura.

A validação não deve executar as integrações reais.

---

# 7. TESTES

O CI deve executar:

```bash
python -m pytest tests/ -v
```

Os testes devem continuar independentes de:

- Tiny ERP real;
- API real dos Correios;
- serviço real de cálculo de frete;
- credenciais;
- arquivo `.env`.

Não adicionar credenciais reais ao workflow.

Não criar secrets apenas para executar testes unitários.

---

# 8. COBERTURA DE TESTES

Adicionar `pytest-cov`.

Executar algo equivalente a:

```bash
python -m pytest tests/ --cov=Arquivos --cov-report=term-missing
```

O objetivo inicial é medir a cobertura.

IMPORTANTE:

Não exigir arbitrariamente uma porcentagem mínima neste momento.

Primeiro obter a cobertura real atual.

Não adicionar:

```text
--cov-fail-under=80
```

ou outro limite artificial sem analisar o resultado.

A meta desta etapa é criar visibilidade sobre a cobertura, não maquiar o número.

---

# 9. README

Atualizar o README para refletir corretamente a nova estrutura.

Adicionar um badge real do GitHub Actions, apontando para o workflow:

```text
CI
```

O badge deve ficar próximo dos badges existentes.

Substituir informações estáticas que possam ficar desatualizadas.

Por exemplo, em vez de depender somente de:

```text
tests-136 passed
```

deixar claro que os testes são executados automaticamente pelo GitHub Actions.

Não inventar números novos.

---

# 10. CORRIGIR A DOCUMENTAÇÃO DO PYTHON

No README existe uma inconsistência:

A documentação apresenta Python 3.11 / 3.12 como versões utilizadas, mas em pré-requisitos aparece:

```text
Python 3.8 ou superior
```

Corrigir para refletir as versões efetivamente suportadas pelo projeto.

Usar:

```text
Python 3.11 ou superior
```

somente se a análise do código confirmar essa compatibilidade.

Caso contrário, documentar exatamente as versões suportadas.

Não declarar compatibilidade com versões que não foram testadas.

---

# 11. PYPROJECT.TOML

Criar uma configuração simples e profissional.

Exemplo conceitual:

```toml
[tool.ruff]
target-version = "py311"
line-length = 100

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Ajustar conforme a estrutura real do projeto.

Não copiar cegamente este exemplo.

---

# 12. GITIGNORE

Verificar se arquivos gerados pelo CI ou ferramentas locais estão corretamente ignorados.

Exemplos:

```text
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/
```

Adicionar somente o que fizer sentido.

Não ignorar arquivos que façam parte do código-fonte.

---

# 13. QUALIDADE DO WORKFLOW

O arquivo `.github/workflows/ci.yml` deve ser:

- simples;
- legível;
- fácil de entender para alguém avaliando o portfólio;
- sem scripts extremamente complexos;
- sem dependências externas desnecessárias.

Adicionar nomes claros às etapas.

Exemplo:

```text
Checkout
Setup Python
Install dependencies
Compile Python files
Run Ruff
Run tests
Generate coverage
```

---

# 14. SEGURANÇA

Garantir que o CI:

- nunca leia credenciais reais;
- nunca exija `.env`;
- nunca faça chamadas reais para Tiny;
- nunca faça chamadas reais para Correios;
- nunca envie dados para serviços externos desnecessários.

Os testes devem continuar usando mocks.

---

# 15. TESTES DO PRÓPRIO CI

Depois de criar os arquivos:

1. executar localmente os mesmos comandos usados pelo workflow;
2. corrigir qualquer falha encontrada;
3. verificar se todos os testes passam;
4. verificar se o Ruff passa;
5. verificar se `compileall` passa;
6. fazer commit.

Usar um commit semelhante a:

```text
ci: adicionar pipeline de qualidade automatizada
```

---

# 16. CRITÉRIOS DE CONCLUSÃO

A Etapa 6 só deve ser considerada concluída quando:

- [ ] `.github/workflows/ci.yml` criado;
- [ ] CI executando em `push`;
- [ ] CI executando em `pull_request`;
- [ ] Python 3.11 validado;
- [ ] Python 3.12 validado;
- [ ] dependências instaladas automaticamente;
- [ ] `compileall` executado;
- [ ] Ruff configurado;
- [ ] testes executados automaticamente;
- [ ] cobertura exibida;
- [ ] README atualizado;
- [ ] inconsistência da versão Python corrigida;
- [ ] `.gitignore` atualizado quando necessário;
- [ ] nenhum segredo adicionado ao repositório;
- [ ] nenhum acesso real às APIs durante os testes;
- [ ] comportamento atual da aplicação preservado.

---

# REGRA PRINCIPAL

Esta etapa não é para criar novas funcionalidades.

A finalidade é fazer o projeto responder automaticamente:

> "Essa alteração que acabei de enviar ainda está saudável?"

O GitHub deve conseguir responder isso por meio dos testes e das verificações automáticas.

Não avançar para uma nova grande refatoração depois de concluir esta etapa.