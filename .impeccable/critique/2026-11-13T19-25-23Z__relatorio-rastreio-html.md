---
target: critica 13 desktop+celular, 4 paginas
total_score: 27
max_score: 40
na_heuristics: 
p0_count: 0
p1_count: 3
target_identity: "file:C:\\Users\\yansa\\Yan\\Rastreio-correios\\relatorio_rastreio.html"
target_fingerprint: "sha256:bab20496a79faa5c8b5ad3c05603616343c10de1309fab9959caedda8202eaf4"
target_path: "C:\\Users\\yansa\\Yan\\Rastreio-correios\\relatorio_rastreio.html"
timestamp: 2026-11-13T19-25-23Z
slug: relatorio-rastreio-html
---
⚠️ DEGRADED: single-context (o designer.md proíbe delegar a outros agentes e o navegador embutido é compartilhado; a revisão A rodou antes de ler o detector e o navegador foi usado em sequência)

Escopo: 13ª crítica. Painel, Atrasados, Entregues (nova) e Opções de Frete, servidos em 127.0.0.1:8000. Medido em 1280, 1100, 1024, 375 e 360px, tema claro e escuro. O `opcoes_frete.html` servido já tinha o menu novo (gerado às 15:34), então não foi preciso gerar cópia. Atrasados está com 0 pedidos: só o estado vazio foi avaliado.

## Design Health Score

| # | Heurística | Nota | Ponto principal |
|---|---|---|---|
| 1 | Visibilidade do status | 3 | Idade dos dados e contagem visíveis; a meta mostra "próxima em —" até o JS rodar |
| 2 | Linguagem do mundo real | 3 | Vocabulário do operador; "Gerado em" (Atrasados, Entregues, Frete) e "Dados de" (Painel) para a mesma ideia |
| 3 | Controle e liberdade | 3 | Esc, Limpar, pílula Todos, seletor de semana |
| 4 | Consistência | 2 | Os 4 cabeçalhos e os 3 tipos de cartão de resumo diferem; botão de tema do frete mostra "Claro" no celular escuro; rastreio em monoespaçada só em Entregues |
| 5 | Prevenção de erros | 3 | Consulta desativada na espera; ações só de leitura |
| 6 | Reconhecimento | 3 | Selos com descrição sr-only; "Ver cartão" é um ícone de caixa sem rótulo visível |
| 7 | Flexibilidade | 3 | "/", Esc, três visões, ordenação |
| 8 | Estética e minimalismo | 2 | Entregues no celular: 386px por entrega (7 entregas = 2,7 mil px); aviso dos Correios no frete vira coluna de 129×323px |
| 9 | Recuperação de erros | 2 | Frete: prazo "—" em 16 de 21 serviços, sem dizer por quê |
| 10 | Ajuda | 3 | Legenda em Opções; descrição do selo agora acessível |
| **Total** | | **27/40** | **Acceptable (68%)** |

## Design Specificity Verdict

LLM: continua específico do produto. A aba Entregues encaixa no vocabulário (semana, dias até a entrega), mas chegou com o cabeçalho, os cartões de resumo e a tabela de outro "dialeto" visual; o painel virou quatro páginas que não falam igual.

Detector (`impeccable detect --json` nos 4 HTMLs + web/): 21 achados, exit 2.
- overused-font Inter (6x): decisão documentada, falso positivo.
- cramped-padding (4x) em entregues_semana.html: `.summary-card` com `padding: 6px 2px` (components.css:2022) e `.table-wrapper`. Verdadeiro positivo no `.summary-card` do celular.
- side-tab (7x) em opcoes_frete.html: a borda esquerda de 3px do serviço "Mais barato". Documentada no DESIGN.md, mas a exceção do config só cobre components.css.
- design-system-radius 4px (opcoes_frete.html:330), design-system-font-size 0.9375rem (:555), design-system-color #bfdbfe (exceção documentada).
- em-dash-overuse (17x) em opcoes_frete.html: são os "—" do prazo vazio, sintoma do problema do prazo.

Overlay: não injetado (navegador compartilhado; medição por JS).

## Medições

Painel 1280 (escuro): header 24–102, nav 120–162, faixa 195–239, cartões 253–345, busca 373–423, pílulas 437–485, linha da visão 491–537, primeiro pedido y=565. Estouro 0. Título "Status de Entregas" em x 490–775 e ferramentas em 778–1153: 3px entre o título e o botão "Claro". Igual em 1100 (400–685 e 688–1063). O conteúdo tem 1040px em qualquer largura ≥1080, então o lado a lado nunca tem folga.
Tabela 1280 e 1024: cabe no contêiner (1038 e 967px, sem rolagem lateral); linhas de 61–66px; table-layout fixed. Pendência da 12ª resolvida.
Opções aberto (1280): painel 793–1153, cabe; "Recarregar dados salvos de 14:32" quebra em 2 linhas (57px).
Painel 375: primeiro pedido y=374 (meta ≤420: ok); cartão médio 382–507px; FAB 744–796 cobre o canto do primeiro cartão (termina em 756). Cartões de resumo: os números ficam em alturas diferentes (y=199 e y=208) porque "Não enviados" e "Entregues hoje" quebram em 2 linhas e o cartão centraliza na vertical.
Painel 360: nav cabe (336px); "Devolvidos" quebra no meio da palavra ("Devolvido/s") e "Em trânsito" em 2 linhas, por `overflow-wrap: anywhere` em `.dash-label` (components.css:1476).
Entregues 1280: tabela auto, Rastreio 266px com o código encostado no botão (4px); datas e "1,9 dias" quebram em 2 linhas; linhas de 73px.
Entregues 375: 3 cartões de resumo numa grade de 4 colunas (sobra 89px à direita), padding 2px; cada entrega vira cartão de 386px com os 7 campos (a regra `.col-secundaria` do celular existe, mas `pagina_entregues.py` não marca colunas com ela); docH 3197.
Frete 1280: nav termina em 220 e o resumo começa em 220 (0px de respiro). Prazo: "—" em 16 de 21 serviços, "2 dias úteis" em 4. "Mais rápido" nunca aparece.
Frete 375 escuro: o botão de tema (44×44) mostra "☀ Claro" vazando do círculo. Causa: `[data-theme="dark"] .btn-theme .tema-claro { display: inline-block }` (report.py, linha 201 do HTML) vence `.btn-theme span { display: none }` (linha 514). No claro não acontece. Serviços em 2 colunas de 155px: pedido com 1 serviço deixa meia linha vazia; o aviso da Portaria (âmbar) fica em 129×323px.
Atrasados 375: estado vazio ok; a meta quebra e a segunda linha começa com "— Gerado em".
Contraste e alvos: alvos ≥44px no celular; sem estouro horizontal nas 4 páginas.

## Priority Issues

1. [P1] Frete: prazo "—" em 16 de 21 serviços, sem explicação. O operador escolhe pelo preço sem saber o prazo, e "Mais rápido" some. /impeccable harden (backend investiga; frontend troca "—" por "Prazo indisponível").
2. [P1] Frete no celular escuro: "Claro" vaza do botão de tema. /impeccable polish.
3. [P1] Entregues no celular: 386px por entrega. Marcar Cidade e Postado em como `.col-secundaria` (sai de ~386 para ~250px). /impeccable distill.
4. [P2] Cartões de resumo no celular: palavra quebrada em 360px e números desalinhados. /impeccable layout.
5. [P2] Título colado no botão "Claro" de 1100 a 1280px (3px). /impeccable layout.
6. [P2] Frete no celular: serviço único ocupa meia linha e o aviso vira torre de 323px. /impeccable adapt.
7. [P2] Entregues: resumo com 3 cartões em grade de 4 no celular; no desktop, datas e dias quebram e o código encosta no botão. /impeccable layout.
8. [P3] Cabeçalhos diferentes nas 4 páginas ("Dados de" × "Gerado em", "—" no início da linha). /impeccable clarify.
9. [P3] Frete: 0px entre nav e resumo; raio 4px e 0.9375rem fora do sistema; borda lateral de 3px do "Mais barato" (side-tab 7x); aviso da Portaria em âmbar (não é pendência). /impeccable polish.
10. [P3] "Ver cartão" usa ícone de caixa (package), que no menu significa "Opções de Frete". /impeccable clarify.
11. [P3] FAB cobre o canto do primeiro cartão em 375. /impeccable layout.

## Persona Red Flags

Casey (celular): Entregues pede 2,7 mil px para 7 entregas; no frete, o aviso dos Correios vira uma coluna estreita de 15 linhas; no escuro, o botão de tema mostra "Claro" vazando.
Alex (desktop): no frete não dá para comparar prazo em 16 de 21 serviços; em Entregues as datas quebram e a leitura da tabela fica em 2 linhas por célula.
Sam (leitor de tela): "Ver cartão" ok pelo nome acessível; nada novo bloqueante.

## Minor Observations

- "próxima em —" na meta até o JS rodar.
- "Recarregar dados salvos de HH:MM" quebra em 2 linhas no menu Opções.
- Rastreio em monoespaçada só em Entregues.

## Questions to Consider

- Os cartões de resumo das quatro páginas devem ser um componente só?
- O prazo vazio do frete é falha de consulta ou o serviço realmente não informa prazo?
