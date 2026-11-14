# Lições do designer — Rastreio-correios

- 2026-11-13 · Recarregar com `location.reload()` dentro do script de medida corta o script e pode medir a página sem CSS. Use `navigate` e meça numa chamada separada.
- 2026-11-13 · No celular, conferir 360px além de 375: o `overflow-wrap: anywhere` dos rótulos só quebra palavra no meio em 360.
- 2026-11-13 · O frete tem CSS próprio em `Arquivos/frete/report.py`; regras do tema escuro lá podem vencer as do celular por especificidade. Testar o frete no celular escuro sempre.
- 2026-11-13 · Página nova que reusa `.table-wrapper` precisa marcar `.col-secundaria`, senão o cartão do celular mostra todos os campos.
- 2026-11-13 · Cópia temporária do frete: gere com `FreteReportGenerator` + `mock_open` (o `gerar_html` grava na raiz se não houver mock) e sirva noutra porta com `web/fonts` copiado. Nessa origem a emulação de 375px deu `scrollWidth` 586 mesmo com a página oculta; conferir largura na página real antes de acusar estouro.
- 2026-11-13 · Comparar o mesmo pedido entre páginas (cor do selo, hora "Dados de"): as incoerências de significado só aparecem quando há dado real nas duas páginas.
- 2026-11-13 · `localStorage` do 8000 pode ter estado de outra sessão (ex.: `painel.visao`); anotar o valor inicial antes de mexer e restaurar exatamente ele.
