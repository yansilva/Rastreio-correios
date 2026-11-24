# Brief de implementação: direção "Mesa Limpa"

Autor: designer · 2026-11-24 · Fonte da verdade: `DESIGN.md` (seções marcadas como Mesa Limpa). Este brief diz **onde** e **como medir**; os valores estão no DESIGN.md.

Regras do projeto que continuam: não chamar `/atualizar`; regenerar pelo cache com `docker compose exec painel python -c "import sys; sys.path.insert(0,'Arquivos'); import consulta_correios; consulta_correios.processar(usar_cache=True)"`; só o coordenador reinicia o container; nada de commit sem aval. Não reabrir: escala única de urgência (3–4 Atenção, 5–6 Alto, 7+ Crítico), Entregues em âmbar acima de 7 dias, cartão de Entregues de ~199px no celular, FAB pode cobrir conteúdo na rolagem, ferramentas abaixo das abas entre 641 e 1099px, painel sem senha, botão de consulta no cabeçalho no desktop.

## Linha de base (medida em 24/11, dados das 08:11, antes da mudança)

Meça de novo antes de começar, com os mesmos dados, e use esses números como teto.

| Página | Largura | Medida | Hoje |
|---|---|---|---|
| Painel | 375 | topo do primeiro `.order-card` (faixa calma) | 362 |
| Painel | 1440 | topo do primeiro `.order-card` | 566 |
| Painel | 1024 | topo da `.orders-table` (visão Tabela) | 610 |
| Entregues | 375 | topo da primeira linha | 329 |
| Frete | 375 | topo do primeiro `.pedido-card` | 469 (meta: ≤ 420) |

## Lotes

Os lotes não compartilham arquivo. A e B são do mesmo executor, em sequência (B usa os tokens de A). C e D podem correr em paralelo com A/B.

### Lote A · Base (tokens, fonte, cabeçalho e abas) — `web/css/main.css`
1. `:root` e `[data-theme="dark"]`: novos valores de `--color-primary`, `--color-primary-hover`, `--color-primary-light`, `--color-link`, `--color-bg`, `--color-surface`, `--color-surface-hover`, `--color-header-bg`, `--color-border`, `--color-border-strong` (passa a ser definida também no escuro: #6b7585), `--color-text-main`, `--color-text-muted`, `--color-text-subtle`. Status sem mudança.
2. Tokens novos: `--font-sans`, `--font-display`, `--font-mono`, `--radius-sm: 6px`, `--radius-md: 8px`, `--radius-lg: 10px` (mantém `--radius-full`), `--shadow-sm: none`, `--shadow-md` (claro e escuro, ver DESIGN.md), `--motion: 120ms ease-out`. Troque `--transition: all .2s` por `--transition: color var(--motion), background-color var(--motion), border-color var(--motion), box-shadow var(--motion)`.
3. Remover o `@font-face` da Inter; `body { font-family: var(--font-sans); font-size: 0.875rem; line-height: 1.5; }`; remover `transition` de `body`.
4. `h1`: `--font-display`, 1.5rem, peso 600, cor `--color-text-main` (tirar o azul e a regra `[data-theme="dark"] h1`). `.meta`: 0.8125rem, Tinta Discreta.
5. `header`: alinhado à esquerda a partir de 641px (hoje é centralizado). A partir de 1100px, linha 1 = título + meta; linha 2 = `.nav-tabs` à esquerda e `.header-tools` à direita; `border-bottom: 1px solid var(--color-border)`; 20px até o conteúdo. Entre 641 e 1099px, ferramentas abaixo das abas (como hoje).
6. `.nav-tab`: sem borda, sem fundo, sem raio; 40px; 0×12px; 0.8125rem peso 500; ativo com `box-shadow: inset 0 -2px 0 var(--color-primary)`, peso 600, cor Tinta (apagar `.nav-tab.active::after` e o fundo do ativo). Hover: Tinta + Superfície 2. Celular: 44px, sticky, borda inferior.
7. `.back-link`: raio 8px, sem sombra, sem `translateY`.
8. `@media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition: none !important; animation: none !important; } }` no fim do arquivo.

### Lote B · Componentes do painel, Atrasados e Entregues — `web/css/components.css`
Seletores (todos com os tokens do lote A; nenhum hex novo):
- `.dash-card` (13–80, 1880–1890), `.dash-number`, `.dash-label` (168), `.dash-icon`: raio `--radius-lg`, 14×16px, sem sombra, sem `translateY` no hover (borda forte + `--shadow-md`), número 1.5rem peso 600 `tabular-nums` cor Tinta, rótulo 0.8125rem sem caixa-alta. Celular: número 1.25rem, rótulo 0.75rem, `justify-content: flex-start`.
- `.summary-card`, `.summary-number`, `.summary-label` (816–840, 1863, 2030–2041): igual ao `.dash-card`. No celular, `.summary-card` com 8×4px; `.summary-label` com `overflow-wrap: normal`.
- `.action-strip` (86), `.action-chip` (106–170), regra do celular (~1503): raio 10px no contêiner e 6px nos chips; `padding: 8px 12px` (resolve o `cramped-padding` do detector); borda `--color-border`; título sem caixa-alta.
- `.search-input` (213–240): 40px, raio 8px, borda forte; celular igual a hoje (recolhida, 44px, 16px).
- `.filter-pill`, `.pill-count` (280–310, 1689, 1720, 1745): raio 6px, 32px (44px no celular), borda forte, 13px peso 500; ativo azul; zerado tracejado.
- Visão segmentada e `.options-menu` (1139–1150, 1709): contêiner raio 8px, segmento 6px; menu raio 10px.
- `.btn-action` (620–660), `.btn-theme` (667–700), `.btn-copy`, `.btn-ver-cartao`: raio 8px, 36px, sem sombra e sem `translateY`/`scale`; FAB do celular continua (círculo, `--shadow-lg`).
- `.order-card` (359–380), `.order-header` (377), `.order-closed` (1317–1330): raio 10px, sem sombra em repouso, cabeçalho em Superfície com borda inferior; título 1rem peso 600; rastreio em `--font-mono` 0.8125rem.
- Timeline `.event` (488–530), `.order-history` (459–480): bolinha de 10px; evento crítico sem fundo tingido.
- `.badge` (538–580), `.badge-*`, `.dias-badge` (891–901): raio 6px, 0.75rem peso 600, sem `text-transform`/`letter-spacing`, `::before` com ponto de 6px em `currentColor`.
- `.table-wrapper` (845), `.orders-table`, `th`: cabeçalho 0.75rem peso 600 sem caixa-alta, fundo Superfície 2; linha 44px; Cliente com `-webkit-line-clamp: 2` (`.orders-table td[data-label="Cliente"]`, 1779).
- `.empty-state` (903–915, 1415): grade `36px 1fr`, alinhada à esquerda, borda e raio 10px; `.empty-state .emoji` vira o círculo de 36px (fundo `--color-success-bg`, ícone 18px `--color-success-text`). Sem mudar marcação.
- Entregues: `.entregues-seletor` (intervalo com `white-space: nowrap`), larguras de coluna (2344–2350) sem mudança.
- Trocar todo `transition: var(--transition)`/`all` que sobrar e todo `transform` de hover.

### Lote C · Frete — `Arquivos/frete/report.py` (CSS embutido e HTML)
1. Repetir no `:root` e no escuro do relatório os mesmos tokens do lote A (cores, fontes, raios, sombras, `--motion`); remover o `@font-face` da Inter (atualizar `tests/test_frete.py:899`, que procura o `src` da Inter).
2. `.nav-tab`, `.btn-theme`, `.btn-limpar` (421–500): mesmas regras do lote A; manter o tema só com ícone no celular (spans sr-only).
3. `.summary`, `.summary-card`, `.summary-number`, `.summary-label`, `.summary-link` (604–627, 798–801): como o resumo do painel; tirar `animation`/`animation-delay` (`fadeIn`).
4. **P2 da 15ª — resumo alto no celular:** até 640px, rótulos curtos e uma linha cada: "Pedidos", "Menor frete", "Prazo > 3 dias". Os números dos pedidos (`#sumMenorPedido`) ficam ocultos na tela até 640px (`display: none` só no celular; no desktop seguem visíveis). Gere os rótulos curto e longo no HTML (`<span class="rotulo-longo">` / `<span class="rotulo-curto">`, padrão de `.meta-longo`/`.meta-curto`) em vez de trocar texto por JS. Meta: cartões do resumo com no máximo 2 linhas de rótulo e primeiro pedido em y ≤ 420 em 375px.
5. `.pedido-card`, `.pedido-header`, `.servico-card`, `.servicos-grid`, `.servicos-indisponiveis`, `.prazos-aviso` (630–737): raio 10px no pedido e 8px no serviço, sem sombra em repouso; preço 1rem peso 600 `tabular-nums`; CEP em mono.
6. `.empty-state` (756–769): igual ao painel.
7. Regenerar só por `FreteReportGenerator` com dados fictícios numa pasta temporária (como na 14ª), nunca por consulta real.

### Lote D · Geradores de HTML e JS — `Arquivos/correios/pagina_entregues.py`, `web/js/dashboard.js`
1. **P2 da 15ª — Entregues estoura a largura no celular:** em `pagina_entregues.py:66`, trocar `f"Mais demorado&nbsp;·&nbsp;{dias}&nbsp;dias"` por `f"Mais demorado · {dias}&nbsp;dias"` (só número e "dias" juntos). Hoje o bloco inquebrável mede 120px numa coluna de 96px: a página fica com 378px em 375 e 368px em 360. Atualizar `TestMaisDemoradoSemQuebra` em `tests/test_pagina_entregues.py` para o contrato novo ("10,0&nbsp;dias" junto; quebra permitida depois de "Mais demorado").
2. `pagina_entregues.py:154`: o intervalo do seletor sem quebra: `Esta semana <span class="intervalo">(dd/mm–dd/mm)</span>` (o CSS do lote B dá `nowrap` em `.intervalo`).
3. `web/js/dashboard.js:252`: a célula Cliente da Tabela recebe `title` com o nome completo (o corte de 2 linhas é do lote B).

## Critérios de aceite (por aba)

Medir com a página recarregada, `innerWidth` conferido, nos dois temas (`localStorage.theme` = `light` e `dark`), e restaurar o `localStorage` no fim.

**Todas as abas**
1. **AA:** todo texto ≥ 4,5:1 sobre o fundo real (compor o alfa dos selos sobre a superfície); contorno de campo, filtro, botão secundário e segmento ≥ 3:1 contra o fundo vizinho. Valores esperados estão no DESIGN.md (menor texto: 4,97:1 no claro, 5,32:1 no escuro).
2. **Sem estouro:** `document.documentElement.scrollWidth === clientWidth` em 360 e 375px, nos dois temas; em Entregues, nas duas semanas; no Painel, nas visões Cartões e Compacta, com a busca fechada e aberta.
3. **Abas:** cada `.nav-tab` com altura ≥ 44px até 640px e ≥ 40px no desktop; aba atual com sublinhado de 2px visível nos dois temas; foco por teclado visível.
4. **Fonte:** nenhuma requisição a `InterVariable.woff2` na aba Rede; `getComputedStyle(document.body).fontFamily` começa por "Segoe UI Variable Text"; códigos de rastreio com a fonte mono.
5. **Movimento:** com `prefers-reduced-motion: reduce` emulado, `transition-duration` e `animation-duration` computados são `0s` em `.dash-card`, `.order-card`, `.filter-pill`, `.nav-tab` e `.btn-action`; sem emulação, nenhuma transição passa de 120ms e nenhum elemento muda `transform` no hover.
6. **Detector:** `impeccable detect --json` nos 4 HTMLs + `web/` sem achado novo além dos falsos positivos registrados (Inter some do relatório quando o `@font-face` sair).
7. `pytest -q` e `ruff check .` passando.

**Painel**
- Primeiro `.order-card` em 375px: ≤ 362 com a faixa calma (mesmos dados). Em 1440: ≤ 566. Tabela em 1024: ≤ 610.
- Busca recolhida no celular: botão de 44×44 até receber foco; ao abrir, ocupa a linha (como hoje).
- Números do resumo no mesmo topo em 360 e 375px (diferença 0).
- Selos com ponto e texto, sem caixa-alta; "Atrasado · N dias · Nível" intacto.
- Tabela: nenhuma linha acima de 66px com nomes longos (Cliente em 2 linhas no máximo).

**Atrasados**
- Estado vazio alinhado à esquerda, com ícone no círculo e "Ver o painel" como link; tabela com os mesmos critérios do Painel quando houver atrasados (testar com a demo).

**Entregues**
- Sem estouro em 360 e 375 nas duas semanas, com "Mais demorado · 10,0 dias".
- Primeira linha em 375px: ≤ 329. Cartões de entrega entre 198 e 228px (como hoje).
- Intervalo "(dd/mm–dd/mm)" numa linha só.

**Frete**
- Primeiro pedido em 375px: ≤ 420 (hoje 469). Rótulos do resumo em no máximo 2 linhas no celular.
- Tema só com ícone no celular, nos dois temas, antes e depois do script do tema rodar.
- Sem `fadeIn` nos cartões.

## Validação sugerida
- qa: critérios 2, 3, 5 e os números de posição; regressão funcional (filtros, busca, cópia, visões, troca de semana).
- acessibilidade: critério 1 (contraste com composição de alfa), foco, nome acessível dos botões que viram ícone.
- revisao-codigo: nenhum hex novo fora dos tokens, nenhum `transition: all`, tokens do frete iguais aos do `main.css`.
