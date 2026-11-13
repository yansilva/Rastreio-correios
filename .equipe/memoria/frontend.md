# Memória do frontend — Rastreio-correios

- 2026-11-12 · Seletor com `aria-pressed` precisa de JS externo (`web/js/entregues.js`). Painéis escondidos com `hidden` só somem se o CSS não sobrescrever `display`: `.summary` é `display: grid`, então a regra `.entregues-painel[hidden] { display: none }` vem no bloco da página.
- 2026-11-12 · Página nova no menu: a aba entra nos `<nav>` de `consulta_correios.py` (painel e atrasados), `demo_data.py` (painel e atrasados) e `frete/report.py`. Atrasados não estava no nav do frete: não acrescentei, só Entregues.
- 2026-11-12 · Teste de servidor: não depender de arquivo da raiz. Usar `ServerConfig(base_dir=<pasta temporária>)` com um HTML mínimo gravado nela, e restaurar `RastreioRequestHandler.server_config` com `addCleanup` (corrigido a pedido do coordenador).
- 2026-11-12 · Botão de tema: sem `aria-label`. O nome acessível é o texto visível "Escuro"/"Claro" (WCAG 2.5.3). Vale para todos os templates e para `web/js/app.js` (`setTheme` só troca o texto).
- 2026-11-12 · Tabela que vira `display:block` no celular perde a semântica no Safari/VoiceOver. Pôr `role` explícito em table, rowgroup, row, columnheader e cell.
- 2026-11-12 · `regera_frete.py` (scratchpad da sessão de origem) lia o destino com separador "—", mas a página usa "·" ("Cidade/UF · CEP 00000-000"). Destinos saíam como "—". Versão corrigida em `scratchpad\regera_frete_corrigido.py`. Antes de regerar o frete com esse método, confira `CEP-matches` na página nova.
- 2026-11-12 · Para ver tabela e cartões com dados no navegador, gere uma página de teste na raiz e apague depois. Não deixe no repositório.
- 2026-11-12 · Cabeçalho do painel: o nav de 4 abas cabe em 375px (somadas, ~334px). Confira de novo se mudar o texto das abas.
- 2026-11-13 · Menu de abas: a fonte única é `nav_html(ativa, atrasados=None)` em `Arquivos/correios/navegacao.py`. Não copie `<nav>` em página nova. Atrasados aparece sempre; o número só com valor > 0 e só nas páginas que recebem a contagem (painel, atrasados, entregues e demo; frete não recebe).
- 2026-11-13 · Nos testes de menu, procure `<a href="..."` e não só `href="..."`: o `href` do `<use>` dos ícones também casa.
- 2026-11-13 · `frete/report.py` ainda tem o CSS do `.nav-tabs` copiado do painel (a página não carrega `main.css`). Se o menu mudar de estilo, mude nos dois lugares.
