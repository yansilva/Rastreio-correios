---
target: "painel de rastreio, segunda rodada (localhost:8000/relatorio_rastreio.html)"
total_score: 25
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 2
target_identity: "url:http://localhost:8000/relatorio_rastreio.html"
timestamp: 2026-10-16T23-28-48Z
slug: localhost-relatorio-rastreio-html
---
# Critique: painel de rastreio, segunda rodada (localhost:8000/relatorio_rastreio.html)

Method: DEGRADED single-context (sem sub-agentes; detector já visto em rodadas anteriores). Relatório real de 19:59 com 7 pedidos, em 1280px (escuro) e 375px (claro). O HTML tem o P1 (selo, histórico recolhido, cartão Atrasados); o P2 (ícones, legenda) só aparece após novo Atualizar Dados.

## Design Health Score

| # | Heurística | Nota | Problema principal |
|---|---|---|---|
| 1 | Visibilidade do status | 3 | Selo e idade no cabeçalho; falta destacar Tiny x Correios |
| 2 | Linguagem do usuário | 2 | "Atrasados 4" são os mesmos 4 de "Devolvidos 4" |
| 3 | Controle e liberdade | 3 | Limpar filtros, banner, cooldown |
| 4 | Consistência | 3 | Ícones e nomes novos ainda fora do HTML gerado |
| 5 | Prevenção de erros | 3 | Cooldown e botão desabilitado |
| 6 | Reconhecimento | 3 | Status se lê no cabeçalho |
| 7 | Flexibilidade | 2 | Sem ordenação, atalho nem recolher tudo |
| 8 | Estética e minimalismo | 3 | 5 de 7 cartões são casos encerrados |
| 9 | Recuperação de erros | 2 | Falhas aparecem, texto genérico |
| 10 | Ajuda | 1 | Legenda só no código, não na página atual |
| Total | | 25/40 | Aceitável (anterior 24/40) |

## Veredito de especificidade
Ganho de especificidade veio da informação (selo, idade, ordem por urgência); a superfície segue genérica de SaaS. Detector: side-tab x1 (falso positivo), overused-font x1 (Inter não carregada), 36 avisos consultivos de desvio do DESIGN.md.

## Problemas prioritários
- [P1] "Atrasados" inclui devolvidos e duplica "Devolvidos" (data-status "devolvido atrasado"); atraso real em trânsito é zero. Comandos: harden, clarify.
- [P1] A regra que oculta casos encerrados não vale na tela (applyFilters reexibe); 5 de 7 cartões são encerrados e devolvidos ficam acima de em trânsito. Comando: harden.
- [P2] Botões flutuantes cobrem conteúdo no celular e vêm primeiro na ordem de teclado. Comandos: layout, adapt.
- [P2] Sem recolher/expandir tudo, ordenação nem atalho de busca. Comando: layout.
- [P3] Divergência Tiny x Correios (Tiny "Não entregue" com Devolvido) aparece como texto cinza. Comando: clarify.

## Personas
Marina: alarme vermelho leva a 4 devoluções antigas e perde a confiança. Alex: sem ordenação nem atalho. Casey: botões flutuantes cobrem "Ver histórico completo".

## Minhas observações
Barra de rolagem horizontal visível na faixa de filtros no celular; ícones e legenda só após regenerar.

## Perguntas
Devolvido concluído deveria ter seção própria? O vermelho deveria significar só ação imediata? A primeira tela poderia mostrar só o que está ativo?
