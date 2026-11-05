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
  info-text: "#0369a1"
  success-text: "#166534"
  warning-text: "#92400e"
  purple: "#9333ea"
  purple-bg: "#f3e8ff"
  purple-border: "#e9d5ff"
  console-bg: "#0f172a"
  console-header: "#1e293b"
  console-text: "#f8fafc"
  shadow-soft: "rgba(0, 0, 0, 0.1)"
  shadow-deep: "rgba(0, 0, 0, 0.3)"
  warning-tint: "rgba(217, 119, 6, 0.07)"
typography:
  body:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  title:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 700
    lineHeight: 1.6
  label:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 600
    letterSpacing: "0.05em"
  display:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 800
    lineHeight: 1.6
    letterSpacing: "-0.025em"
  number:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 800
    lineHeight: 1.1
  secondary:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 600
    lineHeight: 1.6
  badge:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 700
    letterSpacing: "0.05em"
rounded:
  sm: "6px"
  md: "10px"
  lg: "16px"
  card: "12px"
  row: "8px"
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
- **Azul Informação** (#0284c7) com fundo (#e0f2fe): informação neutra. Para texto sobre esse fundo (selo "Em trânsito") use o token `--color-info-text` (#0369a1 no claro, ≈5,9:1; no escuro #38bdf8).
- **Verde Texto** (`--color-success-text`, #166534 no claro; #4ade80 no escuro): texto do selo "Nada atrasado nem aguardando retirada" sobre o fundo verde-claro.
- **Âmbar Texto** (`--color-warning-text`, #92400e no claro; #fbbf24 no escuro): texto do selo "Não enviado" sobre o fundo âmbar.
- **Borda do selo "Mais barato"** (#bfdbfe, `--color-badge-border`): borda do selo de frete em `Arquivos/frete/report.py`, que define a variável no CSS embutido do relatório. Não está na tabela de tokens acima; no escuro vira `rgba(147, 197, 253, 0.35)`; fica registrada aqui como exceção de página, e poderia virar token do sistema se o selo for reutilizado.

**Exceções do detector** (registradas em `.impeccable/config.json`, só para o arquivo indicado; o CSS não muda):
- `side-tab` em `web/css/components.css`: a borda esquerda de 3px (`border-left: 3px solid var(--color-border)`) usa a cor neutra `--color-border` como trilho da timeline. Não é acento colorido, então o alerta é falso positivo. O detector não extrai valor de `side-tab`, então a exceção é um curinga restrito ao arquivo (`hooks ignore-value side-tab "*" --file web/css/components.css`); a exceção antiga, por valor, nunca casava.
- `design-system-font` em `web/css/components.css`: `Sfmono-Regular` é o fallback monoespaçado da pilha de DESIGN.md (SFMono). Não é família nova.

### Named Rules
**The One Signal Rule.** O azul de ação aparece em no máximo um elemento de decisão por área visível. Cor de status é reservada para estado do pedido; nunca usar vermelho ou verde como decoração.

**The Contrast Floor Rule.** Texto em qualquer cor de status precisa de 4.5:1 sobre o fundo onde aparece. Os tons de texto (Verde, Âmbar, Vermelho e Tinta Discreta) foram escurecidos para atingir esse mínimo; ícones e bordas podem usar os tons mais claros.

**The Control Edge Rule.** Campos e botões cujo contorno é o único limite visível usam `--color-border-strong` (#64748b), com pelo menos 3:1 contra o fundo nos dois temas (WCAG 1.4.11). A borda fina `--color-border` fica para cartões e divisórias decorativas. O texto dos selos usa os tokens `--color-*-text`: tom mais escuro no tema claro e mais claro no escuro, sempre com 5,7:1 ou mais sobre o fundo do selo.

## Typography

**Body Font:** Inter, com pilha de fallback do sistema (-apple-system, Segoe UI, Roboto, Arial).
**Label Font:** a mesma família, com caixa-alta e espaçamento de letras.
**Mono:** ui-monospace, SFMono, Consolas, para o console de logs.

**Character:** Uma família única, funcional, sem display separado. A hierarquia vem de peso e tamanho, não de troca de fonte.

Inter variável vem embutida (`web/fonts/InterVariable.woff2`, licença SIL OFL ao lado, `font-display: swap`); a pilha do sistema segue como fallback. A página de frete carrega o mesmo arquivo, pelo `@font-face` do próprio relatório.

### Hierarchy
Rampa de seis tamanhos (0.75, 0.8125, 0.875, 1, 1.25 e 1.75rem); todo `font-size` do CSS cai num deles.
- **Display** (800, 1.75rem / 1.6, -0.025em; 1.25rem no celular): título do painel e da página de frete, apenas uma vez por página.
- **Number** (800, 1.75rem / 1.1): números dos cartões de resumo.
- **Title** (700, 1.25rem / 1.6): nome do pedido no cabeçalho de cada cartão.
- **Body** (400, 1rem / 1.6): descrições de evento. Manter linhas curtas nos cartões.
- **Secondary** (400–600, 0.875rem): metadados, situação no Tiny, botões de texto, campos.
- **Label** (600–700, 0.8125rem): rótulos de cartões, datas, legenda, contadores e cabeçalhos de tabela.
- **Badge** (700, 0.75rem, 0.05em, caixa-alta): selos e tags de urgência; é o menor tamanho permitido.
### Named Rules
**The Zero Is Calm Rule.** Contador zerado não chama atenção: sem atrasos nem retiradas a faixa vira uma linha verde calma, chips, pílulas e cartões zerados ficam neutros (pílula e chip com borda tracejada) e não filtram; o mesmo vale para os totais zerados da página de atrasados.

**The One Meaning Per Color Rule.** Verde é "entregue" e vermelho/âmbar são pendências; o frete não usa verde para "disponível" (usa cartões neutros e selos de texto "Mais barato" e "Mais rápido").

**The Number First Rule.** Em cada cartão de resumo, o número vem antes do rótulo. O rótulo é uma legenda, não o foco.

**The Ramp Rule.** Nenhum texto fica abaixo de 12px, e todo tamanho novo precisa cair num dos seis degraus acima. Valores soltos (como 0.84rem ao lado de 0.85rem) foram eliminados.

## Layout

Coluna central com largura máxima de 1040px e margem de 20px nas laterais de página (12px no mobile). Cabeçalho centralizado com título e meta. No desktop (≥641px), "Consultar Tiny e Correios" e o tema ficam em `.header-tools`; entre 641 e 1099px essas ferramentas sobem para uma linha acima do título. No celular (até 640px) o título ocupa a linha de cima, com 44px de altura para deixar o botão de tema acima da meta, e a meta fica numa linha só, a 12px, sem a palavra "de" (ela fica em `.meta-longo`): "Dados 04/11 15:24 (há 13 min) · próxima em 35 min". A navegação de abas sai do `<header>` e, no celular, fica fixa no topo (ver Navigation). A idade dos dados ("há N min") fica sempre visível. Abaixo de 640px a contagem mostra só os minutos e o horário "(às HH:MM)" fica na versão completa, que o desktop mostra. A meta usa duas versões do mesmo texto, `.meta-longo`/`.meta-curto` e `.contagem-completa`/`.contagem-curta`, escolhidas por CSS. Os cartões de resumo usam grade automática com colunas mínimas de 180px; no mobile (até 640px), uma faixa de 4 colunas com o número acima de um rótulo curto em 0.75rem (`.dashboard` e `.summary`), sem ícone e com 2px de respiro lateral. Controles (busca e filtros) ocupam a largura total. O contador de pedidos (`#filterCount`) fica à direita do campo de busca, na mesma linha (`.search-row`), e não solto entre a legenda e a visão.

A faixa de pílulas nunca quebra linha: rola horizontalmente quando não cabe, em qualquer largura. Em telas estreitas a barra de filtros vira coluna.

Espaçamento observado: 8, 10, 14, 16, 18, 20 e 28–32px entre blocos. No celular, o bloco do cabeçalho (navegação de abas), os cartões de resumo e a busca usam 14px, 16px e 20px, para que o primeiro pedido apareça logo. Não há escala formal de espaçamento no código.

Botão de consulta (Consultar Tiny e Correios): no desktop (≥641px) fica no cabeçalho, em `.header-tools`, ao lado do tema. No celular (até 640px) é um círculo flutuante de 52px no canto inferior direito, com 16px de margem (ver Components).

## Elevation & Depth

Profundidade em camadas leves. Em repouso, cartões usam `--shadow-sm` (sombra mínima). No hover, cartões de resumo sobem 2px e ganham `--shadow-md`. O botão flutuante usa `--shadow-lg` e `--shadow-xl` no hover.

### Shadow Vocabulary
- **Repouso** (`box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05)`): cartões, campos e botões secundários.
- **Hover de cartão** (`box-shadow: 0 4px 6px -1px rgba(0,0,0,0.08), 0 2px 4px -2px rgba(0,0,0,0.05)`): cartões de resumo ao passar o mouse.
- **Cartão de pedido** (`box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1)`): cabeçalho de pedido, com hover de `0 10px 15px -3px rgba(0,0,0,0.1)`.
- **Ação flutuante** (`box-shadow: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.04)`): botão de sincronização.
- **Foco de busca** (`box-shadow: 0 0 0 3px rgba(37,99,235,0.12)`): anel de foco do campo de busca.
- **Brilho da aba ativa**: removido. A aba atual não tem sombra; navegação não é decisão, então não ganha brilho azul. A exceção `dark-glow` foi retirada de `.impeccable/config.json`.

### Named Rules
**The Quiet Lift Rule.** Sombras são resposta a estado. Elementos em repouso não ganham sombra além da mínima; o hover eleva.

## Shapes

Três famílias de forma. Cartões e campos usam cantos de 16px (`--radius-lg`). Blocos internos e caixas de filtro usam 10px. Pílulas (filtros, botões de ação, links de navegação) usam cantos totalmente arredondados. Cartões de pedido usam 12px, e a barra lateral de status (`border-left`) usa 0 8px 8px 0 para destacar estados críticos.

Bordas são sempre finas (1px) em `--color-border`. A exceção é a barra lateral de urgência na tabela de atrasados, que tem 4px.

## Components

### Buttons
- **Shape:** pílula (9999px).
- **Primary (`.btn-action`):** fundo Correio Azul, texto branco, 12px × 22px, peso 700, sombra grande. No desktop fica no cabeçalho; no celular vira círculo flutuante de 52px no canto inferior direito (ver Ferramentas do cabeçalho).
- **Hover / Focus:** hover escurece para Azul Pressionado, sobe 2px e aumenta a sombra. Foco visível com contorno de 2px em azul e deslocamento de 3px.
- **Disabled:** fundo Tinta Sutil, sem sombra e sem movimento.
- **Secondary (`.btn-theme`):** fundo branco, borda fina, texto principal. Hover troca a borda para azul.

### Filter Pills
- **Style:** pílula transparente, borda fina, texto Tinta Discreta, 7px × 14px.
- **State:** ativo com fundo azul e texto branco. Hover mostra borda e texto em azul com fundo Azul Névoa.
- **Layout:** a faixa fica numa linha só em todas as larguras (1280px, 1040px e 375px). Quando não cabe, rola na horizontal; a borda direita esmaece como pista de que há mais pílulas. Ativas vêm primeiro e zeradas no fim. Com Tab, cada pílula rola até ficar visível.

### Cards / Containers
- **Summary card (`.dash-card`, `.summary-card`):** cantos de 16px, fundo branco, borda fina, 18px × 20px. Hover sobe 2px. Estado ativo usa contorno azul de 2px e fundo Azul Névoa. Os quatro cartões (não enviados, em trânsito, entregues, devolvidos) são exclusivos e somam o total de pedidos. O que pede ação fica fora deles, na faixa "Precisam de ação" (`.action-strip`), com botões `.action-chip` para atrasados e aguardando retirada; esses são subconjuntos de "em trânsito" e por isso não entram na soma.
- **Order card (`.order-card`):** cantos de 12px, borda fina, sombra média. Cabeçalho em Cinza Cabeçalho com o título à esquerda e, à direita, o selo do status atual (`.badge`), há quanto tempo foi o último evento e o status do Tiny. Só o último evento fica visível; o restante abre em `<details class="order-history">` ("Ver histórico completo"). A lista é ordenada por urgência: aguardando retirada, atrasados (mais antigos antes), em trânsito, não enviados, devolvidos e entregues. Casos encerrados (entregues e devolvidos sem pendência) ganham `.order-closed`: título em tom discreto, cabeçalho sem fundo e sem tinta no evento, e ficam no fim. Quando a situação do Tiny contradiz os Correios (por exemplo, entregue nos Correios e "Enviado" no Tiny), o cabeçalho mostra o selo amarelo "Tiny desatualizado" (classe `badge-divergencia`), com a explicação na dica. No celular esse selo ocupa a segunda linha do cabeçalho. "Atrasado" conta só pedidos ainda a caminho; devolvidos têm status próprio.
- **Event timeline:** linha vertical de 3px em Borda Fina, bolinha de 12px no início de cada evento. Eventos críticos ganham a cor do status na barra e na bolinha, com fundo levemente tingido. O selo do evento segue o mesmo mapa de cor: POSTADO é azul (`badge-blue`), nunca verde, porque verde é só "entregue". O selo do evento é omitido quando repete o texto do selo do cabeçalho (por exemplo, "Aguardando retirada" aparece uma vez só no cartão).

### Inputs / Fields
- **Search (`.search-input`):** cantos de 16px, borda fina, fundo branco, padding vertical de 14px, ícone de lupa à esquerda em Tinta Sutil. Fica dentro de `.search-row`, ao lado do contador de pedidos.
- **Focus:** borda azul e anel de 3px a 12% de azul.
- **Busca do frete:** a página de opções de frete usa o mesmo campo, na primeira linha da barra de filtros, acima dos filtros de valor. Busca por pedido, cliente, cidade e CEP (com ou sem hífen), sem acento; `/` foca e Esc limpa. Os cartões de serviço têm no máximo 280px, alinhados à esquerda. No celular, entre 360 e 640px, os serviços ficam em 2 colunas (abaixo de 360px, em coluna única). "Menor frete do lote" é link para o cartão do pedido de origem: a página rola até ele e o foco vai junto.
- **Placeholder:** Tinta Sutil. Contraste de placeholder abaixo do recomendado; aceitável apenas por ser texto de apoio.

### Badges
- **Style:** texto em caixa-alta, peso 700, 0.75rem, cantos de 99px. `white-space: nowrap`: o selo nunca quebra por dentro; se não couber na linha do cabeçalho, desce inteiro (`.order-meta` tem `flex-wrap: wrap`).
- **Variants:** vermelho, âmbar, verde, roxo e azul (`badge-blue`, usado em "Em trânsito" e "POSTADO"), cada um com fundo tingido, texto da cor e borda da mesma família.
- **Descrição do status:** no cartão, a explicação do selo fica num `<span class="sr-only">` logo depois dele (texto ": descrição"). O selo não tem `title` nem `aria-describedby`. A busca e a cópia do Status para a tabela usam só o texto visível do selo.

### Toasts
- **Cores:** pelos tokens do tema: `--color-success` (cópia e atualização), `--color-danger` (erro e "Copie manualmente"), `--color-warning` (cooldown) e `--color-primary` por padrão. O texto usa `--console-bg` ou `--console-text`, o que tiver mais contraste sobre o fundo. Pendência: `web/js/dashboard.js` (aviso de motivo da tabela) ainda usa `#b45309` fixo.
- **Sucesso:** `role="status"` e `aria-live="polite"`. A confirmação de cópia some em 2 s; os demais sucessos, em 3,5 s.
- **Erro:** `role="alert"`. Fica aberto até o botão "Fechar" (focável), sem temporizador. Quando a cópia falha nos dois caminhos (Clipboard API e campo oculto), o toast mostra "Copie manualmente: CÓDIGO" com o texto selecionável.
- Foco, hover ou toque seguram o toast; um clique o fecha, exceto quando há texto selecionado.

### Console (SSE)
- **Style:** fundo Tinta Principal (#0f172a), cabeçalho em #1e293b, texto claro em monoespaçada de 0.84rem.
- **Log lines:** borda esquerda de 2px conforme nível (info azul-celeste, sucesso verde, erro vermelho).
- **Traffic lights:** três pontos de 12px (vermelho, amarelo, verde) decorativos no cabeçalho.

### Ícones
- **Style:** SVG de traço fino (1.75px, cantos arredondados), cor herdada do texto (`currentColor`) e 1.1em de tamanho; nos chips de resumo, 1.6rem na cor do status.
- **Theme button:** mostra o ícone do tema de destino (sol no escuro, lua no claro).

### Ferramentas do cabeçalho e da lista
- **Tema:** o botão fica no topo da página (`.header-tools`), à direita no desktop; no celular vira só o ícone de 44px, no canto superior direito, ao lado do título.
- **Visão:** controle segmentado (Cartões, Compacta, Tabela) na linha da lista, à direita, junto de "Opções". Essa linha é uma só em 1280, 1040 e 375px: à esquerda fica o "Limpar filtros" (aparece só com filtro ativo, mas reserva o espaço) e não há título de lista; o contador segue ao lado da busca. No celular os rótulos da Visão ficam um degrau menores e o "Limpar filtros" pode quebrar em duas linhas. O botão ativo usa `aria-pressed` e fica em estado "pressionado" neutro: fundo Cinza Cabeçalho (`--color-surface-hover`), texto Tinta Principal e contorno interno de 1px em `--color-border-strong`, sem azul (o azul de decisão fica no filtro ativo e no botão flutuante). No celular a Tabela fica desativada, com contorno tracejado (sem o anel de "pressionado"), pois não cabe na tela. "Expandir históricos" só aparece com a visão Cartões, em qualquer largura (na Compacta e na Tabela ele fica oculto). "Opções" guarda o seletor de ordem (urgência, último evento mais recente ou mais antigo, número do pedido), o "Recarregar dados salvos" e "Expandir históricos", em grade de rótulo e controle.
- **Atalhos:** a tecla `/` foca a busca e Esc limpa o texto. A legenda "O que significam os status?" também fica em Opções, no topo do menu, para deixar a lista logo abaixo da busca. "Recarregar dados salvos de HH:MM" (em Opções) reconstrói o relatório com os últimos dados já consultados, sem chamar o Tiny nem os Correios; o cabeçalho mostra "Dados consultados em" para deixar claro de quando são os dados.
- **Consultar Tiny e Correios:** consulta as APIs. No desktop (≥641px) fica em `.header-tools`, ao lado do tema; entre 641 e 1099px sobe para a linha acima do título. No celular (até 640px) vira um círculo flutuante de 52px no canto inferior direito, só com o ícone e com `aria-label`.

### Tabela (visão Tabela)
- **Desktop, de 641 a 1023px:** a tabela rola na horizontal dentro do próprio contêiner (`.orders-table-wrap`, `overflow-x: auto`). O cabeçalho não fica fixo.
- **A partir de 1024px:** larguras fixas por coluna (`table-layout: fixed`) e cabeçalho fixo ao rolar a lista. O contêiner não rola na horizontal.
- **Ações:** "Copiar rastreio" é o botão principal da célula, e "Ver cartão" aparece como link (`.btn-ver-cartao`) logo abaixo dele, em qualquer largura de desktop.
- **Celular:** a visão Tabela fica desativada (ver Controles da lista).

### Navigation (`.nav-tabs`)
- **Style:** pílulas com borda fina. Aba atual com estado neutro de "selecionado": superfície mais forte (`--color-surface-hover`), texto principal e sublinhado azul de 2px (`--color-link`) na base. Sem sombra nem brilho; o azul sólido fica reservado ao filtro ativo e ao botão flutuante.
- **Hover:** texto e borda em azul. Na aba atual, o hover mantém o texto principal.
- **Celular (até 640px):** a nav fica fora do `<header>` e é `position: sticky` no topo, com fundo de Cartão Branco (`--color-surface`), 44px de altura e as três abas numa linha só, sem ícones e em 0.8125rem. Ao rolar, o conteúdo some por baixo dela sem transparência. Os alvos de toque têm 44px.

### Controles da lista (`.search-row`, `.list-meta`, `.filters-row`)
- **Desktop:** busca e contador na primeira linha; pílulas de status na segunda; Limpar, visão (Cartões/Compacta/Tabela) e Opções na terceira. Alvos de 40px.
- **Celular (até 640px):** o painel vira uma grade de uma linha só. A busca fica fechada como ícone de 44px, com o contador "N pedidos" ao lado, e a visão (segmentada, 44px) e "Opções" à direita. Ao focar ou ao ter texto, a busca ocupa a linha e visão e Opções saem dela; "Limpar filtros" aparece no lugar. Opções abre como popover sobre a lista, com o seletor de ordem em 44px e 16px (o iOS não amplia a página ao focar).
- **Pílulas:** 44px de altura e 8px de espaço entre elas, em faixa com rolagem horizontal.
- **Faixa de ação (`.action-strip`) no celular:** chips compactos, cada um do tamanho do próprio texto (`flex: 0 1 auto`, `nowrap`). O chip zerado encolhe, e "Aguardando retirada" não quebra em duas linhas.
- **Placeholder:** "Pedido, cliente ou rastreio" no celular (`data-placeholder-curto`, aplicado em `web/js/dashboard.js` por `matchMedia`); no desktop, "Pedido, cliente, rastreio ou cidade" (`data-placeholder-longo`).
- **Primeiro pedido:** medido sem filtros: 360px y=417, 375px y≈419, 412px y=379 (meta de ≤420 em 360 e 375px). A medição de 375px é da 12ª rodada (lote L7); não foi refeita na documentação.
- **Limitação conhecida:** no celular, "Limpar filtros" só aparece com a busca aberta. Com só um filtro de status ativo, a volta é pela pílula "Todos".

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

O modo escuro redefine apenas as superfícies e o texto: fundo `#0b0f19`, cartões `#151c2c`, cabeçalhos `#192237`, borda `#26334d`, texto principal `#f8fafc`, texto discreto `#b6c2d2`. As cores de status usam fundos translúcidos (15% de opacidade) e textos mais claros para manter 4.5:1 sobre as superfícies escuras: verde `#4ade80`, âmbar `#fbbf24`, vermelho `#f87171` e laranja `#fb923c`. Console fica escuro nos dois temas, com tokens próprios (`--console-*`, `--log-*`). O fundo do toast segue a cor de estado do tema (ver Toasts); só o texto usa `--console-*`. Azul Névoa vira `#1e293b`.
