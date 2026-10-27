---
target: painel de rastreio, quinta rodada (dados ao vivo)
total_score: 27
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 2
target_identity: "url:http://localhost:8000/relatorio_rastreio.html"
timestamp: 2026-10-27T21-47-02Z
slug: localhost-relatorio-rastreio-html
---
# Critique — painel de rastreio (quinta rodada, dados ao vivo)

Method: dual-agent. Nota 27/40 (Nielsen: 3,3,3,2,3,3,3,3,2,2). Detector: 34 achados (tight-leading x7, side-tab x1, overused-font, nested-cards x2 no overlay, selos fora do DESIGN.md como aviso).

## Prioridades
- [P1] Zero-state com cara de alarme: faixa "Precisam de ação" e chips vermelhos com 0/0; filtro vazio mostra texto de erro. Comando: clarify, harden.
- [P1] Mobile: primeiro pedido em y~1088; placeholder cortado; barra de rolagem grossa; summary de 36px. Comando: adapt, layout.
- [P2] Três mecanismos de filtro e duas saídas; falta aria-pressed. Comando: distill, harden.
- [P2] Cartões sem hierarquia nem semântica (.order-title é div; cabeçalho variável; cidade no meio da frase). Comando: typeset, layout.
- [P3] Contraste no limite (azul/roxo grande no escuro 3,2 a 3,7:1; .filter-count 4,55) e transição de tema lenta. Comando: colorize, polish.

## Personas
Alex: sem ação por pedido nem visão compacta. Sam: sem skip link, sem aria-pressed, busca sem anel de 2px, a.nav-tab com anel do navegador. Casey: pedido só após 1090px, FAB cobre cartões, alvos de 36px.

## Observações
Opções empurra a lista; H1 azul compete com números; cartões de resumo em quatro cores; Inter declarada e não carregada; tight-leading 1,28x.
