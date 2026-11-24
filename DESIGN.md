---
name: Rastreio Correios
description: Painel local de expedição que mostra, de relance, quais pedidos do Tiny ERP estão atrasados ou parados.
colors:
  primary: "#2554d9"
  primary-hover: "#1d44b8"
  primary-light: "#eef2fd"
  on-primary: "#ffffff"
  link: "#2554d9"
  bg: "#f6f7f9"
  surface: "#ffffff"
  surface-hover: "#f1f3f6"
  header-bg: "#f1f3f6"
  border: "#e3e6ea"
  border-strong: "#7b8594"
  text-main: "#101828"
  text-muted: "#475467"
  text-subtle: "#667085"
  success: "#15803d"
  success-bg: "#dcfce7"
  success-border: "#bbf7d0"
  warning: "#b45309"
  warning-bg: "#fef3c7"
  warning-border: "#fde68a"
  danger: "#b91c1c"
  danger-bg: "#fee2e2"
  danger-border: "#fecaca"
  high-text: "#9a3412"
  high-bg: "#ffedd5"
  info: "#0284c7"
  info-bg: "#e0f2fe"
  info-border: "#bae6fd"
  info-text: "#0369a1"
  success-text: "#166534"
  warning-text: "#92400e"
  purple: "#9333ea"
  purple-bg: "#f3e8ff"
  purple-border: "#e9d5ff"
  purple-text: "#7e22ce"
  console-bg: "#0f172a"
  console-header: "#1e293b"
  console-text: "#f8fafc"
typography:
  display:
    fontFamily: "Segoe UI Variable Display, Segoe UI, system-ui, -apple-system, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Segoe UI Variable Text, Segoe UI, system-ui, -apple-system, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.4
  number:
    fontFamily: "Segoe UI Variable Display, Segoe UI, system-ui, -apple-system, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.1
    fontFeature: "tabular-nums"
  body:
    fontFamily: "Segoe UI Variable Text, Segoe UI, system-ui, -apple-system, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
  secondary:
    fontFamily: "Segoe UI Variable Text, Segoe UI, system-ui, -apple-system, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 500
    lineHeight: 1.5
  badge:
    fontFamily: "Segoe UI Variable Text, Segoe UI, system-ui, -apple-system, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 600
    lineHeight: 1.4
  mono:
    fontFamily: "Cascadia Mono, Cascadia Code, ui-monospace, SFMono-Regular, Consolas, monospace"
    fontSize: "0.8125rem"
    fontWeight: 400
rounded:
  sm: "6px"
  md: "8px"
  lg: "10px"
  full: "9999px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.secondary}"
    rounded: "{rounded.md}"
    padding: "0 14px"
    height: "36px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "{colors.on-primary}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-main}"
    borderColor: "{colors.border-strong}"
    rounded: "{rounded.md}"
    padding: "0 14px"
    height: "36px"
  nav-tab:
    backgroundColor: "transparent"
    textColor: "{colors.text-muted}"
    rounded: "0"
    padding: "0 12px"
    height: "40px"
  nav-tab-active:
    textColor: "{colors.text-main}"
    indicator: "inset 0 -2px 0 {colors.primary}"
  filter-pill:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-muted}"
    borderColor: "{colors.border-strong}"
    rounded: "{rounded.sm}"
    padding: "0 10px"
    height: "32px"
  filter-pill-active:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.sm}"
  search-input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-main}"
    borderColor: "{colors.border-strong}"
    rounded: "{rounded.md}"
    padding: "0 12px 0 36px"
    height: "40px"
  dash-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-main}"
    rounded: "{rounded.lg}"
    padding: "14px 16px"
  order-card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.lg}"
    padding: "14px 16px"
  badge-red:
    backgroundColor: "{colors.danger-bg}"
    textColor: "{colors.danger}"
    rounded: "{rounded.sm}"
    padding: "2px 8px"
---

# Design System: Rastreio Correios

> **Direção atual: "Mesa Limpa"** (aprovada pelo usuário em 2026-11-24). Este documento já descreve a direção nova. A implementação segue `.equipe/brief-mesa-limpa.md` (lotes A–D do frontend); até o fim dela, partes do código ainda usam a direção anterior, resumida em **Histórico de direção**, no fim do arquivo.

## Overview

**Creative North Star: "A Mesa Limpa"**

O painel é uma ferramenta de operação diária. Quem o abre quer saber, em poucos segundos, o que chegou, o que está parado e o que está atrasado. A Mesa Limpa é uma mesa de trabalho arrumada: superfícies brancas e planas sobre um cinza frio muito claro, linhas finas no lugar de sombras, tipografia do sistema e cor só onde há algo a fazer.

O sistema é denso sem ser apertado. Os números do resumo são médios e alinhados (algarismos de largura fixa); a lista de pedidos rola abaixo, com cada pedido num cartão plano e uma linha do tempo vertical de eventos. A busca e os filtros ficam sempre à vista.

O sistema tem modo claro e escuro, com a alternância seguindo a preferência do sistema operacional. No escuro, as superfícies são grafite frio, sem azul-marinho.

**Key Characteristics:**
- Superfícies planas e bordas de 1px; sombra só como resposta ao hover.
- Cor de status (vermelho, laranja, âmbar, verde, roxo, azul) é o principal sinal de urgência, sempre com texto.
- Fonte do sistema, sem fonte web; códigos de rastreio em monoespaçada.
- Cantos discretos (6 a 10px); o círculo completo fica para o botão flutuante e para contadores.
- Movimento só de cor e borda, em 120ms.
- Português brasileiro em todos os rótulos.

## Colors

A paleta é fria e neutra, com um único azul de ação e um conjunto de cores semânticas para estados de pedido. Os tokens mantêm os nomes de `web/css/main.css` (`--color-*`); só os valores mudam.

### Primary
- **Azul Ação** (`--color-primary`, #2554d9; 6,27:1 com texto branco): ação principal e seleção ativa. Usado no botão "Consultar Tiny e Correios", no filtro ativo e no sublinhado da aba atual. O título do painel deixa de ser azul.
- **Azul Pressionado** (`--color-primary-hover`, #1d44b8): hover do botão principal.
- **Azul Névoa** (`--color-primary-light`, #eef2fd): fundo do cartão de resumo ativo.
- **Link** (`--color-link`, #2554d9 no claro; #8db0ff no escuro).

### Neutral
- **Papel** (`--color-bg`, #f6f7f9): fundo da página.
- **Superfície** (`--color-surface`, #ffffff): cartões, campos, tabelas e barras.
- **Superfície 2** (`--color-surface-hover` e `--color-header-bg`, #f1f3f6): cabeçalho de tabela, hover de linha, aba e segmento pressionados.
- **Borda** (`--color-border`, #e3e6ea): cartões e divisórias.
- **Borda de controle** (`--color-border-strong`, #7b8594): contorno de campos, filtros e botões secundários (3,73:1 sobre a superfície; 3,48:1 sobre o papel).
- **Tinta** (`--color-text-main`, #101828): texto principal.
- **Tinta Discreta** (`--color-text-muted`, #475467): rótulos e metadados (7,69:1 na superfície; 6,92:1 na Superfície 2).
- **Tinta Sutil** (`--color-text-subtle`, #667085): placeholder, contadores dentro de filtros e números zerados. Só sobre `--color-surface` (4,97:1) ou `--color-bg` (4,64:1); sobre a Superfície 2 fica em 4,48:1 e não passa.

### Status (sem mudança de valor)
- **Crítico** (7+ dias): texto `--color-danger` #b91c1c sobre `--color-danger-bg` #fee2e2 (5,30:1).
- **Alto** (5–6 dias): texto `--color-high-text` #9a3412 sobre `--color-high-bg` #ffedd5 (6,38:1).
- **Atenção** (3–4 dias) e **Aguardando retirada**: texto `--color-warning-text` #92400e sobre `--color-warning-bg` #fef3c7 (6,37:1).
- **Entregue**: `--color-success-text` #166534 sobre `--color-success-bg` #dcfce7 (6,49:1).
- **Devolvido**: `--color-purple-text` #7e22ce sobre `--color-purple-bg` #f3e8ff (5,92:1).
- **Em trânsito / informação**: `--color-info-text` #0369a1 sobre `--color-info-bg` #e0f2fe (5,17:1).
- **Borda do selo "Mais barato"** (#bfdbfe, `--color-badge-border`): exceção de página em `Arquivos/frete/report.py`; no escuro, `rgba(147, 197, 253, 0.35)`.

**Exceções do detector** (registradas em `.impeccable/config.json`, só para o arquivo indicado):
- `side-tab` em `web/css/components.css`: a borda esquerda de 3px da timeline usa a cor neutra `--color-border` como trilho; não é acento colorido.
- `design-system-font` em `web/css/components.css`: `Sfmono-Regular` é o fallback monoespaçado da pilha mono.

### Named Rules
**The One Signal Rule.** O azul de ação aparece em no máximo um elemento de decisão por área visível. Cor de status é reservada para estado do pedido; nunca usar vermelho ou verde como decoração.

**The Contrast Floor Rule.** Texto precisa de 4,5:1 sobre o fundo onde aparece, nos dois temas, inclusive em selos de fundo translúcido (medir com a composição do alfa sobre a superfície real). Recalcule sempre que um hexadecimal mudar.

**The Control Edge Rule.** Campos, filtros e botões cujo contorno é o único limite visível usam `--color-border-strong`, com pelo menos 3:1 contra o fundo nos dois temas (WCAG 1.4.11). A borda fina `--color-border` fica para cartões e divisórias.

## Typography

**Sans:** pilha do sistema, sem fonte web. `--font-sans: "Segoe UI Variable Text", "Segoe UI", system-ui, -apple-system, Roboto, "Helvetica Neue", Arial, sans-serif`. Título e números usam `--font-display: "Segoe UI Variable Display", "Segoe UI", system-ui, -apple-system, Roboto, "Helvetica Neue", Arial, sans-serif`.
**Mono:** `--font-mono: "Cascadia Mono", "Cascadia Code", ui-monospace, SFMono-Regular, Consolas, monospace`, para códigos de rastreio, CEP e o console de logs.
**Números:** `font-variant-numeric: tabular-nums` em resumo, contadores, datas, dias, preços e colunas numéricas.

A Inter deixa de ser carregada (`@font-face` sai de `main.css` e do frete). O arquivo `web/fonts/InterVariable.woff2` fica no repositório até o usuário decidir sobre ele; a direção não depende dele. No Windows a fonte é a Segoe UI Variable; no Android, Roboto; no iPhone, San Francisco.

### Hierarchy
Escala de seis degraus (12, 13, 14, 16, 20 e 24px = 0.75, 0.8125, 0.875, 1, 1.25 e 1.5rem). Pesos 400, 500 e 600; 700 e 800 saem.
- **Display** (600, 24px / 1.2, -0.01em; 20px no celular): título da página, uma vez por página.
- **Number** (600, 24px / 1.1, tabular; 20px no celular): números do resumo.
- **Title** (600, 16px / 1.4): número e cliente no cabeçalho do cartão de pedido.
- **Body** (400, 14px / 1.5): texto de evento e células de tabela.
- **Secondary** (500, 13px): meta do cabeçalho, botões, abas, filtros, rótulos do resumo, datas.
- **Badge / Caption** (600, 12px): selos, contadores e cabeçalho de tabela. Menor tamanho permitido.
- **Campos no celular:** busca, seletor de ordem e valores do frete em 16px até 640px (o iOS não amplia a página ao focar).

Sem caixa-alta: rótulos do resumo, cabeçalhos de tabela, selos e o título da faixa de ação passam a usar caixa normal, sem `letter-spacing`.

### Named Rules
**The Zero Is Calm Rule.** Contador zerado não chama atenção: sem atrasos nem retiradas a faixa vira uma linha verde calma; chips, filtros e cartões zerados ficam neutros (filtro e chip com borda tracejada, número em Tinta Sutil) e não filtram; o mesmo vale para os totais zerados da página de atrasados.

**The One Meaning Per Color Rule.** Verde é "entregue" e vermelho, laranja e âmbar são pendências; o frete não usa verde para "disponível".

**The Number First Rule.** Em cada cartão de resumo, o número vem antes do rótulo.

**The Ramp Rule.** Nenhum texto abaixo de 12px, e todo tamanho cai num dos seis degraus.

## Layout & Density

Coluna central de 1040px, com 24px de margem lateral no desktop e 12px no celular.

**Cabeçalho (`header`):**
- **A partir de 1100px:** duas linhas. Na primeira, o título e a meta, alinhados à esquerda. Na segunda, as abas à esquerda e as ferramentas (`.header-tools`: tema e "Consultar Tiny e Correios") à direita, na mesma linha. Uma borda de 1px (`--color-border`) fecha o cabeçalho, com 20px até a faixa de ação.
- **De 641 a 1099px:** título e meta, depois as abas e, abaixo delas, as ferramentas (decisão do usuário).
- **Até 640px:** título na linha de cima com o tema (ícone de 44px) à direita; a meta curta numa linha, a 12px: "Dados 04/11 15:24 (há 13 min) · próxima em 35 min"; abas fixas no topo (ver Navigation); "Consultar" vira o botão flutuante.
- A idade dos dados ("há N min") fica sempre visível. A meta usa `.meta-longo`/`.meta-curto` e `.contagem-completa`/`.contagem-curta`, escolhidas por CSS.

**Densidade:**
- Espaço entre blocos: 12px (cartões entre si), 16px (busca → filtros → lista), 20px (cabeçalho → conteúdo). Escala de espaçamento: 4, 8, 12, 16, 20, 24px.
- Cartões: 14×16px de espaço interno. Linha de tabela: 44px no desktop. Alvos: 32–40px no desktop, 44px no celular.
- Cartões de resumo em grade de 4 colunas (desktop); no celular, faixa de 4 colunas com o número acima de um rótulo de 12px, alinhados pelo topo (`justify-content: flex-start`), com 8×4px de espaço interno.
- A faixa de filtros nunca quebra linha: rola na horizontal quando não cabe.
- O contador de pedidos (`#filterCount`) fica à direita da busca, na mesma linha (`.search-row`).

## Elevation & Depth

Plano por padrão. Em repouso, nada tem sombra, exceto o botão flutuante do celular.

### Shadow Vocabulary
- **Repouso** (`--shadow-sm: none`): cartões, campos, filtros e botões.
- **Hover** (`--shadow-md: 0 1px 2px rgba(16, 24, 40, .06), 0 2px 8px -2px rgba(16, 24, 40, .08)`): cartão de resumo e cartão de pedido, junto com a borda passando a `--color-border-strong`. No escuro, `--shadow-md: 0 0 0 1px #343c49` (um anel, porque sombra some no escuro).
- **Ação flutuante** (`--shadow-lg`, como hoje): só o botão flutuante do celular.
- **Foco** (contorno, não sombra): `outline: 2px solid var(--color-primary); outline-offset: 2px` em todo controle; na busca, borda azul e anel `0 0 0 3px` a 15% do azul.

### Named Rules
**The Quiet Lift Rule.** Sombras são resposta a estado. Nada sobe (`translateY`) no hover; muda a borda e entra a sombra mínima.

## Shapes

- `--radius-sm` (6px): filtros, chips da faixa de ação, selos, segmentos da visão.
- `--radius-md` (8px): campos, botões, menu Opções, contêiner do controle segmentado.
- `--radius-lg` (10px): cartões de resumo, cartões de pedido, tabelas, faixa de ação, estado vazio.
- `--radius-full`: só o botão flutuante, os pontos de status e o contador da aba Atrasados.

Bordas sempre de 1px. A timeline usa trilho de 3px em `--color-border`. Nenhum acento colorido na lateral de cartões (a borda lateral do frete já saiu).

## Motion

- `--motion: 120ms ease-out`, só em `color`, `background-color`, `border-color` e `box-shadow`. Sem `transition: all`, sem `translateY` no hover, sem `scale` no clique.
- O giro do ícone no botão de consulta continua: é feedback de "consultando". O `fadeIn` dos cartões do frete sai.
- `@media (prefers-reduced-motion: reduce)`: `transition: none` e `animation: none` em tudo; o botão de consulta mostra o estado só pelo texto.

## Components

### Buttons
- **Primary (`.btn-action`):** fundo Azul Ação, texto branco, 36px de altura, 0×14px, 13px peso 600, raio de 8px, sem sombra. Hover: Azul Pressionado. No celular vira o círculo flutuante de 52px no canto inferior direito, com `--shadow-lg` e `aria-label`.
- **Secondary (`.btn-theme`, `.btn-copy`, `.btn-limpar`):** fundo Superfície, borda `--color-border-strong`, texto Tinta, 36px, raio de 8px. Hover: fundo Superfície 2. No celular, 44px.
- **Disabled:** fundo Superfície 2, texto Tinta Sutil, borda `--color-border`, sem movimento.

### Navigation (`.nav-tabs`)
- **Fonte única:** `nav_html(ativa, atrasados=None)` em `Arquivos/correios/navegacao.py`. Ordem fixa: Painel, Atrasados, Entregues, Opções de Frete. A aba ativa leva `class="nav-tab active"` e `aria-current="page"`.
- **Style:** abas sublinhadas, sem borda nem pílula. Texto Tinta Discreta, 13px peso 500, 40px de altura, 0×12px, raio 0. Ícone de 16px à esquerda, na cor do texto.
- **Aba atual:** texto Tinta, peso 600, e sublinhado de 2px em Azul Ação (`box-shadow: inset 0 -2px 0 var(--color-primary)`). Sem fundo.
- **Hover:** texto Tinta e fundo Superfície 2.
- **Contagem de atrasados (`.atrasados-count`):** bolha de 12px peso 600, fundo `--color-danger-bg`, texto `--color-danger`, raio cheio; só com valor > 0 e só nas páginas que recebem a contagem (o frete não recebe).
- **Celular (até 640px):** nav fora do `<header>`, `position: sticky` no topo, fundo Superfície e borda inferior de 1px; quatro abas numa linha, sem ícones, 44px de altura, 13px.

### Faixa de ação (`.action-strip`)
- Fundo Superfície, borda `--color-border`, raio de 10px, 8×12px de espaço interno. Título "Precisam de ação" em Secondary, Tinta Discreta, sem caixa-alta.
- **Chips (`.action-chip`):** raio de 6px, 32px (44px no celular), fundo e borda da cor do status com o número em peso 600.
- **Calma:** "Nada atrasado nem aguardando retirada" numa linha, fundo `--color-success-bg`, texto `--color-success-text`, ícone de check, 8×12px.
- **Celular:** o título sai da tela (sr-only) e os chips ficam lado a lado, cada um do tamanho do texto.

### Resumo (`.dash-card`, `.summary-card`)
- Fundo Superfície, borda `--color-border`, raio de 10px, 14×16px, sem sombra. Hover: borda forte e `--shadow-md`. Ativo: borda de 2px em Azul Ação e fundo Azul Névoa.
- Número em Number (24px, 600, tabular) na cor Tinta; zerado em Tinta Sutil. Rótulo em Secondary (13px), Tinta Discreta, caixa normal.
- Ícone do painel: 32×32, fundo Superfície 2, raio de 8px, traço na cor Tinta Discreta (o tom de status só no cartão ativo). Some no celular.
- Os quatro cartões do painel somam o total; atrasados e aguardando retirada ficam na faixa de ação.

### Filtros de status (`.filter-pill`)
- Antes eram pílulas redondas; agora são **filtros de raio 6px** (`--radius-sm`).
- 32px de altura (44px no celular), 0×10px, 13px peso 500, fundo Superfície, borda `--color-border-strong`, texto Tinta Discreta. Contador (`.pill-count`) em 12px, Tinta Sutil, tabular.
- **Ativo:** fundo Azul Ação, texto e contador brancos.
- **Zerado:** borda tracejada em `--color-border`, sem filtrar.
- **Layout:** uma linha só em qualquer largura, com rolagem horizontal; ativas primeiro e zeradas no fim; com Tab, o filtro rola até ficar visível.

### Selos (`.badge`, `.dias-badge`)
- **Style:** bolinha de 6px na cor do texto (`::before`, `border-radius: 50%`) e o texto; 12px peso 600, caixa normal, 2×8px, raio de 6px, `white-space: nowrap`, fundo tingido e borda da mesma família.
- **Texto:** sempre diz o estado; o atraso diz o nível ("Atrasado · 6 dias · Alto"). A cor nunca é o único sinal.
- **Variants:** `badge-red` (Crítico, devolvido em alerta), `badge-orange` (Alto), `badge-yellow` (Atenção, aguardando retirada, Tiny desatualizado), `badge-green` (entregue), `badge-purple` (devolvido; com `badge-aviso`, o selo curto "Aviso" das visões Compacta e Tabela), `badge-blue` (em trânsito, postado).
- **Descrição:** a explicação fica num `<span class="sr-only">` logo depois do selo.

### Cartões de pedido (`.order-card`)
- Fundo Superfície, borda `--color-border`, raio de 10px, sem sombra; hover com borda forte e `--shadow-md`.
- **Cabeçalho (`.order-header`):** fundo Superfície (não mais cinza) e borda inferior de 1px; 14×16px. À esquerda, "#43122" e o cliente em Title; abaixo, o rastreio em mono 13px. À direita, o selo, "Último evento hoje" e "Copiar rastreio".
- **Situação no Tiny (`.order-tiny-status`):** só aparece quando a situação do Tiny diverge do status dos Correios (decisão do usuário, 2026-11-24). Quando confirma o que os Correios já dizem (por exemplo, "Enviado" com o pedido em trânsito), a linha não é renderizada. Quem decide se diverge é o backend (`Arquivos/correios/cards.py`); o frontend não esconde por CSS. O selo "Tiny desatualizado" continua para a divergência que pede ação.
- **Evento:** data em Secondary tabular, texto em Body, local em peso 600.
- **Timeline:** trilho de 3px em `--color-border`, bolinha de 10px. Evento crítico pinta bolinha e trilho na cor do status, sem fundo tingido.
- **Encerrados (`.order-closed`):** título em Tinta Discreta, no fim da lista.
- A ordem por urgência, o "Tiny desatualizado" e o histórico em `<details class="order-history">` continuam.

### Aviso dos Correios (`.order-aviso`, definido em 2026-11-24)
Evento informativo dos Correios, como "Sua entrega ou retirada nos Correios pode levar mais tempo do que o previsto". **Não é status:** o selo de status continua o real (por exemplo, Em trânsito), e o aviso é uma informação a mais. Aparece enquanto o objeto não foi entregue. Em pedido entregue ou devolvido, não aparece.
- **Cor:** família roxa (`--color-purple-text`, `--color-purple-bg`, `--color-purple-border`). Não use âmbar, laranja nem vermelho, que são da escala de urgência. O azul (info) também fica de fora, porque o status que mais acompanha o aviso é "Em trânsito", que já é azul, e os dois virariam uma coisa só. O roxo também é o do "Devolvido", mas a forma é outra: no cartão, o aviso é uma linha com rótulo, não um selo, e não aparece em devolvido.
- **Contraste (AA):**
  - Claro: #7e22ce sobre #f3e8ff dá 5,92:1, e sobre branco dá 6,98:1.
  - Escuro: #c084fc sobre o fundo a 15% dá 5,91:1 sobre #151a21 e 5,48:1 sobre #1b212a.
  - A borda roxa no escuro (`rgba(192, 132, 252, .35)`) dá 1,9:1. É decorativa: quem separa a linha da superfície é o fundo tingido, e o texto identifica a linha.
- **No cartão:** uma linha própria, logo abaixo do `.order-header` e acima da "Situação no Tiny" e da timeline.
  - Caixa: fundo `--color-purple-bg`, borda de 1px `--color-purple-border`, raio de 6px, 8×12px de espaço interno, 12px de margem lateral, 8px de margem acima.
  - Conteúdo: ícone `i-info` de 16px (círculo com "i", que não é o triângulo de alerta), na cor do texto; rótulo "Aviso dos Correios" em 13px peso 600; depois o texto do aviso em 13px peso 400. Tudo em `--color-purple-text`.
  - O texto vai **inteiro**, quebrando linha, sem reticências. Os avisos têm menos de 100 caracteres.
  - Se o backend mandar a data do evento, ela vai no fim em Secondary tabular, por exemplo "· 22/11".
  - No celular, o mesmo, ocupando a largura do cartão.
- **Na visão Compacta e na Tabela:** selo curto `badge badge-purple badge-aviso` com o texto "Aviso", ao lado do selo de status (depois dele). O texto completo vai no `title` e num `.sr-only` logo depois do selo ("Aviso dos Correios: …").
- **Faixa de ação:** um chip roxo `.action-chip[data-filter="com_aviso"]`, depois de "Aguardando retirada", com "**N** Com aviso" (singular e plural iguais). O `title` é "Pedidos em aberto com aviso dos Correios, como atraso previsto na entrega".
  - O chip só aparece com N > 0. Aviso é informação, não ação, e não deve ocupar a faixa zerado.
  - A linha calma ("Nada atrasado nem aguardando retirada") só aparece quando atrasados, retiradas e avisos são todos zero. Se só houver aviso, a faixa normal aparece com os dois chips zerados e o chip de aviso.
- **Filtro:** `.filter-pill[data-filter="com_aviso"]` com o rótulo "Com aviso", o ícone `i-info` e `.pill-count`, logo depois de "Aguardando retirada". O estilo é o mesmo dos outros filtros (neutro, com Azul Ação quando ativo), sem roxo.
  - Zerado: borda tracejada e não filtra (The Zero Is Calm Rule).
  - Estado vazio: o `.empty-state` padrão, com check verde e o texto "Nenhum pedido em aberto com aviso dos Correios."

### Tabelas (`.orders-table`, `.table-wrapper`)
- Contêiner com fundo Superfície, borda `--color-border`, raio de 10px.
- Cabeçalho: 12px peso 600, Tinta Discreta, caixa normal, fundo Superfície 2, borda inferior de 1px.
- Linhas de 44px no desktop, divisória de 1px; hover com fundo Superfície 2. Códigos em mono; números e datas tabulares.
- Cliente com no máximo 2 linhas (`-webkit-line-clamp: 2`) e o nome completo no `title`.
- O resto (larguras fixas a partir de 1024px, rolagem do contêiner entre 641 e 1023px, ações numa linha, celular sem Tabela) continua.

### Estado vazio (`.empty-state`)
- Caixa com fundo Superfície, borda `--color-border`, raio de 10px, 16px de espaço interno, alinhada à esquerda: ícone de 18px num círculo de 36px (fundo `--color-success-bg`, traço `--color-success-text`), título em 14px peso 600 e explicação em Tinta Discreta, com a ação como link na mesma linha ("Ver o painel").
- Vale para "Nada atrasado", "Nenhuma entrega nesta semana" e "Nenhum pedido em aberto" do frete. Sem emoji.

### Inputs / Fields
- **Busca (`.search-input`):** 40px, raio de 8px, borda `--color-border-strong`, lupa de 16px em Tinta Sutil, placeholder em Tinta Sutil. Foco: borda azul e anel de 3px a 15%.
- **Celular:** busca recolhida num botão de 44px até ser aberta (como hoje); campos em 16px.
- **Busca do frete:** o mesmo campo, acima dos filtros de valor.

### Controles da lista (`.search-row`, `.list-meta`, `.filters-row`)
- **Desktop:** busca e contador; filtros; "Limpar filtros", visão (Cartões, Compacta, Tabela) e Opções. Alvos de 32–40px.
- **Visão (segmentado):** contêiner com raio de 8px e borda `--color-border-strong`; segmento ativo com fundo Superfície 2, texto Tinta e anel interno de 1px em `--color-border-strong`, sem azul. No celular, a Tabela fica desativada com borda tracejada.
- **Celular:** a mesma grade de hoje (busca recolhida, contador, visão e Opções numa linha; ao abrir, a busca ocupa a linha).
- **Opções:** menu com raio de 10px e borda `--color-border`; seletor de ordem, "Recarregar dados salvos de HH:MM" e "Expandir históricos".
- **Atalhos:** `/` foca a busca e Esc limpa.

### Página Entregues (`entregues_semana.html`)
- Semana atual e anterior do histórico local (`Arquivos/entregas_historico.json`, fora do git), gerada por `Arquivos/correios/pagina_entregues.py`.
- **Seletor de semana (`.entregues-seletor`):** controle segmentado da Visão; o intervalo "(dd/mm–dd/mm)" não quebra.
- **Resumo:** três cartões (total, média de dias, mais demorado). O rótulo do mais demorado quebra depois de "Mais demorado"; só "10,0&nbsp;dias" fica junto.
- **Lista:** tabela com Pedido, Cliente, Rastreio (mono, com "Copiar rastreio"), Cidade, Postado em, Entregue em e Dias. No celular vira cartões, com Cidade e Postado em ocultos na tela e presentes para o leitor de tela.
- **Dias:** acima de 7 dias, `.dias-badge.urgencia-baixa` (âmbar, decisão do usuário).
- **Semana vazia:** só o estado vazio.

### Página Opções de Frete (`opcoes_frete.html`)
- CSS embutido em `Arquivos/frete/report.py`, com os mesmos tokens (repetidos lá) e a mesma pilha de fontes.
- Cada serviço é uma linha de ~44px (desktop) com Serviço | Preço | Prazo | Selos; preço em 16px peso 600 tabular. No celular, 2 colunas e serviço único na linha toda.
- **Resumo no celular:** rótulos curtos ("Pedidos", "Menor frete", "Prazo > 3 dias"); os números dos pedidos do menor frete só no desktop. O link continua levando ao cartão.

### Toasts
- **Cores:** `--color-success` (cópia e atualização), `--color-danger` (erro e "Copie manualmente"), `--color-warning` (cooldown e "Tabela indisponível no celular") e `--color-primary` por padrão; o texto usa `--console-bg` ou `--console-text`, o que tiver mais contraste. Raio de 8px.
- **Sucesso:** `role="status"`, `aria-live="polite"`; a cópia some em 2 s, os demais em 3,5 s.
- **Erro:** `role="alert"`, fica até "Fechar"; falha dupla de cópia mostra "Copie manualmente: CÓDIGO".

### Console (SSE)
- Fundo `--console-bg`, cabeçalho `--console-header`, texto claro em mono de 13px (0.8125rem); linhas com borda esquerda de 2px por nível. Os três pontos decorativos continuam.

### Ícones
- SVG de traço de 1.75px, `currentColor`, 16px nos controles e 1.1em no texto; sprite em `Arquivos/correios/icons.py`. Tema mostra o ícone do tema de destino.

## Do's and Don'ts

### Do:
- **Do** usar a cor de status junto com texto.
- **Do** usar `--radius-sm` em filtros, chips e selos, `--radius-md` em campos e botões e `--radius-lg` em cartões e tabelas.
- **Do** usar `tabular-nums` em números e a mono em códigos.
- **Do** testar em 360 e 375px, nos dois temas, e as duas semanas de Entregues.
- **Do** reutilizar os tokens de `:root` e `[data-theme="dark"]`; nunca escrever hexadecimais novos em componente.

### Don't:
- **Don't** usar Tinta Sutil fora de `--color-surface` e `--color-bg`, nem para texto informativo.
- **Don't** voltar a pílulas redondas em filtros, sombras em repouso ou movimento de subida no hover.
- **Don't** usar caixa-alta com espaçamento em rótulos, selos ou cabeçalhos de tabela.
- **Don't** usar emoji como ícone, gradientes, ilustrações decorativas ou acento colorido na lateral de cartões.
- **Don't** criar uma segunda cor de ação; o azul é a única cor de decisão.
- **Don't** usar 700 ou 800 de peso; o máximo é 600.

## Dark Mode

Superfícies em grafite frio: `--color-bg` #0e1116, `--color-surface` #151a21, `--color-surface-hover` e `--color-header-bg` #1b212a, `--color-border` #262d38, `--color-border-strong` #6b7585 (3,75:1 na superfície; 4,06:1 no fundo), `--color-text-main` #e8ebf0 (14,6:1), `--color-text-muted` #a3adbb (7,70:1; 7,13:1 na Superfície 2), `--color-text-subtle` #8a94a3 (5,70:1), `--color-primary` #2f62e6 (5,24:1 com branco), `--color-primary-hover` #2552c4, `--color-primary-light` #1b2333, `--color-link` #8db0ff (8,14:1).

Status (sem mudança): textos `--color-warning-text` #fbbf24, `--color-high-text` #fb923c, `--color-danger` #f87171, `--color-success-text` #4ade80, `--color-info-text` #38bdf8, `--color-purple-text` #c084fc sobre fundos a 15% de opacidade. Medido sobre #151a21: 8,63, 6,56, 5,72, 8,25, 6,92 e 5,91:1; sobre #1b212a, o menor é 5,32:1 (vermelho).

Bordas de status no escuro (definidas em 2026-11-24, 16ª crítica): a cor do texto do mesmo status a 35%, para a borda nunca ficar mais clara que o texto. `--color-success-border: rgba(74, 222, 128, .35)`, `--color-warning-border: rgba(251, 191, 36, .35)`, `--color-danger-border: rgba(248, 113, 113, .35)`, `--color-info-border: rgba(56, 189, 248, .35)`, `--color-purple-border: rgba(192, 132, 252, .35)`. Valem para selos, chips da faixa de ação e a faixa calma. Antes, esses tokens não tinham valor no escuro e herdavam o pastel do claro (#bbf7d0, #fde68a, #fecaca, #bae6fd, #e9d5ff), o que fazia um halo claro em volta do selo. Regra: todo token usado no claro precisa de valor próprio no escuro.

Console fica escuro nos dois temas (`--console-*`, `--log-*`).

## Histórico de direção

**Até 2026-11-24: "O Painel de Expedição".** Inter embutida (`web/fonts/InterVariable.woff2`), pesos até 800, display de 28px e números de 28px; azul #2563eb também no título; fundo #f8fafc, bordas #e2e8f0, Tinta #0f172a/#475569/#64748b; escuro em azul-marinho (#0b0f19, #151c2c, #192237, borda #26334d, texto #f8fafc/#b6c2d2, Azul Névoa #1e293b). Raios de 16px (cartões e campos), 12px (cartão de pedido) e pílulas redondas em filtros, abas e botões. Sombra mínima em repouso e cartões subindo 2px no hover; `transition: all 0.2s`. Rótulos, selos e cabeçalhos de tabela em caixa-alta com 0.05em. Cabeçalho centralizado com abas em pílula. Trocada pela Mesa Limpa a pedido do usuário ("visual mais moderno"), escolhida entre três direções na 15ª rodada.
