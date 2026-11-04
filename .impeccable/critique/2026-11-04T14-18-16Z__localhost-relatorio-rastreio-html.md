---
target: painel de rastreio, oitava rodada (com atrasados e frete)
total_score: 27
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 2
target_identity: "url:http://localhost:8000/relatorio_rastreio.html"
timestamp: 2026-11-04T14-18-16Z
slug: localhost-relatorio-rastreio-html
---
# Critique — painel de rastreio (oitava rodada, com atrasados e frete)

Method: dual-agent. Nota 27/40 (Nielsen: 3,3,3,2,3,3,3,2,3,2). Detector: 11 achados, todos avisos ou falsos positivos (Inter, selos fora do DESIGN.md, side-tab neutro, Sfmono-Regular). Medições: 0 falhas de contraste, 0 overflow, 0 erros de console; em 1280px as pílulas quebram em duas linhas.

## Prioridades
- [P1] Cartões de resumo e pílulas filtram os mesmos eixos. Comando: distill.
- [P1] Pílulas zeradas: a útil fica fora da tela no celular e Devolvidos 0 quebra no desktop. Ativas primeiro. Comando: layout.
- [P2] Celular: botão flutuante cobre Copiar rastreio; primeiro pedido em y=653. Comando: adapt.
- [P2] Atrasados e frete sem busca, ordenação e copiar rastreio; vazio com quatro zeros; sem skip link nem main; frete com Indisponível repetido. Comando: distill, polish.
- [P3] Foco vai ao body ao fechar o popover com Esc; pílulas desativadas recebem Tab; th-sort Tiny 34x40; matchMedia só na carga.

## Personas
Alex: mais de 20 Tabs até o primeiro pedido. Sam: pílulas aria-disabled com tabindex 0. Casey: primeiro pedido em y=653 e botão flutuante cobrindo a ação.
