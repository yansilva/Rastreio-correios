---
target: critica 15 Docker, 4 abas, 1440/1024/375
total_score: 30
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 0
target_identity: "file:C:\\Users\\yansa\\Yan\\Rastreio-correios\\relatorio_rastreio.html"
target_fingerprint: "sha256:c76cba1dca6fcc3578adf82bd9e7582ff9d9ed519673145908afbea45248328f"
target_path: "C:\\Users\\yansa\\Yan\\Rastreio-correios\\relatorio_rastreio.html"
timestamp: 2026-11-24T11-47-07Z
slug: relatorio-rastreio-html
---
⚠️ DEGRADED: single-context (o designer.md proíbe delegar e o navegador é compartilhado; a revisão A rodou antes de ler o detector)

Escopo: 15ª crítica, depois de 0007a68 (14ª aplicada), 22ab245 e ce3b4a3 (Docker). Painel servido pelo container `rastreio-painel` em 127.0.0.1:8000, páginas geradas por consulta real às 08:11–08:12 de 24/11. Medido em 1440, 1024, 375 e 360px, claro e escuro. Dados do dia: 18 pedidos (17 em trânsito, 1 não enviado), 0 atrasados, Entregues com 2 nesta semana e 22 na anterior, frete com 6 pedidos.

## Design Health Score

| # | Heurística | Nota | Ponto principal |
|---|---|---|---|
| 1 | Visibilidade do status | 3 | "Dados de" igual nas 4 páginas; a meta do painel mostra "Próxima consulta automática em —" por 1–4 s até a resposta da API |
| 2 | Linguagem do mundo real | 3 | Escala Atenção/Alto/Crítico em texto |
| 3 | Controle e liberdade | 3 | Esc, Limpar, Todos, seletor de semana anunciado |
| 4 | Consistência | 3 | Escala única de urgência e "Dados de" resolvidos; resumo do frete e de Entregues ainda num estilo diferente do painel |
| 5 | Prevenção de erros | 3 | Consulta desativada na espera |
| 6 | Reconhecimento | 3 | "Situação no Tiny: Enviado" repetida em 17 de 18 cartões dilui o selo de divergência |
| 7 | Flexibilidade | 3 | "/", Esc, três visões, ordenação |
| 8 | Estética e minimalismo | 3 | Entregues no celular estoura a largura (rótulo do resumo); frete no celular com resumo de 119px |
| 9 | Recuperação de erros | 3 | Prazo do frete agora presente; aviso único quando falta no lote |
| 10 | Ajuda | 3 | Legenda em Opções; selos com descrição |
| **Total** | | **30/40** | **Good (75%)** |

## Resolvidos desde a 14ª (verificado)
- Prazo do frete: 8 de 8 serviços com prazo na consulta real; "Mais barato" e "Mais rápido" aparecem. Era o P1.
- Escala de urgência e "Dados de" com a hora dos dados (24/11 08:11 no painel, Atrasados e Entregues; 08:12 no frete, que tem consulta própria).
- Cabeçalho: em 1440 as ferramentas ficam na linha das abas (nav 120–163, ferramentas 121–163); lista em y=566.
- Celular: faixa calma com 25px; primeiro pedido em y=362 (meta ≤420).
- Frete: serviços por preço; serviço único na linha toda.

## Design Specificity Verdict
LLM: específico do produto e mais coeso. O que resta é polimento de bordas em dados reais (rótulos longos, nomes de empresa, cidades longas).

Detector (4 HTMLs + web/): 9 achados, exit 2.
- overused-font Inter (6x): documentado.
- cramped-padding: `.table-wrapper` de Entregues (2x), falso positivo; `.action-strip` do painel (calma, sem respiro vertical), novo, confere com os 25px medidos no celular.
- design-system-color #bfdbfe: exceção documentada.

## Medições
Painel 1440 escuro: header título 27–64, nav 120–163, ferramentas 858–1233 × 121–163, faixa 195–239, cartões 253–345, busca 373–424, pílulas 438–486, visão 492–538, primeiro pedido 566. Sem estouro.
Painel 1024 claro: ferramentas abaixo das abas (decisão); tabela cabe (967px); linhas de 61px, exceto #43236 com 110px: "Msd Saude Animal Merck Sharp & Dohme…" quebra em 4 linhas na coluna Cliente de 151px.
Painel 375 claro: nav 89–133, faixa 147–172, cartões 180–254, pílulas 310–362, primeiro pedido 362; cartões de 361–410px; alvos ≥44px.
Atrasados: estado vazio nas três larguras, sem estouro.
Entregues 1440/1024: Cidade com 9% (87–93px); "SANTANA DO PARAISO/MG" e "CAMPOS DOS GOYTACAZES/RJ" quebram e as linhas vão a 96px (2 de 22). Datas com ano ocupam 14% cada.
Entregues 375 escuro, semana anterior: cartões de 198–228px; página com 378px de largura (estouro de 3px). Causa: o rótulo "Mais demorado&nbsp;·&nbsp;10,0&nbsp;dias" (`pagina_entregues.py:66`) mede 120px numa coluna de 96px. Em 360px: 362px nesta semana ("6,0") e 368px na anterior. O botão "Esta semana (23/11–29/11)" quebra dentro do intervalo, "(23/11–" / "29/11)".
Frete 1440 escuro: 6 pedidos, cartões de 188–238px; "Indisponíveis: SEDEX 10, SEDEX 12" repetido em 6 de 6.
Frete 375 escuro: resumo em 3 colunas de 112×119px; o cartão "Menor frete do lote · Pedidos #43369 e #43307" ocupa 4 linhas; primeiro pedido em y=469. Tema só com ícone; sem estouro.

## Priority Issues
1. [P2] Entregues no celular estoura a largura (3px em 375, até 8px em 360). Correção: `nbsp` só entre número e "dias" (`10,0&nbsp;dias`) e quebra livre depois de "Mais demorado"; ou o tempo numa segunda linha. Arquivo: `Arquivos/correios/pagina_entregues.py:66` (`.summary-label`). /impeccable adapt.
2. [P2] Frete no celular: resumo de 119px e primeiro pedido em y=469. Correção: no ≤640, rótulos curtos ("Pedidos", "Menor frete", "Prazo > 3 dias") e os números dos pedidos do menor frete só no desktop; meta ≤420. Arquivo: `Arquivos/frete/report.py` (`.summary-label`, `.summary-link` no bloco ≤640). /impeccable distill.
3. [P3] Tabela do painel: nome de empresa em 4 linhas (110px). Correção: `-webkit-line-clamp: 2` com `title` em `.orders-table td[data-label="Cliente"]`. `web/css/components.css:1779`. /impeccable layout.
4. [P3] Entregues desktop: Cidade com 9%. Correção: datas sem ano ("17/11 16:21", ano no `title`) e Cidade 15%, Postado/Entregue 11% cada. `components.css:2344-2350` e `pagina_entregues.py`. /impeccable layout.
5. [P3] Seletor de semana quebra o intervalo. Correção: `&nbsp;` e `white-space: nowrap` no intervalo; `pagina_entregues.py:154`. /impeccable polish.
6. [P3] "Situação no Tiny: Enviado" em 17 de 18 cartões. Correção: mostrar só quando diverge ou não é o esperado para o status (como o frete já faz com a situação comum). `Arquivos/correios/cards.py:295`. Decisão do usuário. /impeccable distill.
7. [P3] "Próxima consulta automática em —" na primeira pintura. Correção: escrever no HTML o horário já conhecido (`next_time`) e deixar o JS só atualizar a contagem. `web/js/logs.js` e o gerador da meta. /impeccable harden.
8. [P3] Faixa calma do painel sem respiro vertical (detector). Correção: `padding-block` de 8px na variante calma do celular. `components.css:1503`. /impeccable polish.
9. [P3] Frete: "Indisponíveis: SEDEX 10, SEDEX 12" repetido em todos os pedidos quando vale para o lote. Correção: uma linha no resumo quando o serviço falta em todos. `report.py`. /impeccable distill.

## Persona Red Flags
Casey (celular): Entregues arrasta para o lado na semana anterior; no frete o primeiro pedido só aparece em y=469.
Alex (desktop): na Tabela, nomes de empresa longos esticam a linha; em Entregues, cidades longas quebram.
Sam (leitor de tela): sem regressão.

## Questions to Consider
- "Situação no Tiny" precisa aparecer quando confirma o que os Correios já dizem?
- O resumo do frete no celular precisa dos números dos pedidos?
