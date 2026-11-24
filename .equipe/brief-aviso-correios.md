# Brief: Aviso dos Correios no painel

A especificação completa está no DESIGN.md, na seção "Aviso dos Correios". Este brief diz quem faz o quê e como aceitar.

## Contrato de dados (backend → HTML)

No cartão do pedido com aviso, e enquanto ele não foi entregue nem devolvido:

- `data-aviso="1"` no `.order-card`;
- o token `com_aviso` somado ao `data-status`, por exemplo `data-status="em_transito com_aviso"`. Com isso, o filtro funciona pelo `applyFilters` que já existe, sem lógica nova;
- logo depois do `.order-header`, este elemento:
  ```html
  <p class="order-aviso">
    <svg class="icon icon-info" aria-hidden="true" focusable="false"><use href="#i-info"></use></svg>
    <strong>Aviso dos Correios</strong> <span class="order-aviso-texto">TEXTO DO EVENTO</span>
    <time class="order-aviso-data">22/11</time>  <!-- opcional -->
  </p>
  ```
- o símbolo `i-info` em `Arquivos/correios/icons.py` (círculo com "i", traço de 2px como os outros);
- `faixa_acao(atrasados, retiradas, avisos)` em `cards.py`:
  - o chip de aviso só aparece com `avisos > 0`;
  - a linha calma só aparece quando os três são zero;
- o filtro `com_aviso` na lista de filtros de `consulta_correios.py`, logo depois de "Aguardando retirada".

## Frontend (CSS em `web/css/components.css`, JS em `web/js/dashboard.js`)

1. `.order-aviso`:
   - caixa: fundo `var(--color-purple-bg)`, borda `1px solid var(--color-purple-border)`, `border-radius: var(--radius-sm)`, `padding: 8px 12px`, `margin: 8px 12px 0`;
   - `display: flex; gap: 8px; align-items: flex-start`, para o ícone ficar na primeira linha;
   - texto em `var(--color-purple-text)`, 13px; `strong` em peso 600; quebra normal, sem `text-overflow`;
   - `.order-aviso-data` em Secondary e `tabular-nums`;
   - nada de valor fixo de cor: o tema escuro vem dos tokens.
2. `.action-chip[data-filter="com_aviso"]`: **substituído na 17ª crítica.** Agora vale o DESIGN.md, seção "Faixa de ação": chip contornado, roxo só no ícone e no número, fundo roxo só quando ativo, `title` "Pedidos ainda não entregues com aviso dos Correios".
3. `.filter-pill[data-filter="com_aviso"]`: nenhum CSS novo; o estilo é o mesmo dos outros filtros.
4. JS:
   - `STATUS_LABELS.com_aviso = 'Com aviso'`;
   - `MENSAGENS_VAZIO.com_aviso = 'Nenhum pedido em aberto com aviso dos Correios.'`;
   - contagem do `.pill-count` e reordenação (zerado no fim) como nos outros filtros.
5. Visões Compacta e Tabela: o cartão com `data-aviso="1"` ganha, depois do selo de status:
   - `<span class="badge badge-purple badge-aviso" title="TEXTO">Aviso</span>`;
   - `<span class="sr-only">Aviso dos Correios: TEXTO</span>`.

   O TEXTO vem do `.order-aviso-texto`. Na Compacta, a linha `.order-aviso` fica oculta.

## Critérios de aceite

- [ ] O pedido 43312 mostra o selo do status real (por exemplo, "Em trânsito") e a linha "Aviso dos Correios" com o texto inteiro, em 1440, 1024, 375 e 360px, sem rolagem horizontal.
- [ ] Nenhum âmbar, laranja ou vermelho na linha, no chip ou no selo de aviso. A cor computada é a da família roxa nos dois temas.
- [ ] Contraste do texto: pelo menos 5,9:1 no claro e 5,4:1 no escuro (Superfície 2 incluída).
- [ ] Faixa: com aviso, aparece o chip "N Com aviso", e clicar nele filtra (`aria-pressed="true"`). Sem aviso, o chip não existe. Com zero atraso, zero retirada e zero aviso, aparece a linha calma.
- [ ] Filtro "Com aviso": mostra só os cartões com `com_aviso`. Zerado, fica tracejado e não filtra. Ativo sem resultado (por busca), mostra o estado vazio com o texto definido.
- [ ] A busca acha o pedido pelo texto do aviso ("mais tempo"). A linha não é `.sr-only`, então a busca a enxerga.
- [ ] Pedido entregue ou devolvido nunca mostra o aviso.
- [ ] Na Tabela e na Compacta: o selo "Aviso" com `title` e `.sr-only`; o celular sem Tabela continua igual.
- [ ] Com `prefers-reduced-motion`, nada novo se move.
