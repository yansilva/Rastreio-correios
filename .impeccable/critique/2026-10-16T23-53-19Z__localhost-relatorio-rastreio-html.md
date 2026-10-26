---
target: painel de rastreio, quarta rodada (template real com cache sintético)
total_score: 29
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 1
target_identity: "url:http://localhost:8000/relatorio_rastreio.html"
timestamp: 2026-10-16T23-53-19Z
slug: localhost-relatorio-rastreio-html
---
# Critique: painel de rastreio, quarta rodada (template real com cache sintético)

Method: DEGRADED single-context (sem sub-agentes; detector já visto em rodadas anteriores). Alvo: template real renderizado com cache sintético numa pasta temporária, 1280px escuro e 375px claro. O relatório servido em localhost:8000 segue o de 19:59 (sem cache nem melhorias de hoje).

## Design Health Score

| # | Heurística | Nota | Problema principal |
|---|---|---|---|
| 1 | Visibilidade do status | 3 | Não avisa quando os dados estão velhos |
| 2 | Linguagem do usuário | 3 | "Regerar página" é jargão |
| 3 | Controle e liberdade | 3 | Ordenar, expandir tudo, regerar sem rede |
| 4 | Consistência | 3 | Atrasados é subconjunto de Em trânsito, mas é cartão irmão |
| 5 | Prevenção de erros | 3 | Cooldown e travas |
| 6 | Reconhecimento | 3 | Selo, idade e legenda |
| 7 | Flexibilidade | 3 | Ordenação e expansão se perdem ao atualizar |
| 8 | Estética e minimalismo | 3 | Meta do cabeçalho junta três horários |
| 9 | Recuperação de erros | 3 | 409 com a causa; falha de atualização aparece |
| 10 | Ajuda | 2 | Atualizar x Regerar só em dica |
| Total | | 29/40 | Bom (anteriores 24, 25, 28) |

## Veredito de especificidade
Linguagem do produto (Aguardando retirada, Atrasado, Tiny desatualizado, Dados consultados em); superfície sóbria. Detector: side-tab x1 (falso positivo), overused-font x1, 40 avisos consultivos de desvio do DESIGN.md.

## Problemas prioritários
- [P1] Cartões de resumo não somam (7 para 6 pedidos): Atrasados e retirada estão dentro de Em trânsito. Comandos: layout, clarify.
- [P2] "Regerar página" e "Atualizar Dados" parecem iguais; explicação só em dica. Comando: clarify.
- [P2] Meta do cabeçalho com três horários quebra em até 4 linhas no celular. Comandos: distill, layout.
- [P2] Pendências anteriores: retirada em vermelho (âmbar aprovado), tipografia pequena, Inter não carregada. Comandos: colorize, typeset.
- [P3] Ordenação e expansão se perdem ao atualizar. Comando: harden.

## Personas
Marina: soma 7 para 6 e desconfia. Alex: perde a ordenação ao atualizar e confunde Regerar com Atualizar. Casey: meta com 4 linhas antes dos números.

## Observações menores
Relatório real sem as melhorias até um Atualizar Dados; página de atrasados com tema antigo; report.py com CSS e emojis próprios.

## Perguntas
Que números a faixa deveria somar? Precisa de botão só para o cache? Para que serve "gerado em"?
