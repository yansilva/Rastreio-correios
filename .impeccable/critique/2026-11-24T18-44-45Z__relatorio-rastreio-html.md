---
target: critica 17 aviso dos Correios, 4 abas, 1440/1024/375/360
total_score: 31
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 0
target_identity: "file:C:\\Users\\yansa\\Yan\\Rastreio-correios\\relatorio_rastreio.html"
target_fingerprint: "sha256:ee2427a8e3c44ab8ad8e1a6a65ecb5edc690be4131c900154486af4dcbe44e8e"
target_path: "C:\\Users\\yansa\\Yan\\Rastreio-correios\\relatorio_rastreio.html"
timestamp: 2026-11-24T18-44-45Z
slug: relatorio-rastreio-html
---
⚠️ DEGRADED: single-context (regra do coordenador: o especialista designer não delega a outros agentes; avaliação de design feita antes de ler o detector)

# 17ª crítica — painel (Painel, Atrasados, Entregues, Frete fictício), 1440/1024/375/360, claro e escuro

## Nota: 31/40 (16ª: 30/40)

| # | Heurística | Nota | Ponto-chave |
|---|---|---|---|
| 1 | Visibilidade do status | 4 | Aviso visível em 3 lugares (linha, chip, filtro) sem trocar o status real; contagem "1 de 19 pedidos" ao filtrar |
| 2 | Linguagem do mundo real | 3 | Texto do aviso dos Correios na íntegra; "Precisam de ação" agora abriga um aviso que não pede ação |
| 3 | Controle e liberdade | 3 | Igual |
| 4 | Consistência | 3 | Frete alinhado; restam os segmentados em pílula (DESIGN pede 8px), número do chip em 800 e 16px, frete com pesos 700/800 |
| 5 | Prevenção de erros | 3 | Correção da retirada tirou o falso "aguardando retirada" |
| 6 | Reconhecimento | 3 | "Situação no Tiny" só quando diverge (1 de 19); data do aviso solta à direita no celular |
| 7 | Flexibilidade | 3 | Igual |
| 8 | Estética e minimalismo | 3 | Faixa com borda vermelha sem nenhum atraso; chip de aviso preenchido pesa mais que o de atraso |
| 9 | Recuperação de erros | 3 | Igual |
| 10 | Ajuda | 3 | `title` no chip e no selo curto |
| **Total** | | **31/40** | **Good (78%)** |

## Especificidade
O painel continua com cara de ferramenta própria: rastreio em mono, selos com o nível escrito, timeline. O aviso entrou no vocabulário certo (linha com rótulo, não um selo a mais). O detector achou 2 avisos de qualidade no HTML real e 4 avisos consultivos no Frete antigo (não vale: o Frete real ainda é o visual anterior). Falsos positivos: "RIO DE JANEIRO/RJ 4×" no cartão (é a timeline + histórico); `table-wrapper` sem respiro (as células têm padding).

## Achados
- **[P2] Faixa com borda vermelha sem atraso.** `web/css/components.css:94` (`.action-strip { border: 1px solid var(--color-danger-border) }`). Medida: borda #fecaca no claro e rgba(248,113,113,.35) no escuro, com 0 atrasados e 0 retiradas, em todos os tamanhos. Sinal de urgência falso. Correção: borda `var(--color-border)` (DESIGN.md, faixa de ação); se quiser alarme, só com `.action-strip:has(.action-chip[data-filter="atrasado"]:not(.is-zero))`. Responsável: frontend.
- **[P2] Chip de aviso pesa mais que o de atraso.** `components.css:106-131` e `:169-178`. Medida: atraso com N>0 = fundo transparente, borda cinza, número vermelho; aviso = fundo roxo preenchido (rgba(147,51,234,.15)) e borda roxa. Com atraso e aviso juntos, a informação vence a urgência. Correção: chip de aviso no mesmo molde dos outros (fundo transparente, borda `--color-border-strong`; roxo só no ícone e no número); fundo roxo só em `.active`. A especificação do aviso no DESIGN.md (minha) precisa dizer isso. Responsável: designer (DESIGN.md) e frontend.
- **[P3] Controles segmentados em pílula.** `components.css:2052-2065` (`.view-switch`, `.view-option` com `--radius-full`) e `.entregues-seletor`. Medida: 9999px; DESIGN.md pede contêiner de 8px. No celular, "Cartões" fica num anel de 49px colado ao texto. Correção: `--radius-md` no contêiner e `--radius-sm` no segmento. Responsável: frontend (entra na limpeza de regras antigas).
- **[P3] Número do chip em 800 e 16px; rótulo em 14px.** `components.css:113,127-129`. DESIGN.md: peso máximo 600, Secondary 13px. Correção: `strong { font-size: inherit; font-weight: 600 }`, chip `0.8125rem`. Responsável: frontend.
- **[P3] Data do aviso solta no celular.** `.order-aviso-data` em 375/360: o rótulo vai para uma linha, o texto quebra em 2 e "24/11" fica à direita no meio (linha de 79px). Correção: no celular, data logo depois do rótulo ("Aviso dos Correios · 24/11") e o texto na linha de baixo. Responsável: frontend.
- **[P3] Filtros rolam já em 1440.** `.filter-pills`: 1103px de conteúdo em 1040px; "Devolvidos 0" cortado em 35px. Aceitável (zerado no fim), mas o nono filtro mudou isso. Correção opcional: gap de 6px e padding 0×8px nos zerados. Responsável: frontend.
- **[P3] Frete (cópia fictícia).** Abas centralizadas (`.nav-tabs` com `justify-content: center`, 1ª aba em x=281 contra 193 no Painel); pesos 700/800 em `.pedido-numero`, `.pedido-valor`, `.servico-nome`, `.pedido-badge`; `.pedido-badge` ("Pago") em caixa-alta e pílula. Arquivo: `Arquivos/frete/report.py`. Responsável: frontend.

## Hierarquia do aviso no cartão
Status (selo azul "Em trânsito") segue no cabeçalho; o aviso é uma faixa roxa logo abaixo, 38px no desktop e 79px no celular, contraste 5,92:1 (claro) e 5,91:1 (escuro); data 6,51 e 6,88:1. A cor não briga com a escala de urgência. Num cartão atrasado com aviso, a faixa roxa ocupa mais área que o selo vermelho, mas o selo e a timeline continuam carregando a urgência; aceitável. O risco real está na faixa do topo (achado P2 acima), não no cartão.

## Divergências do DESIGN.md
1. `.action-strip` com borda de perigo (DESIGN: `--color-border`).
2. DESIGN diz que chips têm "fundo e borda da cor do status", mas o atraso é contornado e só o aviso é preenchido: corrigir o texto do DESIGN para o molde contornado.
3. `.view-switch`/`.entregues-seletor` em pílula (DESIGN: 8px).
4. Chip: número 800/16px, rótulo 14px (DESIGN: ≤600, 13px).
5. Título do chip de aviso: implementado "Pedido com aviso dos Correios que ainda não foi entregue."; DESIGN diz "Pedidos em aberto com aviso dos Correios, como atraso previsto na entrega". Alinhar um dos dois.
6. Frete: abas centralizadas e pesos 700/800.

## Medidas
- Sem estouro horizontal em nenhuma combinação (Painel, Atrasados, Entregues, Frete; 1440/1024/375/360; claro e escuro).
- Primeiro cartão do Painel: 522 (1440), 564 (1024), 381 (375 e 360).
- Frete fictício: primeiro pedido 494 (1440), 544 (1024), 409 (375 e 360).
- Filtro "Com aviso": 1 de 19; chip com `aria-pressed="true"`; busca "mais tempo" acha o 43312; selo "Aviso" com `title` e `.sr-only` na Compacta e na Tabela; a linha some na Compacta.

## Perguntas ao usuário
1. O pedido com aviso deve subir na ordem da lista? Hoje o 43312 é o 11º de 19.
2. Quando só houver aviso (nada atrasado), a faixa deve continuar dizendo "Precisam de ação", ou mostrar a linha calma "Nada atrasado nem aguardando retirada" com o chip de aviso ao lado?
