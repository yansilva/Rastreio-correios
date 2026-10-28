---
target: painel de rastreio, sétima rodada (com atrasados e frete)
total_score: 27
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 2
target_identity: "url:http://localhost:8000/relatorio_rastreio.html"
timestamp: 2026-10-28T21-20-35Z
slug: localhost-relatorio-rastreio-html
---
# Critique — painel de rastreio (sétima rodada, com atrasados e frete)

Method: dual-agent. Nota 27/40 (Nielsen: 3,3,3,2,3,3,3,2,2,3). Detector: 17 achados (font-size 2.25rem e 3rem fora da rampa; Inter, selos e side-tab neutro são falsos positivos). Medições: sem overflow, uma falha de contraste (contagem da pílula ativa, 3,49:1).

## Prioridades
- [P1] Contagem da pílula ativa a 3,49:1. Comando: polish.
- [P1] Pílulas e chips zerados filtram e abrem lista vazia. Comando: harden.
- [P2] Estado vazio da tabela sem termo nem saída. Comando: harden.
- [P2] Topo pesado: banner Filtro ativo repete a pílula; pílulas quebram em duas linhas. Comando: distill.
- [P2] Select Ordenar por e cabeçalhos da tabela descoordenados. Comando: clarify.
- [P3] Cabeçalho da tabela sem sticky; Esc do popover; carregando visível; nomes do painel; números zerados coloridos em Atrasados; formatação do pacote e CEP no frete; alvos de 36 a 38px.

Ambiente: o servidor com código antigo reescreveu opcoes_frete.html no formato velho; reiniciado e regenerado.
