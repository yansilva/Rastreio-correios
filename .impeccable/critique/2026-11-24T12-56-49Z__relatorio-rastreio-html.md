---
target: critica 16 Mesa Limpa, 4 abas, 1440/1024/375/360
total_score: 30
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 0
target_identity: "file:C:\\Users\\yansa\\Yan\\Rastreio-correios\\relatorio_rastreio.html"
target_fingerprint: "sha256:f06c4b757d285ac48e909da349b972b4036b3f4d5db72a8391de03fea0afa251"
target_path: "C:\\Users\\yansa\\Yan\\Rastreio-correios\\relatorio_rastreio.html"
timestamp: 2026-11-24T12-56-49Z
slug: relatorio-rastreio-html
---
⚠️ DEGRADED: single-context (o designer.md proíbe delegar e o navegador é compartilhado; a revisão A rodou antes de ler o detector)

Escopo: 16ª crítica, Mesa Limpa implementada (cfd9121), container `rastreio-painel` em 127.0.0.1:8000, dados de 24/11 09:46. Painel, Atrasados (vazio), Entregues (duas semanas) e Frete (cópia fictícia com 5 pedidos, servida em 8014 e apagada; a página real ainda está no visual antigo). 1440, 1024, 375 e 360px, claro e escuro. Comparação contra o DESIGN.md da Mesa Limpa por estilo computado.

## Design Health Score

| # | Heurística | Nota | Ponto principal |
|---|---|---|---|
| 1 | Visibilidade do status | 3 | Meta e contagem visíveis; nada mudou |
| 2 | Linguagem do mundo real | 3 | Selos em caixa normal com o nível escrito |
| 3 | Controle e liberdade | 3 | Igual |
| 4 | Consistência | 3 | Ganhou com tokens únicos; perdeu com cabeçalho centralizado só no Frete, título de 28px em 3 abas e 24px no Frete, botão de consulta em pílula ao lado do tema de 8px |
| 5 | Prevenção de erros | 3 | Igual |
| 6 | Reconhecimento | 3 | "Situação no Tiny" ainda em todo cartão |
| 7 | Flexibilidade | 3 | Igual |
| 8 | Estética e minimalismo | 3 | Mais calmo e plano; no escuro, bordas de status em pastel claro fazem halo |
| 9 | Recuperação de erros | 3 | Igual |
| 10 | Ajuda | 3 | Igual |
| **Total** | | **30/40** | **Good (75%)**, igual à 15ª |

## Resolvidos da 15ª (verificado)
- Entregues no celular: sem estouro em 360 e 375 nas duas semanas ("Mais demorado · 10,0 dias" quebra em 2 linhas).
- Frete no celular: resumo com 60px e rótulos curtos; primeiro pedido em y=409 (meta ≤420).
- Tabela do painel: nomes longos em 2 linhas, linha máxima de 63px.
- Inter: nenhum `@font-face`; corpo em Segoe UI Variable Text; o detector não acusa mais a fonte.
- Posições: painel 1440 primeiro cartão 535 (≤566); 1024 cartão 577; 375 e 360 primeiro cartão 358 (≤362); números do resumo no mesmo topo; abas de 44px no celular; Entregues primeira linha 324 (≤329).

## Divergências da implementação em relação ao DESIGN.md (estilo computado)
| Elemento | DESIGN.md | Medido | Origem |
|---|---|---|---|
| `h1` (Painel, Atrasados, Entregues ≥641) | 24px | 28px | `components.css:1581-1585` (regra antiga vence `main.css`) |
| `h1` (Frete) | 24px | 24px | ok; logo, as abas divergem entre si |
| Botão de consulta (desktop) | raio 8px, 36px, 13px/600, sem sombra | raio 9999px, 42px, 16px/700, `--shadow-lg` | `components.css:2524` exclui `.btn-update` da camada nova |
| `.btn-ver-cartao` | raio 8px | 9999px | regra antiga |
| Bordas de status no escuro (`--color-*-border`) | não definidas no DESIGN.md | pastel do claro (#bae6fd, #bbf7d0, #fde68a, #fecaca, #e9d5ff) | `main.css` sem valores no `[data-theme="dark"]` |
| `.order-title` / `.order-num` | 16px peso 600, tabular | 20px peso 700, sem tabular | regra antiga |
| `.order-header` | 14×16px | 15×25px | regra antiga |
| Bolinha da timeline | 10px | 12px | regra antiga |
| `.dash-card`, `.summary-card` (desktop e frete) | 14×16px | 18×20px | regra antiga e `report.py` |
| `.search-input` (desktop) | 40px | 51px (16px de fonte) | padding antigo |
| `.action-strip` (faixa calma) | 8×12px | 10×14 no desktop; 0×12 no celular (23px) | regras antigas; detector acusa |
| `.nav-tabs` | à esquerda | `justify-content: center` dentro da caixa de 640px (deslocamento muda por aba) | `main.css` |
| Meta no celular | alinhada ao título | centralizada (texto em x=37, título em x=12) | regra antiga do ≤640 |
| Rastreio na Tabela e em Entregues | mono | Segoe UI | só `.order-code` recebeu a mono |
| Estado vazio | título 14px/600, compacto, link na linha | `h2` 21px com margens padrão; caixa de 205px | `components.css` (h2 e p sem margem zerada) |
| `strong`, `.pill-count`, `.contagem-completa` | peso máx. 600 | 700 (81 `strong` no painel) | padrão do navegador e regras antigas |
| Frete: cabeçalho | à esquerda | centralizado | `report.py` |
| Frete: selos "Mais barato/Mais rápido" | caixa normal, raio 6px, 600 | caixa-alta, 0.6px, raio 9999px, 700 | `report.py` (`.servico-selo`) |
| Frete: busca / serviço / abas | 8px / 8px / 40px | 10px / 6px / 44px no desktop | `report.py` |
| Frete: CEP | mono | Segoe UI | `report.py` |

## Detector
`impeccable detect --json` (3 HTMLs reais + frete fictício + web/): Inter sumiu. Achados: `cramped-padding` no `.action-strip` (real, ver tabela) e no `.table-wrapper` de Entregues (falso positivo); `em-dash-overuse` 34x só no frete fictício (não visível em texto); `design-system-font-size` 11x (1.75rem), `design-system-color` 5x (#000) e `design-system-radius` 1x (12px) em `components.css`, todos em regras antigas; só o 1.75rem do `h1` chega à tela.

## Priority Issues
1. [P2] Bordas de status no escuro em pastel claro (halo em selos, chips e faixa calma). Correção: valores no `[data-theme="dark"]` de `main.css` (`--color-success-border: rgba(74,222,128,.35)`, `--color-warning-border: rgba(251,191,36,.35)`, `--color-danger-border: rgba(248,113,113,.35)`, `--color-info-border: rgba(56,189,248,.35)`, `--color-purple-border: rgba(192,132,252,.35)`) e registrar no DESIGN.md. /impeccable colorize.
2. [P2] Botão de consulta no desktop fora da Mesa Limpa (pílula, sombra, 16px/700, 42px) ao lado do tema de 8px. Correção: aplicar a regra de botões a `.btn-update` a partir de 641px; o FAB ≤640 segue redondo. `components.css:2524`. /impeccable polish.
3. [P2] Frete fora da Mesa Limpa em cabeçalho (centralizado), selos (caixa-alta, pílula, 700), busca (10px), serviço (6px), resumo (18×20), abas (44px no desktop) e CEP. `Arquivos/frete/report.py`. /impeccable polish.
4. [P3] Título de 28px em 3 abas (regra antiga `components.css:1581-1585`); 24px no Frete. Remover a regra. /impeccable typeset.
5. [P3] Cartão de pedido com título 20px/700, cabeçalho 15×25, bolinha 12px; resumo 18×20; busca 51px. Regras antigas; entram na limpeza pendente. /impeccable polish.
6. [P3] Abas centralizadas na própria caixa em vez de alinhadas à esquerda. `main.css` `.nav-tabs { justify-content: flex-start }` a partir de 641px. /impeccable layout.
7. [P3] Meta centralizada no celular sob título à esquerda. Regra ≤640 de `.header-main .meta`. /impeccable layout.
8. [P3] Rastreio sem mono na Tabela e em Entregues. `.orders-table td[data-label="Rastreio"]`, `.table-wrapper td[data-label="Rastreio"]` com `--font-mono`. /impeccable typeset.
9. [P3] Estado vazio alto (205px) com `h2` 21px. `.empty-state h2 { font-size: .875rem; font-weight: 600; margin: 0 }`, `p { margin: 0 }`, link na linha. /impeccable distill.
10. [P3] Peso 700 em `strong`, `.pill-count`, `.order-num`. `main.css`: `strong, b { font-weight: 600 }`. /impeccable typeset.
11. [P3] `.btn-ver-cartao` redondo ao lado do "Copiar rastreio" de 8px. /impeccable polish.
12. [P3] Faixa calma sem respiro vertical no celular (23px). `.action-strip` ≤640 com `padding: 8px 12px`. /impeccable polish.

## Persona Red Flags
Alex (desktop, escuro): halos claros nos selos de cada cartão; botão de consulta com outro desenho que o resto.
Casey (celular): sem regressão; primeiro pedido em 358.
Sam: sem regressão; contraste dos textos medido conforme o DESIGN.md.

## Não avaliado
- Tabela de Atrasados (0 atrasados; a demo não foi gerada).
- Frete real (ainda antigo).

## Questions to Consider
- "Situação no Tiny" continua em todo cartão; mostrar só quando diverge?
