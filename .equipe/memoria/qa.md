# Memória do qa — Rastreio-correios

- 2026-11-12 · Ao validar testes do servidor, confira se dependem de arquivo gerado na raiz (ex.: `entregues_semana.html`). Para provar, copie o repositório para uma pasta temporária, apague os HTML gerados e rode o teste.
- 2026-11-12 · Os HTML da raiz (`opcoes_frete.html`, etc.) podem estar antigos depois de uma mudança de menu. Confira a data de geração antes de medir a navegação.
- 2026-11-12 · `Arquivos/entregas_historico.json` tem nomes de clientes. Só verifique a existência e nunca leia o conteúdo.
- 2026-11-12 · Ao testar a cópia do texto no navegador embutido, o clique real (ref) funciona. O JavaScript sem foco cai no aviso "Copie manualmente".
- 2026-11-12 · Em 1280px o navegador embutido tem barra de rolagem de ~15px: `innerWidth` dá 1280, mas a área visível é 1265 (`clientWidth`). Meça overflow contra `document.documentElement.clientWidth`, não contra `innerWidth`.
- 2026-11-12 · Overflow medido com `getBoundingClientRect` dentro de containers com `overflow-x: auto` (ex.: `.filter-pills.tem-rolagem`) não é overflow da página. Confira `scrollWidth` do documento antes de reprovar.
- 2026-11-13 · Para testar concorrência em fila, rode várias threads com `put` numa fila cheia (`maxsize` pequeno). Um teste de uma thread só não mostra `queue.Full`.
- 2026-11-13 · Scripts de QA com `print` de texto em português quebram no console do Windows (cp1252). Use `ascii()` ou escreva em arquivo UTF-8.
