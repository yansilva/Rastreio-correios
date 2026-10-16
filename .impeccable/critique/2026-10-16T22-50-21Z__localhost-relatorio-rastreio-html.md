---
target: "painel de rastreio (localhost:8000/relatorio_rastreio.html)"
total_score: 24
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 2
target_identity: "url:http://localhost:8000/relatorio_rastreio.html"
timestamp: 2026-10-16T22-50-21Z
slug: localhost-relatorio-rastreio-html
---
# Critique: painel de rastreio (localhost:8000/relatorio_rastreio.html)

Method: DEGRADED single-context (sem sub-agentes: exigem pedido explícito nesta sessão; detector já visto em rodadas anteriores). Revisão visual em 1280px (claro e escuro) e 375px (claro), 7 pedidos reais.

## Design Health Score

| # | Heurística | Nota | Problema principal |
|---|---|---|---|
| 1 | Visibilidade do status | 3 | Cartão do pedido sem status atual no cabeçalho |
| 2 | Linguagem do usuário | 3 | "Status Tiny" é jargão; "Retirada" vs "Aguardando retirada" |
| 3 | Controle e liberdade | 3 | Limpar filtros e banner ajudam |
| 4 | Consistência | 3 | "Atrasados" é aba e filtro com significados diferentes |
| 5 | Prevenção de erros | 3 | Cooldown e botão desabilitado |
| 6 | Reconhecimento | 2 | Status só aparece lendo a timeline |
| 7 | Flexibilidade | 2 | Sem ordenação, atalhos nem recolher tudo |
| 8 | Estética e minimalismo | 2 | 110 eventos expandidos; emoji como ícones |
| 9 | Recuperação de erros | 2 | Falha aparece, mas com texto genérico |
| 10 | Ajuda | 1 | Nada explica o critério de atrasado |
| Total | | 24/40 | Aceitável |

## Veredito de especificidade
Conteúdo do produto, linguagem visual genérica de painel SaaS. Detector: side-tab x1 (falso positivo, trilho da timeline), overused-font x1 (Inter, nunca carregado), 33 avisos consultivos de desvio do DESIGN.md.

## Problemas prioritários
- [P1] Overflow horizontal no celular: scrollWidth 683 em viewport de 375; contador "7 pedidos" cortado. Comando: adapt.
- [P1] Tarefa principal enterrada: sem "Atrasados" nos cartões de resumo, sem selo de status no cabeçalho, timelines expandidas (14.901px no celular). Comandos: layout, distill.
- [P2] Emoji como sistema de ícones. Comando: polish.
- [P2] Inter declarado mas não carregado. Comando: typeset.
- [P2] Sem ajuda sobre o critério de atrasado nem diferença entre aba e filtro. Comando: clarify.

## Personas
Marina (operadora): precisa achar parados em 5s e precisa ler timelines. Alex: sem atalho para busca, ordenação ou recolher tudo. Casey: overflow lateral, FABs sobre o conteúdo, faixa de filtros com barra de rolagem grossa.

## Observações menores
Meta do cabeçalho quebra com "|" solto; datas sem tempo relativo; botão de tema mostra o modo de destino; placeholder da busca corta no celular.

## Perguntas
A primeira tela poderia responder só "o que precisa de mim hoje?". Um pedido em trânsito precisa mostrar a timeline inteira? A ordem padrão deveria ser por urgência?
