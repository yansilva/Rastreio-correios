---
target: painel de rastreio, sexta rodada (com opcoes_frete)
total_score: 28
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 1
target_identity: "url:http://localhost:8000/relatorio_rastreio.html"
timestamp: 2026-10-28T20-12-30Z
slug: localhost-relatorio-rastreio-html
---
# Critique — painel de rastreio (sexta rodada, com opcoes_frete.html)

Method: dual-agent. Nota 28/40 (Nielsen: 3,3,3,2,3,3,3,3,3,2). Detector: 14 achados (eram 34): selos fora do DESIGN.md (avisos), Inter, font-size 3rem no frete, side-tab neutro, Sfmono-Regular. Medições: 0 erros de console, 0 overflow, 0 falhas de contraste em 12 cenários.

## Prioridades
- [P1] Tabela perde o foco ao ordenar (activeElement vira body) e é ruim no celular (418px por pedido, sem ordenação). Comando: harden, adapt.
- [P2] Dois sistemas de filtro (cartões e pílulas); cartão com contagem 0 esvazia a lista; Title Case nas pílulas. Comando: distill, clarify.
- [P2] Opções de Frete destoa do painel: h1 36px, sem abas, "1 dias úteis", verde para disponível, Indisponível sem motivo, filtro vazio mudo, primeiro pedido na dobra no celular. Comando: polish, clarify, adapt.
- [P3] Acessibilidade fina: Ver cartão sem nome, ordenação por Status alfabética, alvos de 32 a 36px. Comando: harden.
- [P3] DESIGN.md diverge do código. Comando: document.

## Personas
Alex: ordenar perde o foco. Sam: Ver cartão repetido sem nome. Casey: tabela mobile gigante.
