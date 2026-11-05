---
target: critique mobile
total_score: 23
max_score: 36
na_heuristics: 9
p0_count: 0
p1_count: 3
target_identity: "file:C:\\Users\\yansa\\Yan\\Rastreio-correios\\relatorio_rastreio.html"
target_fingerprint: "sha256:a336b1af80c809b7007ff138c3d3b9dfbb7685d5abb38e567b78049dc99976db"
target_path: "C:\\Users\\yansa\\Yan\\Rastreio-correios\\relatorio_rastreio.html"
timestamp: 2026-11-05T14-07-03Z
slug: relatorio-rastreio-html
---
Method: ⚠️ DEGRADED: single-context (sub-agents not spawned for this run; detector and browser evidence collected inline)

Escopo: só uso no celular. Larguras 360, 375, 390 e 412px; tema claro e escuro; páginas relatorio_rastreio.html, opcoes_frete.html e pedidos_atrasados.html.

## Design Health Score (mobile)

| # | Heuristic | Score | Key Issue |
|---|---|---|---|
| 1 | Visibility of System Status | 3 | Idade dos dados e próxima consulta visíveis; no celular a meta quebra em duas linhas |
| 2 | Match System / Real World | 3 | Vocabulário do operador mantido |
| 3 | User Control and Freedom | 3 | Esc e "Limpar filtros" existem; no celular o "Limpar filtros" ocupa a linha da visão |
| 4 | Consistency and Standards | 2 | "Tabela" fica desativada no celular, mas a preferência salva continua como "tabela" e cai em Compacta sem aviso |
| 5 | Error Prevention | 3 | Cooldown na atualização; leituras sem confirmação |
| 6 | Recognition Rather Than Recall | 2 | Legenda dos status só em Opções; "Atrasado" sem explicação na primeira tela |
| 7 | Flexibility and Efficiency | 2 | Sem atalhos no celular; trocar de página exige rolar até o topo |
| 8 | Aesthetic and Minimalist Design | 2 | Antes do primeiro pedido há 549px de 812px (68%): meta, nav, faixa, 4 cards, busca, pílulas, visão e Opções |
| 9 | Error Recovery | n/a | Não exercitado nesta rodada |
| 10 | Help and Documentation | 2 | Explicações de status só em Opções e tooltips |
| **Total** | | **23/36** | **Acceptable (64%)** |

Max aplicável: 36 (heurística 9 marcada n/a). Snapshot de mobile: não comparável diretamente com a crítica de desktop de 28/40.

## Design Specificity Verdict

LLM assessment: a tela continua específica do produto (pedidos, Tiny desatualizado, Precisam de ação, legenda de atrasados). O problema no celular é de densidade vertical: muitos controles empilhados antes do conteúdo que o operador veio buscar.

Deterministic scan: impeccable detect --json (relatorio_rastreio.html, pedidos_atrasados.html, opcoes_frete.html, web/), 9 achados, exit 2:
- overused-font: Inter, em 3 HTMLs e web/css/main.css (decisão documentada, falso positivo para este produto).
- design-system-color (advisory): rgb(191,219,254) na borda do selo "Mais barato" em opcoes_frete.html (documentado em DESIGN.md como exceção).
- side-tab: web/css/components.css:484, border-left 3px com cor neutra (falso positivo provável).
- design-system-font: web/css/components.css:752, Sfmono-Regular (fallback monoespaçado documentado).
Nenhum achado detector trata de toque, espaço ou tamanho de texto: a medição de celular foi feita no navegador.

Visual overlays: não injetados nesta rodada (foco em medição de celular, sem [Human] tab).

## Overall Impression

A tela principal chegou a y=549 no primeiro pedido em 360–390px (a crítica anterior media 668 em 375). O ganho vem de cabeçalho e cartões mais enxutos, mas os controles de lista ainda ocupam três faixas de altura 40px antes do conteúdo. O maior ganho possível agora está em alvos de toque, na troca de página e no espaço acima da lista.

## Medições (celular)

Acima do primeiro pedido (375px): header 16–156px (título+tema em 140px com meta de 2 linhas, 38px); nav 112–156px; faixa de status ~176–216px; cartões de resumo em 2 colunas ~235–335px; busca 353–403px; pílulas 421–461px; visão + Opções 474–518px; primeiro cartão em y=549.
- 360px: primeiro pedido y=549; 375px: y=549; 390px: y=549; 412px: y=530.
- Estouro horizontal: 0 em todas as larguras (overflowX=0), também no tema escuro a 412px.

Alvos de toque abaixo de 44px (360–412px): 10 elementos.
- Pílulas de filtro: 40px de altura (7 pílulas: Todos 97×40, Em trânsito 154×40, Entregues 139×40, Não enviados 161×40, Atrasados 118×40, Aguardando retirada 187×40, Devolvidos 124×40).
- Botão de tema "Escuro": 44×40.
- "Opções": 52×40.
- Seletor de ordem dentro de Opções: 26×40 (medido com o menu fechado; conferir aberto).
- Espaço entre pílulas: 6px (abaixo dos 8px pedidos).
- Botões de Cartões/Compacta/Tabela: 44px de altura, ok.

Texto e campos:
- Busca: 16px (sem zoom automático no iOS, verificado por computed style; zoom real no iOS não foi testado no navegador embutido).
- Seletor de ordem: 14px (dispara zoom automático no iOS ao focar).
- Placeholder da busca: "Pedido, cliente, rastreio ou cidade" cortado em 360–375px.
- Meta do cabeçalho: 2 linhas em 375px (38px de altura).

Pílulas: faixa com rolagem horizontal (scrollWidth 1049 px para 351 px visíveis). "Devolvidos" fica a 3–4 gestos do início. Zero Is Calm mantido: "Atrasados 0" e "Aguardando retirada 0" com borda tracejada, mas ficam no fim da rolagem.

Visão: com a preferência salva painel.visao=tabela (localStorage), a visão "Tabela" aparece desativada e a Compacta fica pressionada sem explicação.

Elementos fixos: apenas o botão flutuante "Consultar Tiny e Correios" (52×52, em x=307, y=744 a 375px; 16px da margem inferior). Ele não cobre o cartão de ação em 375px no scroll inicial. A nav de abas não é fixa: para trocar de página é preciso voltar ao topo.

Tamanho da lista: 24 cartões de 227px cada no celular, docHeight 6.4–7.0k px. Para ir do último pedido à aba Opções de Frete são cerca de 6 mil px de rolagem.

Tarefas no celular (contagem aproximada):
- Ver o que precisa de ação: 0 toques, rolagem: a faixa e os cartões estão acima da dobra só a partir do y=549.
- Achar pedido pela busca: 2 toques (campo + teclado) + digitação; o campo fica em y=353.
- Filtrar por status: 1 toque, mas o alvo está na faixa de rolagem horizontal (até 3 gestos).
- Copiar rastreio: 1 toque no cartão, sem necessidade de rolagem extra.
- Abrir histórico: 1 toque ("Ver histórico completo" é <details>, 23 fechados).
- Consultar Tiny e Correios: 1 toque no botão flutuante (zona do polegar).
- Trocar de página a partir do fim da lista: 1 toque + ~6 mil px de rolagem até o topo.

Atrasados (375px): sem pedidos na amostra de hoje (0 atrasados); a aba de navegação quebra em duas linhas (Painel / Atrasados (0) numa linha, Opções de Frete na seguinte), e "Ver o painel" tem 29px de altura. O botão de tema tem 40px.

Frete (375px): título "Opções de Frete / Correios" quebra em duas linhas; bloco de pacote com 2 linhas; campos de valor mínimo e máximo em 2 colunas (Valor mínimo do pedido (R$) quebra); placeholder da busca cortado; 66 cartões de serviço em coluna única, docHeight 2910px; o primeiro pedido começa em ~y=590. O cartão "Menor frete do lote" aparece esmaecido na captura (não confirmado se é estado real ou transição de animação; conferir).

Desempenho percebido: HTML do painel 78KB, 1169 nós no DOM, 24 cartões renderizados, sem imagens, 4 scripts locais com cache-bust. Não foi medido tempo de carga real nem em 3G; a carga local parece imediata.

## What's Working

1. Botão "Consultar Tiny e Correios" flutuante no canto inferior direito, dentro da zona do polegar, com 52px e sem sobreposição do conteúdo principal.
2. Cartões de pedido com "Ver histórico completo" fechado: a lista rola menos por cartão, e o último evento já aparece.
3. Sem estouro horizontal em nenhuma largura medida, nos dois temas; o modo escuro mantém contraste.

## Priority Issues

1. **[P1] Trocar de página exige voltar ao topo.** A nav (Painel / Opções de Frete / Atrasados) não é fixa. Com 24 cartões de ~227px (≈5,4 mil px), sair do fim da lista para Frete custa ~6 mil px de rolagem. Por que importa: a troca entre páginas é uma das tarefas centrais do operador. Correção: nav compacta fixa no topo (44px) ou um item de navegação no rodapé que não conflite com o botão flutuante. Arquivos: Arquivos/consulta_correios.py (HTML gerado), web/css/main.css (regras .nav-tabs). Comando: /impeccable adapt.
2. **[P1] Antes do primeiro pedido há 549px de 812px.** Meta em 2 linhas (38px), nav (44px), faixa de status, 4 cartões em 2×2, busca, pílulas, linha da visão e Opções. Por que importa: o operador veio ver o que está atrasado; hoje ele rola 2/3 da tela antes do primeiro cartão. Correção: meta em uma linha no celular (sem "próxima em"), cartões de resumo em uma faixa compacta, e visão + Opções na mesma linha da busca. Arquivos: Arquivos/consulta_correios.py, web/css/main.css, web/css/components.css. Comando: /impeccable layout, depois /impeccable distill.
3. **[P1] Alvos de toque abaixo de 44px e pílulas a 6px.** Sete pílulas com 40px, o botão de tema 44×40, o "Opções" 52×40 e as pílulas separadas por 6px. Por que importa: toques errados em uma faixa de rolagem horizontal, com o polegar. Correção: min-height 44px nas pílulas e em Opções, tema 44×44, gap de 8px. Arquivos: Arquivos/consulta_correios.py (HTML das pílulas), web/css/components.css (.filter-pill, summary de Opções, .btn-theme). Comando: /impeccable adapt.
4. **[P2] Seletor de ordem com 14px.** Dentro de Opções, o select tem 14px e o iOS amplia a tela ao focar. Correção: 16px no celular. Arquivos: web/css/components.css (.sort-select). Comando: /impeccable polish.
5. **[P2] Visão "Tabela" desativada com preferência salva.** Com painel.visao=tabela no localStorage, o celular mostra Compacta pressionada, sem aviso. Correção: no celular, tratar "tabela" como Compacta sem sobrescrever a preferência, e mostrar um rótulo "Tabela indisponível no celular" ao tocar. Arquivos: web/js/dashboard.js. Comando: /impeccable clarify.
6. **[P2] Página de atrasados: nav em duas linhas.** Painel, Atrasados (0) e Opções de Frete quebram em duas linhas com um item sozinho. Correção: depende da nova nav do item 1; aplicar nela. Arquivos: web/css/main.css, Arquivos/consulta_correios.py. Comando: /impeccable adapt (depois do lote A).
7. **[P2] Frete: título, bloco de pacote e busca ocupam ~590px antes do primeiro pedido.** O título "Opções de Frete / Correios" quebra em 2 linhas, o bloco de pacote tem 2 linhas e o placeholder da busca corta. A regra DESIGN.md diz 1.25rem no celular; o título parece maior e não foi medido. Correção: título em uma linha, bloco de pacote recolhido em uma linha, placeholder mais curto, e medir o font-size do título no celular. Arquivos: Arquivos/frete/report.py (CSS embutido), web/css/main.css. Comando: /impeccable typeset, depois /impeccable adapt.
8. **[P2] Botão flutuante sem espaço de rolagem no fim da lista.** Não cobre o cartão em 375px no início, mas o fim da lista pode ficar atrás dele; falta padding inferior no contêiner de pedidos. Correção: padding-bottom de ~84px no contêiner. Arquivos: web/css/components.css (.floating-actions e contêiner da lista). Comando: /impeccable polish.
9. **[P3] Legenda dos status só em Opções.** "Atrasado" e "Aguardando retirada" não se explicam na primeira tela. Correção: title e descrição curta em cada pílula e selo; legenda completa continua em Opções. Arquivos: Arquivos/consulta_correios.py, web/js/dashboard.js. Comando: /impeccable clarify.
10. **[P3] Placeholder da busca cortado em 360–375px.** "Pedido, cliente, rastreio ou cidade" corta em "cidade ou". Correção: "Pedido, cliente ou rastreio" no celular. Arquivos: Arquivos/consulta_correios.py. Comando: /impeccable clarify.
11. **[P3] Achados do detector em tokens documentados.** side-tab em web/css/components.css:484 (borda neutra), Sfmono-Regular em components.css:752, cor do selo "Mais barato" em opcoes_frete.html. Correção: registrar em DESIGN.md ou ajustar config.json; não mexer no CSS. Comando: /impeccable document.

## Persona Red Flags

**Casey (Distracted Mobile User):** precisa de 1 toque para consultar e de 1 toque para copiar, mas trocar de página exige voltar ao topo de ~6 mil px. Os filtros de status exigem rolagem horizontal com alvos de 40px.

**Jordan (First-Timer):** "Atrasado" e "Aguardando retirada" só têm explicação em Opções, e a visão "Tabela" aparece desativada sem motivo.

**Sam (Accessibility-Dependent):** alvos de 40px nas pílulas e em Opções são menores que o recomendado (44px); o select de 14px no iOS amplia a página.

## Minor Observations

- Meta do cabeçalho em 2 linhas: útil, mas poderia ser uma linha no celular.
- Cartões de resumo em 2×2 ocupam ~100px a mais que uma faixa de 4 colunas compactas.
- O cartão "Menor frete do lote" aparece esmaecido na captura do frete: confirmar se é transição de animação.

## Questions to Consider

- "Se a nav ficasse fixa, o botão flutuante ainda precisaria ficar no canto?"
- "O que precisa estar acima do primeiro pedido: a faixa de status, os 4 cartões ou só a contagem de atrasados?"
- "Por que a visão e a ordenação continuam na lista se no celular só existem dois modos?"

## Lotes de execução

- **Lote A (cabeçalho e navegação):** itens 1, 2 e 6. Mesmas regras de .nav-tabs, meta e cartões de resumo em main.css. Executar primeiro.
- **Lote B (controles da lista):** itens 3, 4 e 10 (pílulas, Opções, select e busca). Depende de A na mesma faixa de main.css/components.css: executar depois de A, ou em paralelo só se editar regras diferentes.
- **Lote C (preferência da visão):** item 5. Independente (web/js/dashboard.js).
- **Lote D (fim da lista e botão flutuante):** item 8. Independente de A e B (components.css, regras .floating-actions e contêiner da lista; cuidado com o lote B no mesmo arquivo).
- **Lote E (página de frete):** item 7. Independente (Arquivos/frete/report.py). Não mexe no HTML do painel.
- **Lote F (textos e legenda):** item 9. Depende de C (dashboard.js) e de B (busca).
- **Lote G (detector e documentação):** item 11. Depende de B (components.css) e de E (frete).

Ordem recomendada: A → B → (C, D, E em paralelo) → F → G → /impeccable polish no final.
