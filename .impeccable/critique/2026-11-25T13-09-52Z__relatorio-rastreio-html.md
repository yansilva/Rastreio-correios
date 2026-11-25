---
target: painel relatorio_rastreio.html (18a critica)
total_score: 30
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 1
target_identity: "file:C:\\Users\\yansa\\Yan\\Rastreio-correios\\relatorio_rastreio.html"
target_fingerprint: "sha256:8eb80173f51df5ecfdb8045ea4f24403909885f80a550c20c96a219fef422203"
target_path: "C:\\Users\\yansa\\Yan\\Rastreio-correios\\relatorio_rastreio.html"
timestamp: 2026-11-25T13-09-52Z
slug: relatorio-rastreio-html
---
⚠️ DEGRADED: single-context (o papel de designer não delega a subagentes; A e B rodaram em sequência)

# 18ª crítica — relatorio_rastreio.html (commit 3f24bb8)

## Nota
| # | Heurística | Nota | Ponto-chave |
|---|---|---|---|
| 1 | Visibilidade do estado | 2 | 43249 é atraso Crítico (7 dias) e o cartão só diz "Aguardando retirada" e "Último evento há 2 dias" |
| 2 | Linguagem do mundo real | 4 | "Saiu para entrega" é o termo dos Correios; o detalhe "É preciso ter alguém no endereço" ajuda |
| 3 | Controle e liberdade | 3 | Limpar filtros, Esc, filtro lembrado |
| 4 | Consistência | 3 | Atrasados mostra "7 dias · Crítico" e o Painel não; aba Atrasados sem contador no Frete |
| 5 | Prevenção de erro | 3 | — |
| 6 | Reconhecimento | 3 | Filtros zerados escondidos pela rolagem em 1024 |
| 7 | Eficiência | 3 | Atalho /, visões, ordenação |
| 8 | Estética e minimalismo | 3 | Duas linhas de filtros com as zeradas embaixo funcionam bem |
| 9 | Recuperação de erro | 3 | — |
| 10 | Ajuda | 3 | Legenda com "Saiu para entrega" |
| **Total** | | **30/40** | Bom |

## Especificidade
O status novo fala a língua do operador e ocupa um degrau de cor que conta "quase lá". Detector: 10 achados; 2 reais de documentação (teal fora do frontmatter do DESIGN.md), o resto falso positivo (cidades repetidas no histórico, padding de `.table-wrapper`, tamanhos do frete sobrescritos: computado 24/24/20/16px).

## Achados
- **[P1] Retirada atrasada sem atraso no cartão.** 43249 (`data-status="aguardando_retirada atrasado"`, 7 dias, Crítico na aba Atrasados) mostra só "Aguardando retirada" no Cartão, na Compacta e na Tabela. Quem clica no chip "1 Atrasados" chega a um cartão sem atraso. Correção: a linha `.order-atraso` (já implementada para "Saiu para entrega") passa a valer sempre que o pedido está atrasado e o selo não é o de atraso: `cards.py`, `montar_card_pedido`/`selo_status`. Dono: backend; regra no DESIGN.md: designer.
- **[P3] Teal fora do frontmatter do DESIGN.md.** O detector acusa `rgb(15,118,110)` e `rgb(153,246,228)`. Correção: acrescentar `teal-text`, `teal-bg`, `teal-border` em `colors:`. Dono: designer.
- **[P3] Filtros entre 641 e 1099px.** Em 1024, 228px de pílulas escondidos (scrollWidth 1197 em 969): "Não enviados" e "Devolvidos". Correção: estender a quebra em duas linhas para ≥641px. Dono: frontend (decisão de layout).
- **[P3] "POSTADO" em caixa-alta** no selo do evento de postagem do histórico (`consulta_correios.py:129`, `badge-blue`), contra "sem caixa-alta". Correção: "Postado". Dono: backend.
- **[P3] Aba Atrasados sem contador no Frete** (`opcoes_frete.html:667`, gerado por `Arquivos/frete/report.py`); as outras três páginas mostram "Atrasados 1". Dono: backend.

## Medidas
- Sem estouro horizontal em 1440/1024/375/360, claro e escuro, nas 4 abas.
- Filtros 1440: 2 linhas (76px), sem rolagem (1040 = 1040); zerados na 2ª linha. Primeiro cartão 558 (era 522), 564 em 1024, 381 em 375/360.
- Selo teal: 5,25:1 claro, 7,35:1 escuro. Lado a lado com azul e verde (simulado): distinguível pelo fundo quase branco e pelo texto.
- Linha de atraso simulada no 43333: claro 6,47:1 (vermelho); escuro 6,32 / 7,72 / 10,47:1 (Crítico/Alto/Atenção). No celular, linha própria abaixo do selo (grid-row 2), 164px. Na Compacta fica visível; na Tabela entra na célula Status ("Saiu para entrega Atrasado · 8 dias · Crítico"). Em 1440, com a linha, o "Copiar rastreio" desce para a 2ª linha do cabeçalho (meta de 74px).
- Pílula "Saiu para entrega": 44px no celular, logo depois de "Em trânsito".

## Personas
- Alex (operador experiente): filtra Atrasados, vê "Aguardando retirada" e "há 2 dias" e precisa abrir a aba Atrasados para saber que é Crítico.
- Sam (leitor de tela): selo teal tem descrição em sr-only; a linha de atraso é texto, então é lida.

## Perguntas
- Retirada atrasada mostra a linha "Atrasado · 7 dias · Crítico" abaixo do selo de retirada?
- A quebra em duas linhas dos filtros vale também de 641 a 1099px?
