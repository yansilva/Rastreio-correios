---
name: Rastreio Correios
description: Painel local de expedição que mostra, de relance, quais pedidos do Tiny ERP estão atrasados ou parados.
colors:
  primary: "#2563eb"
  primary-hover: "#1d4ed8"
  primary-light: "#eff6ff"
  on-primary: "#ffffff"
  bg: "#f8fafc"
  surface: "#ffffff"
  surface-hover: "#f1f5f9"
  header-bg: "#f1f5f9"
  border: "#e2e8f0"
  text-main: "#0f172a"
  text-muted: "#475569"
  text-subtle: "#64748b"
  success: "#15803d"
  success-bg: "#dcfce7"
  success-border: "#bbf7d0"
  warning: "#b45309"
  warning-bg: "#fef3c7"
  warning-border: "#fde68a"
  danger: "#b91c1c"
  danger-bg: "#fee2e2"
  danger-border: "#fecaca"
  info: "#0284c7"
  info-bg: "#e0f2fe"
  info-border: "#bae6fd"
  purple: "#9333ea"
  purple-bg: "#f3e8ff"
  purple-border: "#e9d5ff"
  console-bg: "#0f172a"
  console-header: "#1e293b"
  console-text: "#f8fafc"
typography:
  body:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  title:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
    fontSize: "1.2rem"
    fontWeight: 700
    lineHeight: 1.6
  label:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
    fontSize: "0.78rem"
    fontWeight: 600
    letterSpacing: "0.05em"
  display:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
    fontSize: "2.25rem"
    fontWeight: 800
    lineHeight: 1.6
    letterSpacing: "-0.025em"
rounded:
  sm: "6px"
  md: "10px"
  lg: "16px"
  full: "9999px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.title}"
    rounded: "{rounded.full}"
    padding: "12px 22px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "{colors.on-primary}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-main}"
    rounded: "{rounded.full}"
    padding: "10px 18px"
  filter-pill:
    backgroundColor: "transparent"
    textColor: "{colors.text-muted}"
    rounded: "{rounded.full}"
    padding: "7px 14px"
  filter-pill-active:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.full}"
    padding: "7px 14px"
  search-input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-main}"
    rounded: "{rounded.lg}"
    padding: "14px 18px 14px 46px"
  dash-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-main}"
    rounded: "{rounded.lg}"
    padding: "18px 20px"
  badge-red:
    backgroundColor: "{colors.danger-bg}"
    textColor: "{colors.danger}"
    rounded: "99px"
    padding: "2px 8px"
---

# Design System: Rastreio Correios

## Overview

**Creative North Star: "O Painel de Expedição"**

O painel é uma ferramenta de operação diária. Quem o abre quer saber, em poucos segundos, o que chegou, o que está parado e o que está atrasado. A aparência deve ser calma e precisa: cartões brancos sobre um fundo cinza-azulado claro, tipografia sem ornamento e cor usada para significar estado, não para decorar.

O sistema é denso sem ser apertado. Números grandes resumem a situação nos cartões de topo; a lista de pedidos rola abaixo, com cada pedido em um cartão de cabeçalho cinza e uma linha do tempo vertical de eventos. A busca e os filtros ficam sempre à vista, porque a tarefa típica é localizar um pedido específico ou um grupo de atrasados.

O sistema tem modo claro e escuro, com a alternância seguindo a preferência do sistema operacional. No modo escuro as superfícies sobem em tons de azul-marinho, sem perder a hierarquia.

**Key Characteristics:**
- Cartões brancos e bordas finas sobre fundo frio.
- Cor de status (vermelho, laranja, amarelo, verde, roxo) é o principal sinal de urgência.
- Números grandes e pesados para resumos; texto de corpo discreto.
- Profundidade leve: sombras pequenas em repouso, maiores no hover.
- Português brasileiro em todos os rótulos.

## Colors

A paleta é fria e neutra, com um único azul de ação e um conjunto de cores semânticas para estados de pedido. As cores de status são o sinal principal de urgência e devem ser lidas antes do texto.

### Primary
- **Correio Azul** (#2563eb): ação principal e seleção ativa. Usado no botão de sincronização, no filtro ativo, no título do painel e no número total de pedidos. Ocupa pouca área; quando aparece em excesso, a tela perde a hierarquia.
- **Azul Pressionado** (#1d4ed8): estado de hover do botão principal.
- **Azul Névoa** (#eff6ff): fundo sutil de cartão selecionado e de hover em filtros.

### Neutral
- **Papel Frio** (#f8fafc): fundo da página.
- **Branco Cartão** (#ffffff): superfície de cartões, campos e tabelas.
- **Cinza Cabeçalho** (#f1f5f9): cabeçalhos de pedido, de tabela e hover de linha.
- **Borda Fina** (#e2e8f0): todas as bordas e divisórias.
- **Tinta Principal** (#0f172a): texto principal.
- **Tinta Discreta** (#475569): texto secundário, rótulos e metadados.
- **Tinta Sutil** (#64748b): placeholders e ícones decorativos. Não usar para texto informativo; ver a nota de contraste abaixo.

### Status
- **Vermelho Atraso** (#b91c1c) com fundo (#fee2e2): atraso crítico e devolvido em alerta.
- **Laranja Alta** (#ea580c): urgência alta na tabela de atrasados.
- **Âmbar Atenção** (#b45309) com fundo (#fef3c7): aguardando retirada e alerta moderado.
- **Verde Entregue** (#15803d) com fundo (#dcfce7): entregue.
- **Roxo Devolvido** (#9333ea) com fundo (#f3e8ff): devolvido.
- **Azul Informação** (#0284c7) com fundo (#e0f2fe): informação neutra.

### Named Rules
**The One Signal Rule.** O azul de ação aparece em no máximo um elemento de decisão por área visível. Cor de status é reservada para estado do pedido; nunca usar vermelho ou verde como decoração.

**The Contrast Floor Rule.** Texto em qualquer cor de status precisa de 4.5:1 sobre o fundo onde aparece. Os tons de texto (Verde, Âmbar, Vermelho e Tinta Discreta) foram escurecidos para atingir esse mínimo; ícones e bordas podem usar os tons mais claros.

## Typography

**Body Font:** Inter, com pilha de fallback do sistema (-apple-system, Segoe UI, Roboto, Arial).
**Label Font:** a mesma família, com caixa-alta e espaçamento de letras.
**Mono:** ui-monospace, SFMono, Consolas, para o console de logs.

**Character:** Uma família única, funcional, sem display separado. A hierarquia vem de peso e tamanho, não de troca de fonte.

Observação: `web/css/main.css` declara Inter sem carregá-la; o navegador usa o fallback do sistema quando Inter não está instalada.

### Hierarchy
- **Display** (800, 2.25rem / 1.6, -0.025em): título do painel, apenas uma vez por página.
- **Headline / Number** (800, 1.75rem / 1.1): números dos cartões de resumo.
- **Title** (700, 1.2rem / 1.6): nome do pedido no cabeçalho de cada cartão.
- **Body** (400, 1rem / 1.6): descrições de evento. Manter linhas curtas nos cartões.
- **Label** (600–700, 0.78rem, 0.05em, caixa-alta): rótulos de cartões, cabeçalhos de tabela e badges.

### Named Rules
**The Number First Rule.** Em cada cartão de resumo, o número vem antes do rótulo. O rótulo é uma legenda, não o foco.

## Layout

Coluna central com largura máxima de 1040px e margem de 20px nas laterais de página (12px no mobile). Cabeçalho centralizado com título e meta. Os cartões de resumo usam grade automática com colunas mínimas de 180px; no mobile, duas colunas fixas. Controles (busca e filtros) ocupam a largura total, com contador alinhado à direita.

A barra de filtros quebra linha em telas estreitas; no mobile vira coluna, e a faixa de pílulas rola horizontalmente sem quebrar em linhas.

Espaçamento observado: 8, 10, 14, 16, 18, 20 e 28–32px entre blocos. Não há escala formal de espaçamento no código.

Botão de sincronização é flutuante no canto inferior direito, com 24px de margem (16px no mobile).

## Elevation & Depth

Profundidade em camadas leves. Em repouso, cartões usam `--shadow-sm` (sombra mínima). No hover, cartões de resumo sobem 2px e ganham `--shadow-md`. O botão flutuante usa `--shadow-lg` e `--shadow-xl` no hover.

### Shadow Vocabulary
- **Repouso** (`box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05)`): cartões, campos e botões secundários.
- **Hover de cartão** (`box-shadow: 0 4px 6px -1px rgba(0,0,0,0.08), 0 2px 4px -2px rgba(0,0,0,0.05)`): cartões de resumo ao passar o mouse.
- **Cartão de pedido** (`box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1)`): cabeçalho de pedido, com hover de `0 10px 15px -3px rgba(0,0,0,0.1)`.
- **Ação flutuante** (`box-shadow: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.04)`): botão de sincronização.
- **Foco de busca** (`box-shadow: 0 0 0 3px rgba(37,99,235,0.12)`): anel de foco do campo de busca.

### Named Rules
**The Quiet Lift Rule.** Sombras são resposta a estado. Elementos em repouso não ganham sombra além da mínima; o hover eleva.

## Shapes

Três famílias de forma. Cartões e campos usam cantos de 16px (`--radius-lg`). Blocos internos e caixas de filtro usam 10px. Pílulas (filtros, botões de ação, links de navegação) usam cantos totalmente arredondados. Cartões de pedido usam 12px, e a barra lateral de status (`border-left`) usa 0 8px 8px 0 para destacar estados críticos.

Bordas são sempre finas (1px) em `--color-border`. A exceção é a barra lateral de urgência na tabela de atrasados, que tem 4px.

## Components

### Buttons
- **Shape:** pílula (9999px).
- **Primary (`.btn-action`):** fundo Correio Azul, texto branco, 12px × 22px, peso 700, sombra grande. Flutuante no canto inferior direito.
- **Hover / Focus:** hover escurece para Azul Pressionado, sobe 2px e aumenta a sombra. Foco visível com contorno de 2px em azul e deslocamento de 3px.
- **Disabled:** fundo Tinta Sutil, sem sombra e sem movimento.
- **Secondary (`.btn-theme`):** fundo branco, borda fina, texto principal. Hover troca a borda para azul.

### Filter Pills
- **Style:** pílula transparente, borda fina, texto Tinta Discreta, 7px × 14px.
- **State:** ativo com fundo azul e texto branco. Hover mostra borda e texto em azul com fundo Azul Névoa.
- **Mobile:** a faixa rola na horizontal sem quebrar linha.

### Cards / Containers
- **Summary card (`.dash-card`, `.summary-card`):** cantos de 16px, fundo branco, borda fina, 18px × 20px. Hover sobe 2px. Estado ativo usa contorno azul de 2px e fundo Azul Névoa. O cartão "Atrasados" (`.dash-card-urgent`) vem primeiro, com borda de status, e ocupa a linha inteira no celular.
- **Order card (`.order-card`):** cantos de 12px, borda fina, sombra média. Cabeçalho em Cinza Cabeçalho com o título à esquerda e, à direita, o selo do status atual (`.badge`), há quanto tempo foi o último evento e o status do Tiny. Só o último evento fica visível; o restante abre em `<details class="order-history">` ("Ver histórico completo"). A lista é ordenada por urgência: aguardando retirada, atrasados (mais antigos antes), devolvidos, em trânsito, não enviados e entregues.
- **Event timeline:** linha vertical de 3px em Borda Fina, bolinha de 12px no início de cada evento. Eventos críticos ganham a cor do status na barra e na bolinha, com fundo levemente tingido.

### Inputs / Fields
- **Search (`.search-input`):** cantos de 16px, borda fina, fundo branco, padding vertical de 14px, ícone de lupa à esquerda em Tinta Sutil.
- **Focus:** borda azul e anel de 3px a 12% de azul.
- **Placeholder:** Tinta Sutil. Contraste de placeholder abaixo do recomendado; aceitável apenas por ser texto de apoio.

### Badges
- **Style:** texto em caixa-alta, peso 700, 0.7rem, cantos de 99px.
- **Variants:** vermelho, âmbar, verde e roxo, cada um com fundo tingido, texto da cor e borda da mesma família.

### Console (SSE)
- **Style:** fundo Tinta Principal (#0f172a), cabeçalho em #1e293b, texto claro em monoespaçada de 0.84rem.
- **Log lines:** borda esquerda de 2px conforme nível (info azul-celeste, sucesso verde, erro vermelho).
- **Traffic lights:** três pontos de 12px (vermelho, amarelo, verde) decorativos no cabeçalho.

### Ícones
- **Style:** SVG de traço fino (1.75px, cantos arredondados), cor herdada do texto (`currentColor`) e 1.1em de tamanho; nos chips de resumo, 1.6rem na cor do status.
- **Theme button:** mostra o ícone do tema de destino (sol no escuro, lua no claro).

### Navigation (`.nav-tabs`)
- **Style:** pílulas com borda fina. Ativa em azul sólido com texto branco e sombra azul suave.
- **Hover:** texto e borda em azul.

## Do's and Don'ts

### Do:
- **Do** usar a cor de status junto com um texto ou rótulo, para que a informação não dependa só de cor.
- **Do** manter o número como elemento dominante em cada cartão de resumo.
- **Do** usar `--radius-full` para ações e filtros, e `--radius-lg` para cartões e campos.
- **Do** testar o layout em 375px de largura: cartões em duas colunas, filtros em faixa horizontal.
- **Do** reutilizar os tokens de `:root` e `[data-theme="dark"]`; nunca escrever cores hexadecimais novas no código de componente.

### Don't:
- **Don't** usar Tinta Sutil (#64748b) para texto informativo sobre fundo branco fora dos placeholders.
- **Don't** usar Âmbar, Verde ou Tinta Sutil para texto pequeno sem escurecer o tom ou acrescentar texto em Tinta Principal.
- **Don't** usar emoji como ícone nem introduzir gradientes ou ilustrações decorativas. Os ícones são SVG de traço fino de 1.75px, definidos em `Arquivos/correios/icons.py` e servidos como sprite inline em cada página; novos ícones seguem o mesmo traço.
- **Don't** criar uma segunda cor de ação; o azul é a única cor de decisão.
- **Don't** aumentar sombras no repouso; a elevação é sempre resposta ao hover.

## Dark Mode

O modo escuro redefine apenas as superfícies e o texto: fundo `#0b0f19`, cartões `#151c2c`, cabeçalhos `#192237`, borda `#26334d`, texto principal `#f8fafc`, texto discreto `#b6c2d2`. As cores de status usam fundos translúcidos (15% de opacidade) e textos mais claros para manter 4.5:1 sobre as superfícies escuras: verde `#4ade80`, âmbar `#fbbf24`, vermelho `#f87171` e laranja `#fb923c`. Console e toast ficam escuros nos dois temas, com tokens próprios (`--console-*`, `--log-*`). Azul Névoa vira `#1e293b`.
