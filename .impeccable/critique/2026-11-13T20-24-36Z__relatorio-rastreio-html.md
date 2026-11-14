---
target: critica 14 desktop+celular, 4 paginas
total_score: 29
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 1
target_identity: "file:C:\\Users\\yansa\\Yan\\Rastreio-correios\\relatorio_rastreio.html"
target_fingerprint: "sha256:4e6440432e8b7d367c43e98fadfda8b3ce52f1b6db4ddcf08eba7dc91474f8de"
target_path: "C:\\Users\\yansa\\Yan\\Rastreio-correios\\relatorio_rastreio.html"
timestamp: 2026-11-13T20-24-36Z
slug: relatorio-rastreio-html
---
⚠️ DEGRADED: single-context (o designer.md proíbe delegar e o navegador é compartilhado; a revisão A rodou antes de ler o detector)

Escopo: 14ª crítica, depois do commit a31d91a (lotes A–D da 13ª). Painel, Atrasados (agora com 1 atrasado), Entregues e Frete em 127.0.0.1:8000, em 1280, 1024, 375 e 360px, claro e escuro. Frete também numa cópia temporária com 5 pedidos fictícios (3 serviços, aviso da Portaria, prazo vazio, serviço único, nenhum serviço), servida em 8012 e apagada no fim. O frete servido já era o novo (17:09).

## Design Health Score

| # | Heurística | Nota | Ponto principal |
|---|---|---|---|
| 1 | Visibilidade do status | 3 | Idade dos dados e contagem visíveis; "Dados de" de Atrasados e Entregues mostra a hora da geração (17:13), não a dos dados (16:46, como no painel) |
| 2 | Linguagem do mundo real | 3 | "Prazo indisponível" no lugar do "—" |
| 3 | Controle e liberdade | 3 | Esc, Limpar, Todos, seletor de semana |
| 4 | Consistência | 2 | O mesmo pedido #42793 é "ATRASADO · 4 DIAS" em vermelho no painel e "4 dias · Atenção" em âmbar em Atrasados; "Dados de" com dois sentidos |
| 5 | Prevenção de erros | 3 | Consulta desativada na espera |
| 6 | Reconhecimento | 3 | "Ver cartão" com ícone próprio |
| 7 | Flexibilidade | 3 | "/", Esc, três visões, ordenação |
| 8 | Estética e minimalismo | 3 | Entregues 287px no celular; frete limpo; no desktop a lista começa em y=633 |
| 9 | Recuperação de erros | 3 | Prazo ausente agora dito e com motivo salvo nos dados |
| 10 | Ajuda | 3 | Legenda em Opções; selos com descrição |
| **Total** | | **29/40** | **Good (73%)** |

## Resolvidos da 13ª (verificado)
- Tema do frete no celular escuro: só o ícone, 44×44; rótulos sr-only.
- Entregues no celular: 287px por entrega (antes 386); resumo em 3 colunas, 114×74, padding 6×8.
- Cartões de resumo em 360: "Devolvidos" numa linha; números no mesmo topo (y=243).
- Título × ferramentas: ferramentas em y 24–66, título em 74–119, em 1024 e 1280.
- Frete: serviço único na linha inteira; aviso da Portaria na largura do cartão (291×105 no celular, antes 129×323); 16px entre menu e resumo; sem borda lateral; "Prazo indisponível"; "Mais rápido" aparece quando há prazo (dados fictícios).
- Entregues 1280: datas e dias numa linha; rastreio e botão na mesma linha.
- "Ver cartão" com ícone de cartão.

## Ainda aberto
- Prazo do frete real: "Prazo indisponível" em 15 de 19 serviços. O motivo agora fica em `prazo_erro`, mas só uma consulta real vai mostrá-lo.

## Design Specificity Verdict
LLM: específico do produto. A família visual ficou mais coesa; o que resta é coerência de significado (cor de atraso, hora dos dados), não de forma.

Detector (4 HTMLs reais + cópia do frete + web/): 12 achados, exit 2.
- overused-font Inter (7x): decisão documentada.
- cramped-padding em `.table-wrapper` de Atrasados e Entregues (2x): falso positivo (as células têm padding).
- design-system-color #bfdbfe do selo "Mais barato": exceção documentada.
- em-dash-overuse (34x) só na cópia fictícia; o frete real tem 1 travessão (no `<title>`). Não reproduzido na página real.
- Sumiram: side-tab (7x), raio 4px, fonte 0.9375rem, cramped-padding do `.summary-card`.

## Medições
Painel 1280 escuro (visão Tabela): ferramentas 24–66, título 79–113, meta 127–152, nav 170–213, faixa "Precisam de ação" 245–306, cartões 320–412, busca 440–490, pílulas 504–552, visão 558–604, tabela a partir de y=633 (13ª: 565). Tabela cabe (1038px), linhas de 61–65px. Sem estouro.
Painel 1024 claro: tabela cabe (967px); lista em y=633; pílulas rolam (1056 > 967), como documentado.
Painel 375 claro: faixa "Precisam de ação" com 81px (rótulo numa linha e chips na outra); primeiro pedido em y=419 (meta ≤420, no limite). Cartões de 199–225px na Compacta. 360 escuro: igual, sem estouro, nav 336px.
Atrasados 1280: tabela cabe (1038px), 1 linha de 73px; resumo 1/0/0/1 com os zerados neutros.
Entregues 1280: Cliente com 122px e Rastreio com 288px; nomes longos quebram em 3–4 linhas (linhas de 96 e 119px). 375: 287px por entrega; "Mais demorado · 1,9 dias" quebra e a segunda linha começa com "·".
Frete real 375 escuro: 12 pedidos, cartões de 309–440px, docH 4904; nav→resumo 16px. Frete fictício 1280: cartões de 146–288px, aviso da Portaria na largura toda; serviços em ordem de código (SEDEX 10 a R$ 48,20 antes de SEDEX 12 a R$ 31,50).
Cópia fictícia no celular: `scrollWidth` 586 mesmo com todo o conteúdo oculto; não ocorre na página real (375). Tratei como artefato da origem temporária.

## Priority Issues
1. [P1, pendente de consulta real] Prazo do frete vazio em 15 de 19 serviços. Correção: na próxima consulta real, ler `prazo_erro` e o log WARNING de `frete.service` e corrigir a causa. /impeccable harden.
2. [P2] Mesmo atraso com duas cores: no painel o selo é vermelho para qualquer atraso (`cards.py:97`, `badge-red`); em Atrasados, 4 dias é âmbar "Atenção". Correção: o selo do painel segue a escala de urgência de Atrasados (4 dias âmbar, 5–6 laranja, 7+ vermelho) com o mesmo texto. Decisão do coordenador antes. /impeccable colorize.
3. [P2] "Dados de" com dois sentidos: painel mostra a hora dos dados; Atrasados e Entregues mostram a hora da geração (`consulta_correios.py:589` usa `time.strftime`; `pagina_entregues.py:176` usa `agora`). Correção: passar a mesma hora dos dados do painel. /impeccable clarify.
4. [P2] Entregues 1280: Cliente espremido (122px), nomes em 3–4 linhas. Correção: `table-layout: fixed` com Cliente ≥200px e Rastreio ~250px. /impeccable layout.
5. [P3] Desktop: a lista começa em y=633 (+68px desde que as ferramentas subiram). Opção: ferramentas na linha da nav. /impeccable layout.
6. [P3] Celular: "Precisam de ação" com 81px deixa o primeiro pedido em 419. Correção: rótulo sr-only no celular, só os chips (~44px). /impeccable distill.
7. [P3] Entregues celular: 287px por entrega; Pedido+Cliente e Entregue em+Dias em pares numa linha levariam a ~180px; "· 1,9 dias" no início de linha. /impeccable distill.
8. [P3] Frete: serviços em ordem de código, não de preço; "Prazo indisponível" repetido em 15 cartões. /impeccable distill.

## Persona Red Flags
Alex (desktop): na Tabela, 633px de cabeçalho antes da primeira linha; vê o #42793 vermelho no painel e âmbar em Atrasados.
Casey (celular): primeiro pedido no limite (419); em Entregues, 7 entregas somam 2 mil px.
Sam (leitor de tela): sem regressão; rótulos do tema e colunas ocultas de Entregues seguem na árvore.

## Minor Observations
- Frete fictício: com 1 dia útil em SEDEX, SEDEX 10 e SEDEX 12, "Mais rápido" vai para o SEDEX pelo desempate de preço: correto, mas dois selos no mesmo cartão.

## Questions to Consider
- Atraso de 4 dias é "atenção" ou "atrasado"? A cor precisa dizer a mesma coisa nas duas páginas.
- As ferramentas do desktop podem dividir a linha com a navegação?
