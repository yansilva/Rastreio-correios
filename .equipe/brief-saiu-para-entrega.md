# Brief: status "Saiu para entrega" no painel

Especificação completa no DESIGN.md, seção "Saiu para entrega". Este brief diz quem faz o quê e como aceitar.

Decisões do usuário (não rediscutir): selo no lugar de "Em trânsito"; pílula de filtro própria; a faixa de ação não muda; pedido atrasado que saiu para entrega mostra o selo "Saiu para entrega", continua contando em Atrasados e aparece no filtro Atrasados.

## Decisões do designer

| Item | Decisão |
|---|---|
| a) Cor e classe | Família **verde-azulada (teal)**, classe `badge badge-teal`. Tokens novos `--color-teal-text`, `--color-teal-bg`, `--color-teal-border` (valores abaixo). |
| b) Ícone | Pílula: `i-map-pin`, que já existe em `icons.py` (o frete usa no destino). **Nenhum ícone novo.** Selo: sem ícone, com a bolinha de 6px como todos os selos. |
| c) Textos | Selo e pílula: **"Saiu para entrega"** (sem rótulo curto). `DESCRICAO_STATUS["saiu_para_entrega"]`: **"Objeto com o carteiro, a caminho do destinatário."** |
| d) Atraso visível | Linha de texto `.order-atraso` logo depois do selo: ícone `i-clock` + **"Atrasado · 8 dias · Crítico"**, na cor da escala de urgência, sem fundo. |
| e) Compacta, Tabela e vazio | `STATUS_LABELS.saiu_para_entrega = 'Saiu para entrega'`; `MENSAGENS_VAZIO.saiu_para_entrega = 'Nenhum pedido saiu para entrega.'`. A Tabela mostra a linha de atraso na célula Status, abaixo do selo. |
| f) Legenda | Entra, depois de "Aguardando retirada": **"Saiu para entrega:** {texto_saiu_para_entrega} Se estiver atrasado, o atraso aparece ao lado do selo." |
| g) Filtros em 1440px | **Não cabe numa linha**: com a 9ª pílula (172px), a linha estoura 133px nos 1040px do contêiner. Decisão: de 1100px para cima, os filtros **quebram em duas linhas** (sem rolagem). Até 1099px, continua a rolagem horizontal de hoje. |

### Por que teal
- É o degrau entre o azul (Em trânsito) e o verde (Entregue): o significado é "quase lá", e a cor conta isso.
- O roxo já é do aviso, que aparece junto no mesmo cartão. O índigo ficaria perto do Azul Ação (#2554d9) e pareceria botão. Âmbar, laranja e vermelho são da urgência.
- Para não parecer "Entregue", três coisas: o texto diz o status; o fundo é quase branco (teal-50), e não o pastel cheio do verde; o pedido entregue só fica na lista no dia da entrega, então os dois raramente aparecem lado a lado.

### Por que a linha de atraso, e não o atraso no texto do selo
"Saiu para entrega · 8 dias · Crítico" num selo só misturaria duas cores (teal e vermelho) ou apagaria a urgência. A linha mantém a escala de urgência (texto + nível, WCAG 1.4.1) e deixa o selo dizer só o status, como o usuário pediu. Sem fundo, ela pesa menos que o selo.

## Contrato de dados (backend → HTML)

- `data-status="em_transito saiu_para_entrega"`; atrasado: `"em_transito saiu_para_entrega atrasado"`. **Confirmo a proposta do Coordenador:** a contagem "Em trânsito" do resumo e a pílula "Em trânsito" continuam mostrando esses pedidos.
- `chave_selo`, ordem de precedência: devolvido/entregue → aguardando retirada → **saiu_para_entrega** → atrasado → em_transito → nao_enviado. (Aguardando retirada e Saiu para entrega não coexistem pela regra do evento mais recente; mesmo assim, retirada vence.)
- `ROTULO_SELO["saiu_para_entrega"] = ("Saiu para entrega", "badge-teal")`. O `selo_status` **não** acrescenta dias a esse selo.
- `DESCRICAO_STATUS["saiu_para_entrega"] = "Objeto com o carteiro, a caminho do destinatário."` (vai para `title`, `aria-describedby` e o `.sr-only` do selo).
- Pedido atrasado que saiu para entrega: logo depois do selo e do `.sr-only` dele, dentro de `.order-meta`:
  ```html
  <span class="order-atraso urgencia-alta"><svg class="icon icon-clock" aria-hidden="true" focusable="false"><use href="#i-clock"></use></svg>Atrasado · 8 dias · Crítico</span>
  ```
  Classe e rótulo vêm de `urgencia_atraso(dias)` (`urgencia-alta`/`-media`/`-baixa`; Crítico/Alto/Atenção). Sem atraso, o elemento não existe.
- Ordem da lista: `prioridade()` não muda (atrasado continua 1; senão, em_transito 3). Em `dashboard.js`, **não** acrescente `saiu_para_entrega` a `URGENCIA_STATUS`.
- Pílula, logo depois de "Em trânsito" em `consulta_correios.py`:
  ```html
  <button type="button" class="filter-pill" data-filter="saiu_para_entrega" title="{texto_saiu_para_entrega}" aria-describedby="desc-status-saiu_para_entrega"><svg class="icon icon-map-pin" aria-hidden="true" focusable="false"><use href="#i-map-pin"></use></svg> Saiu para entrega</button>
  ```
- Legenda em Opções: acrescente `<strong>Saiu para entrega:</strong> {texto_saiu_para_entrega} Se estiver atrasado, o atraso aparece ao lado do selo.` depois de "Aguardando retirada".
- A faixa de ação, `faixa_acao` e o resumo não mudam.
- `demo_data.py`: se ele espelha os filtros, acrescente a pílula também (não é obrigatório para o aceite).

## Frontend

1. Tokens em `web/css/main.css` (claro e escuro; os dois são obrigatórios):
   - Claro: `--color-teal-text: #0f766e; --color-teal-bg: #f0fdfa; --color-teal-border: #99f6e4;`
   - Escuro: `--color-teal-text: #2dd4bf; --color-teal-bg: rgba(20, 184, 166, .15); --color-teal-border: rgba(45, 212, 191, .35);`
2. `.badge-teal` em `components.css`, no mesmo molde de `.badge-blue`: fundo, texto e borda de 1px dos tokens teal.
3. `.order-atraso`:
   - `display: inline-flex; align-items: center; gap: 4px`; 13px, peso 500, `tabular-nums`; sem fundo, sem borda; ícone de 14px na cor do texto.
   - Cor: `.urgencia-alta` → `--color-danger`; `.urgencia-media` → `--color-high-text`; `.urgencia-baixa` → `--color-warning-text`.
   - Celular (≤640px), na grade de `.order-meta`: linha própria abaixo do selo (`grid-column: 1 / -1; grid-row: 2; justify-self: start`). Quando houver também "Tiny desatualizado", ele desce para a linha 3.
4. JS (`web/js/dashboard.js`):
   - `STATUS_LABELS.saiu_para_entrega = 'Saiu para entrega'`.
   - `MENSAGENS_VAZIO.saiu_para_entrega = 'Nenhum pedido saiu para entrega.'`.
   - Acrescente `'saiu_para_entrega'` a `statusValidos` (filtro lembrado no `sessionStorage`).
   - Tabela: `linhasDaTabela` lê também `textoDe(card.querySelector('.order-atraso'))`; a célula Status mostra o selo e, abaixo, o texto de atraso com a mesma classe `order-atraso urgencia-*`. Não troque o selo pelo atraso.
   - Compacta: a `.order-atraso` continua visível (fica no `.order-meta`).
   - Contagem e reordenação da pílula: as mesmas dos outros filtros (zerada vai para o fim, tracejada).
5. Filtros de 1100px para cima (`.filter-pills`):
   - `flex-wrap: wrap; row-gap: 8px; overflow-x: visible`; sem o espaço e o esmaecimento da rolagem (`padding-right` igual ao da esquerda; a `.tem-rolagem` não se aplica).
   - Até 1099px, nada muda: uma linha com rolagem horizontal.

## Critérios de aceite

- [ ] Um pedido com o último evento "Objeto saiu para entrega ao destinatário" mostra o selo teal "Saiu para entrega" nos dois temas, em 1440, 1024, 375 e 360px, sem rolagem horizontal da página.
- [ ] Um evento posterior (por exemplo, "carteiro não atendido") devolve o selo "Em trânsito" (ou o de atraso). Um aviso de `AVISOS_CORREIOS` depois do "saiu" **não** desfaz o status.
- [ ] Contraste do selo: pelo menos 5,2:1 no claro e 6,7:1 no escuro (Superfície e Superfície 2), medido com a composição do alfa.
- [ ] O selo não usa azul nem verde: a cor computada é da família teal nos dois temas.
- [ ] Pedido atrasado que saiu para entrega: selo "Saiu para entrega" + linha "Atrasado · N dias · Nível" na cor da escala; conta em Atrasados (faixa e pílula) e aparece nos filtros Atrasados, Em trânsito e Saiu para entrega.
- [ ] Pílula "Saiu para entrega" logo depois de "Em trânsito" (quando não estiver zerada), com `i-map-pin` e contador; zerada, fica tracejada no fim e não filtra; ativa sem resultado mostra "Nenhum pedido saiu para entrega."
- [ ] Em 1440px, **nenhuma rolagem nos filtros**: `.filter-pills` com `scrollWidth <= clientWidth`; as pílulas quebram em duas linhas. Em 1024px, continuam numa linha com rolagem.
- [ ] Compacta e Tabela: o selo "Saiu para entrega" e, quando atrasado, o texto de atraso abaixo dele.
- [ ] Contagem "Em trânsito" do resumo igual à de antes da mudança.
- [ ] Legenda "O que significam os status?" com a linha de "Saiu para entrega".
- [ ] Busca por "saiu para entrega" não depende do `.sr-only`; o texto visível do selo basta.
