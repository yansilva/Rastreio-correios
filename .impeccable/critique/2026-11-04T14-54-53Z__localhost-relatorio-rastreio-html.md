---
target: painel de rastreio, nona rodada (painel, atrasados e frete)
total_score: 28
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 1
target_identity: "url:http://localhost:8000/relatorio_rastreio.html"
timestamp: 2026-11-04T14-54-53Z
slug: localhost-relatorio-rastreio-html
---
# Critique — painel de rastreio (nona rodada, painel, atrasados e frete)

Method: dual-agent. Nota 28/40 (Nielsen: 3,3,3,2,3,2,3,3,3,3). Detector: 12 achados (Inter, selos fora do DESIGN.md, side-tab neutro, mono de reserva, 22 travessões no frete). Medições: 0 overflow, 0 erros de console, 0 falhas de contraste, Inter carrega nas três páginas, skip link primeiro foco nas três, pílulas numa linha em 1280px, primeiro pedido em y=576 no celular.

## Prioridades
- [P1] Tabela de atrasados com 10 colunas não cabe em 1280px; Copiar rastreio cortado; Dias, Urgência e cor redundantes; celular uma tela por pedido. Comando: adapt, layout.
- [P2] Frete sem busca; serviço único esticado; selo Em aberto repetido. Comando: layout, distill.
- [P2] Painel: visões escondidas em Opções; botão flutuante cobre ações da tabela; Ver cartão grava preferência. Comando: layout, polish.
- [P3] Título do cartão sem hierarquia; Limpar filtros pula 30px; toast com emoji e verde a 3,3:1; num-total a 3,29:1 no escuro; código morto. Comando: typeset, polish.

Ambiente: o prazo "—" do frete vinha do script de regeneração da sessão (regex de "dia útil"); corrigido e página regenerada.
