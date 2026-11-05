---
target: critica 12 desktop+celular
total_score: 26
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 2
target_identity: "file:C:\\Users\\yansa\\Yan\\Rastreio-correios\\relatorio_rastreio.html"
target_fingerprint: "sha256:115cc42c3fad13aeee452b07fe8cb4ba3e3d3494298fcd1bffe6dde375663a0b"
target_path: "C:\\Users\\yansa\\Yan\\Rastreio-correios\\relatorio_rastreio.html"
timestamp: 2026-11-05T18-31-21Z
slug: relatorio-rastreio-html
---
⚠️ DEGRADED: single-context (o briefing do Coordenador e o designer.md proíbem delegar a outros agentes; detector e navegador rodaram em sequência, com a revisão A antes de ler o detector)

Escopo: 12ª crítica. Desktop 1280 e 1024px, celular 375px, tema claro e escuro. Páginas relatorio_rastreio.html, pedidos_atrasados.html e opcoes_frete.html, servidas em 127.0.0.1:8000. Não comparável 1:1 com a 11ª (28/40, só desktop) nem com a de celular (23/36).

## Design Health Score

| # | Heurística | Nota | Ponto principal |
|---|---|---|---|
| 1 | Visibilidade do status | 3 | Idade dos dados e contagem visíveis; o toast de cópia some em 2 s, no topo, longe do botão |
| 2 | Linguagem do mundo real | 3 | Vocabulário do operador mantido |
| 3 | Controle e liberdade | 3 | Esc, Limpar filtros, pílula Todos |
| 4 | Consistência | 2 | Tabela desativada no celular tem o mesmo anel do botão pressionado; selo verde "POSTADO" fere "verde = entregue"; selo do evento repete o selo do cabeçalho |
| 5 | Prevenção de erros | 3 | Cooldown na consulta; ações só de leitura |
| 6 | Reconhecimento | 3 | Selos com title; pílulas com aria-describedby |
| 7 | Flexibilidade | 3 | "/", Esc, três visões, ordenação |
| 8 | Estética e minimalismo | 2 | Celular: primeiro pedido em y=475 (meta do DESIGN.md: ≤420); cartão médio de 413px |
| 9 | Recuperação de erros | 2 | Falha de cópia: mensagem genérica, sem mostrar o código, sem tentar o método alternativo |
| 10 | Ajuda | 2 | Legenda só em Opções; descrição do selo inacessível ao leitor de tela |
| **Total** | | **26/40** | **Acceptable (65%)** |

## Design Specificity Verdict

LLM: continua específico do produto (Precisam de ação, Tiny desatualizado, Dados de, próxima em). Os problemas desta rodada são de execução e de regressão, não de identidade.

Detector (`impeccable detect --json` em 3 HTMLs + web/): 7 achados, exit 2.
- overused-font Inter (5x): decisão documentada, falso positivo.
- design-system-color (advisory): borda #bfdbfe do selo "Mais barato" em opcoes_frete.html, documentada como exceção.
- side-tab em web/css/components.css:484: o ignore em .impeccable/config.json não casa (valor registrado "3px solid var(--color-border)", achado "border-left: 3px solid var(--color-border)"). O DESIGN.md diz que a exceção funciona; não funciona.
- O ignore de Sfmono funciona (não apareceu). Os campos "reason" do config.json estão com acentuação corrompida (UTF-8 lido como Latin-1).

Overlay: não injetado (painel do navegador oculto; medição feita por JS).

## Medições

Desktop 1280 (claro): header 24–102, nav 120–162, faixa 195–257, cartões 270–362, busca 390–441, pílulas 455–503, linha da visão 509–555, primeiro pedido y=583. Estouro horizontal 0. Botão "Consultar Tiny e Correios" em x 974–1241, y 734–776; a coluna do conteúdo termina em x=1153, então o botão passa por cima de "Copiar rastreio" de cada cartão ao rolar.

Tabela, 1024 (claro, 17 pedidos): tabela 1052px num envoltório de 969px; rolagem lateral da página de 64px (a pendência citava 13px). Colunas: Pedido 89, Cliente 108, Rastreio 148, Status 204, Último evento 151, Tiny 89, Ações 263 ("Copiar rastreio" 122 + "Ver cartão" 92 lado a lado, white-space: nowrap). .orders-table-wrap sem overflow-x. Em 1280 a tabela também excede o envoltório (1052 > 1040), mas a margem absorve.

Celular 375 (claro e escuro): nav sticky 44px ok; todos os alvos ≥44px; busca e campos 16px; estouro 0.
- Primeiro pedido em y=475 (DESIGN.md registra 417). Causas: meta em 2 linhas (38px) porque web/js/logs.js:209 põe "(às HH:MM)" na versão curta; faixa "Precisam de ação" com 100px porque "Aguardando retirada" quebra em 2 linhas e o chip zerado "0 Atrasados" ocupa metade da largura.
- Visão Tabela (aria-disabled) com o mesmo box-shadow inset do botão pressionado (components.css:1908 vs 1818): parecem dois segmentos pressionados. O toque mostra o toast "Tabela indisponível no celular." e mantém a preferência (ok).
- Cartões: média 413px, cabeçalho de 192px; 17 pedidos = 8,2 mil px. Compacta: 227px, 5,0 mil px.
- O botão flutuante (307–359, 744–796) cobre o texto do primeiro evento.

Atrasados (375): 0 atrasados, estado vazio "Nada atrasado" com "Ver o painel"; alvos ≥44px. A aba "Atrasados" só aparece nesta página; no Painel e no Frete ela some quando o total é 0 (decisão de código, consulta_correios.py:469).

Frete (375): título numa linha (20px), primeiro pedido em y=419 (antes ~590); serviços em coluna única, cartão de pedido com 501px, docH 3653. O "esmaecido" da crítica anterior é a animação fadeIn de 0,4s (há regra de reduced-motion). Frete 1280 escuro: ok, 2 cartões de resumo.

Contraste no escuro (composição com alfa): selos 6,2–8,0:1, texto de evento 15:1, chip zerado 6,6:1, pílula zerada 7,5:1.

Pendências conhecidas:
1. Tabela em 1024: confirmada, pior (64px).
2. Descrição do selo: confirmada. O selo é `<span class="badge" title aria-describedby>` não focável; o bloco de descrições tem aria-hidden. Leitor de tela em modo de leitura não anuncia aria-describedby de span genérico; no toque o title também não aparece. Nas pílulas (botões) funciona.
3. Ordem duplicada: confirmada em Arquivos/correios/cards.py:85–112 (selo_status e chave_selo repetem a mesma cascata).
4. Toast de "Copiar rastreio": sucesso NÃO verificado. Com o painel do navegador oculto o documento não tem foco e o writeText é rejeitado, inclusive em clique real. Falha verificada: toast vermelho "Não foi possível copiar o rastreio", 2 s, no topo (y=14). Quando o writeText rejeita, o código não tenta o execCommand (app.js:98–100). Cores fixas em hex em app.js:70 e :96.
5. Painel sem senha no Wi-Fi: pergunta de produto.

## Priority Issues

1. [P1] Tabela com 64px de rolagem lateral em 1024. Correção: a tabela cabe no contêiner a partir de 1024 (Ações empilhadas ou "Ver cartão" como link abaixo, largura máxima no Status, table-layout fixo) e overflow-x: auto no envoltório como rede de segurança. /impeccable adapt.
2. [P1] Primeiro pedido em y=475 no celular (regressão; meta ≤420). Correção: versão curta da contagem sem "(às HH:MM)"; chips da faixa com largura pelo conteúdo, o zerado encolhe. /impeccable distill.
3. [P2] Descrição do selo inacessível ao leitor de tela. Correção: texto sr-only irmão do selo, fora do .badge. /impeccable harden.
4. [P2] Tabela desativada parece pressionada. Correção: tirar o anel do aria-disabled, estado tracejado e esmaecido. /impeccable polish.
5. [P2] Copiar rastreio: sem fallback quando a API rejeita, falha sem o código, cores fora dos tokens. /impeccable harden.
6. [P2] Botão "Consultar Tiny e Correios" cobre "Copiar rastreio" em 1024 e 1280. /impeccable layout.
7. [P2] Selos de evento: "POSTADO" verde (fere One Meaning Per Color) e o selo do evento repete o do cabeçalho. /impeccable quieter.
8. [P3] Cartão no celular com 413px. /impeccable distill.
9. [P3] Frete no celular: serviços em coluna única; "Menor frete do lote" sem dizer de qual pedido. /impeccable adapt.
10. [P3] Precedência dos selos duplicada em cards.py.
11. [P3] Exceção side-tab que não casa e config.json com acentos corrompidos. /impeccable document.

## Persona Red Flags

Sam (leitor de tela): o selo de status do cartão é anunciado só como "Aguardando retirada", sem a explicação; no celular a Tabela desativada é anunciada como indisponível (ok), mas visualmente parece selecionada.
Casey (celular): 475px antes do primeiro pedido; cartões de 413px; o botão flutuante cobre o texto do primeiro evento.
Alex (desktop): em 1024 a Tabela pede rolagem lateral para chegar a "Copiar rastreio"; ao rolar, o botão flutuante cobre "Copiar rastreio".

## Minor Observations

- Aba Atrasados aparece e some conforme o total; no Painel não há caminho para a página de atrasados quando é 0 (coerente com Zero Is Calm).
- Toast de sucesso dura 2 s, fica no topo e o botão de cópia fica embaixo.

## Questions to Consider

- O botão de consulta precisa flutuar no desktop, onde há cabeçalho com espaço?
- A visão padrão no celular deveria ser Compacta, já que Cartões custa 1,8x a rolagem?
- O painel deve exigir senha quando acessado pelo Wi-Fi?
