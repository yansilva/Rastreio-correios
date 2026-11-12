# Aba "Entregues" — Plano de Implementação

> **Para quem executa:** cada tarefa vai para a sessão fixa do especialista indicado (`.equipe/sessoes.md`). Use TDD e marque os passos com `- [ ]`. Ninguém faz commit: o coordenador junta tudo e pede o aval do usuário.

**Objetivo:** guardar localmente os pedidos entregues e mostrá-los numa aba "Entregues" (semana atual e anterior). No painel principal, o entregue só aparece no dia da entrega.

**Arquitetura:** `processar()` alimenta um histórico em JSON (`historico_entregas.py`), que também faz uma última consulta aos Correios para os rastreios que saíram do Tiny. Uma função própria (`pagina_entregues.py`) gera `entregues_semana.html` a partir desse histórico.

**Stack:** Python 3.12, pytest, ruff. HTML por template, CSS e JS em `web/`.

**Spec:** `docs/superpowers/specs/2026-11-12-aba-entregues-design.md`

## Restrições globais

- Não chame as APIs do Tiny nem dos Correios nos testes. Use mock. Para regenerar as páginas: `consulta_correios.processar(usar_cache=True)`.
- `Arquivos/entregas_historico.json` fica fora do git, porque contém nomes de clientes.
- Gravação atômica (`.tmp` + `os.replace`), igual a `correios/cache.py`.
- Semana = semana ISO (`isocalendar()`), de segunda a domingo. Guardar só a semana atual e a anterior.
- Dias = `(entregue_em - postado_em)`, em dias corridos, com uma casa decimal. Sem `postado_em`, mostrar "—" e deixar o pedido fora da média.
- Visual: tokens do `DESIGN.md`, nada de verde para "rápido", alvos de 44px no celular, contraste mínimo de 4,5:1.
- Edite com a ferramenta Edit. Nunca use o Set-Content do PowerShell.
- Servidor: páginas `.html` da raiz já são servidas (`security.py:146`). Não precisa mudar nada; basta o teste de 200.

## Pontos de atenção na revisão

1. **Entrega registrada duas vezes:** um rastreio já registrado aparece de novo como entregue numa consulta seguinte e não pode duplicar nem mudar `registrado_em`.
2. **Virada de ano:** uma entrega em 29/12 conta como "semana anterior" quando hoje é 02/01, se as duas datas caem em semanas ISO vizinhas.
3. **Arquivo corrompido ou vazio:** o relatório continua e o histórico recomeça vazio, com aviso no log, sem quebrar.
4. **Falha de rede na última consulta:** o relatório sai do mesmo jeito, e o rastreio sai de `acompanhados`, sem nova tentativa infinita.
5. **Regeração pelo cache** (`usar_cache=True`): nenhuma chamada de rede. `acompanhados` não muda.

---

### Tarefa 1 (backend): módulo de histórico

**Arquivos:**
- Criar: `Arquivos/correios/historico_entregas.py`
- Teste: `tests/test_historico_entregas.py`
- Alterar: `.gitignore` (acrescentar `Arquivos/entregas_historico.json`)

**Interfaces que esta tarefa produz** (usadas nas tarefas 2 e 3):
- `ARQUIVO = "entregas_historico.json"`
- `carregar(caminho: str) -> dict`: devolve `{"versao": 1, "acompanhados": {}, "entregas": {}}` quando o arquivo não existe ou está inválido.
- `salvar(caminho: str, dados: dict) -> None`
- `registrar_entrega(dados: dict, objeto: ObjetoRastreio, pedido: str, cliente: str, agora: datetime) -> bool`: devolve True só quando registra uma entrega nova.
- `podar(dados: dict, agora: datetime) -> None`
- `entregas_da_semana(dados: dict, agora: datetime, deslocamento: int = 0) -> list[dict]`: ordem decrescente de `entregue_em`.
- `resumo(lista: list[dict]) -> dict`: devolve `{"total": int, "media_dias": float | None, "mais_demorado": dict | None}`.
- `dias_ate_entrega(item: dict) -> float | None`
- Cada item tem exatamente as chaves `pedido`, `cliente`, `rastreio`, `cidade`, `postado_em`, `entregue_em` e `registrado_em`. As datas são strings ISO; `postado_em` pode ser `None`.
- `cidade`: `evento.local` do primeiro evento cuja descrição tenha "ENTREGUE". Se não houver, usa `objeto.ultimo_local`.

- [ ] Escrever os testes que falham:
  - `test_registra_entregue_uma_vez`: a segunda chamada devolve False e mantém o `registrado_em`.
  - `test_ignora_nao_entregue`
  - `test_carregar_arquivo_ausente_ou_corrompido`: conteúdo `"{x"` devolve a estrutura vazia.
  - `test_salvar_e_carregar_ida_e_volta`: sem deixar `.tmp` para trás.
  - `test_podar_mantem_semana_atual_e_anterior`: com agora = 2026-11-12, mantém 2026-11-10 e 2026-11-04 e remove 2026-10-28.
  - `test_semana_anterior_na_virada_de_ano`: com agora = 2027-01-04 e entrega em 2026-12-29, o resultado aparece em `deslocamento=-1`.
  - `test_resumo_media_e_mais_demorado`: entregas de 2,0 e 5,5 dias dão média 3,8 e mais demorado com 5,5.
  - `test_resumo_sem_postagem_fica_fora_da_media`
  - `test_resumo_lista_vazia`: `{"total": 0, "media_dias": None, "mais_demorado": None}`
- [ ] `python -m pytest tests/test_historico_entregas.py -q`: os testes falham.
- [ ] Implementar no módulo.
- [ ] Rodar de novo: tudo passa. Depois `python -m pytest -q` e `python -m ruff check Arquivos tests`.

### Tarefa 2 (backend): integração em `processar()` e regra do painel

**Arquivos:**
- Alterar: `Arquivos/consulta_correios.py`, só o corpo de `processar()`, onde os objetos são classificados e o cache é salvo (perto das linhas 300–445).
- Alterar: `Arquivos/correios/tracking.py`, em `deve_ocultar_card`, no bloco de entregue.
- Testes: `tests/test_regerar.py` e `tests/test_correios.py`

**Interfaces:**
- Consome: Tarefa 1, e `consultar_objeto(objeto, token)` e `obter_token()`, que já existem em `consulta_correios.py`.
- Produz: depois de `processar()`, o arquivo `Arquivos/entregas_historico.json` atualizado. Também produz a chamada `gerar_pagina_entregues(historico, agora)` da Tarefa 3, que grava `entregues_semana.html` na mesma pasta dos outros relatórios.

- [ ] Escrever os testes que falham:
  - `test_entregue_hoje_aparece_no_painel` e `test_entregue_ontem_fica_oculto`, em `deve_ocultar_card` com `data_referencia`.
  - `test_processar_registra_entregue_no_historico`, usando cache e um pedido entregue.
  - `test_rastreio_que_saiu_do_tiny_recebe_uma_consulta`: o histórico começa com `acompanhados = {"AE111BR": ...}` e o CSV vem sem ele. Com `consultar_objeto` mockado devolvendo um evento de entrega, o rastreio entra em `entregas` e sai de `acompanhados`. O mock é chamado uma vez.
  - `test_regerar_pelo_cache_nao_faz_ultima_consulta`: com `usar_cache=True`, o `consultar_objeto` mockado com `side_effect=AssertionError` nunca é chamado.
  - `test_falha_na_ultima_consulta_nao_derruba_relatorio`: o mock levanta `requests.RequestException`, o relatório sai e o rastreio sai de `acompanhados`.
- [ ] Rodar os testes: falham.
- [ ] Implementar:
  - Regra do painel: entregue só fica visível quando `data_entrega_dt.date() == agora.date()`. Atualize a docstring.
  - Integração conforme a seção 1.3 da spec: registrar, fazer a última consulta só em consulta real, atualizar `acompanhados`, `podar`, `salvar` e chamar `gerar_pagina_entregues`.
  - Enquanto a Tarefa 3 não estiver pronta, importe com uma proteção: se faltar `pagina_entregues`, não gera a página.
- [ ] Rodar a suíte completa e o ruff: tudo passa.

### Tarefa 3 (frontend): página `entregues_semana.html` e a aba no menu

**Arquivos:**
- Criar: `Arquivos/correios/pagina_entregues.py`
- Teste: `tests/test_pagina_entregues.py`
- Alterar: menu em `Arquivos/consulta_correios.py` (só as linhas do `<nav>`, perto das 225 e 650), em `Arquivos/frete/report.py` e em `Arquivos/demo_data.py` (perto das 373 e 478).
- Alterar: `web/css/components.css` (bloco novo no fim, com o comentário `/* Página Entregues */`) e `DESIGN.md`.

**Interfaces:**
- Consome: as funções `entregas_da_semana`, `resumo` e `dias_ate_entrega` da Tarefa 1. Nos testes, monte o `dict` do histórico à mão.
- Produz: `gerar_pagina_entregues(historico: dict, agora: datetime, destino: str) -> str`, que grava o arquivo e devolve o caminho. Também produz `montar_html_entregues(historico: dict, agora: datetime) -> str`, sem I/O.

Escopo visual (spec, seção 2):
- seletor "Esta semana (dd/mm–dd/mm)" e "Semana anterior", com `aria-pressed`;
- resumo com total, média e o pedido mais demorado;
- tabela no desktop e cartões a partir de 640px;
- "Copiar rastreio" usando o `.btn-copy[data-copy]` existente;
- dias acima de 7 no tom de aviso;
- estado vazio "Nenhuma entrega nesta semana", sem zeros.

- [ ] Escrever os testes que falham:
  - `test_pagina_tem_duas_semanas_e_seletor`
  - `test_semana_vazia_sem_zeros`: o HTML da semana vazia não contém `>0<` no resumo e contém "Nenhuma entrega nesta semana".
  - `test_ordem_mais_recente_primeiro`
  - `test_dias_sem_postagem_mostra_traco`
  - `test_aba_entregues_no_menu_das_quatro_paginas`: painel, atrasados, frete e a própria página. A página ativa leva `aria-current="page"`.
  - `test_servidor_serve_entregues_semana`: responde 200, no mesmo padrão de `tests/test_server.py`.
- [ ] Rodar os testes: falham.
- [ ] Implementar seguindo o padrão das outras páginas: `icon_sprite`, `versao_cache`, skip link e `<main id="conteudo">`.
- [ ] Rodar a suíte e o ruff. Regenerar pelo cache e conferir no navegador em 375px e 1280px, nos dois temas, sem overflow horizontal.

### Tarefa 4: validação (qa, acessibilidade, revisao-codigo)

Começa depois das tarefas 1 a 3, com o servidor reiniciado pelo coordenador.

- [ ] **qa:**
  - Critérios da spec e os cinco pontos de atenção.
  - Contagem e ordem da lista.
  - Seletor de semana.
  - Painel mostrando só os entregues de hoje.
  - Regeração sem rede.
- [ ] **acessibilidade:**
  - Seletor com `aria-pressed`.
  - Tabela com `th scope`.
  - Cartões no celular.
  - Foco, contraste e alvos.
- [ ] **revisao-codigo:**
  - Diff completo.
  - Gravação atômica.
  - Tratamento de erros da última consulta.
  - Duplicação entre os templates de menu.
