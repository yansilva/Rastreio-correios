# Lições do designer — Rastreio-correios

- 2026-11-13 · Recarregar com `location.reload()` dentro do script de medida corta o script e pode medir a página sem CSS. Use `navigate` e meça numa chamada separada.
- 2026-11-13 · No celular, conferir 360px além de 375: o `overflow-wrap: anywhere` dos rótulos só quebra palavra no meio em 360.
- 2026-11-13 · O frete tem CSS próprio em `Arquivos/frete/report.py`; regras do tema escuro lá podem vencer as do celular por especificidade. Testar o frete no celular escuro sempre.
- 2026-11-13 · Página nova que reusa `.table-wrapper` precisa marcar `.col-secundaria`, senão o cartão do celular mostra todos os campos.
