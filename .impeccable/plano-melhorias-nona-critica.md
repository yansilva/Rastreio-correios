# Plano de melhorias — nona crítica de design (04/11/2026)

Autor do plano: Claude Opus 5.5, a partir do critique `.impeccable/critique/2026-11-04T14-54-53Z__localhost-relatorio-rastreio-html.md` (nota 28/40).
Executor: Claude Haiku 5.5, em sessão própria.

## Contexto (leia antes de começar)

Projeto: painel local de rastreio Correios/Tiny. Python gera HTML estático; CSS e JS ficam em `web/`. Interface em pt-BR. Leia `PRODUCT.md` e `DESIGN.md` (regras nomeadas: Zero Is Calm, One Meaning Per Color, Contrast Floor 4,5:1, Control Edge, Ramp Rule com seis tamanhos 0.75/0.8125/0.875/1/1.25/1.75rem, sem emoji, ícones SVG do sprite `Arquivos/correios/icons.py`).

Arquivos principais:
- `Arquivos/consulta_correios.py`: gera `relatorio_rastreio.html` (painel) e `pedidos_atrasados.html`. O template é string `.format()` (chaves literais dobradas `{{ }}`); a página de atrasados é f-string.
- `Arquivos/correios/cards.py`: `montar_card_pedido`, `faixa_acao`, `zero`.
- `Arquivos/frete/report.py`: gera `opcoes_frete.html` (CSS inline no f-string, chaves dobradas).
- `Arquivos/demo_data.py`: espelha o template do painel para a demonstração; mantenha-o coerente quando mudar markup do painel.
- `web/css/main.css` (tokens), `web/css/components.css` (componentes; regras mais novas ficam no fim e vencem a cascata), `web/js/dashboard.js` (filtros, visões, tabela), `web/js/app.js` (tema, toast, copiar rastreio), `web/js/logs.js` (console SSE e toasts de atualização).

Regras de trabalho:
- Não faça commit nem push. O usuário aprova no fim.
- Não chame as APIs do Tiny nem dos Correios. Para regenerar o painel e os atrasados use o cache: na pasta `Arquivos`, `python -I -c "import sys; sys.path.insert(0, '.'); import consulta_correios as c; print(c.processar(usar_cache=True))"`.
- Para regenerar `opcoes_frete.html` sem API, use o script já pronto (lê a página atual como dados): `python -I "C:\Users\yansa\AppData\Local\Temp\claude\59bb9cdfb3775a27\96fcd258-0f7c-45b3-950d-d55ac0109824\scratchpad\regera_frete.py" "C:\Users\yansa\AppData\Local\Temp\claude\59bb9cdfb3775a27\96fcd258-0f7c-45b3-950d-d55ac0109824\scratchpad\opcoes_frete_pre8.html"`. Se mudar o markup do frete de forma que o parser não leia mais a cópia, use sempre esse arquivo `opcoes_frete_pre8.html` como fonte (ele está no formato antigo, que o parser entende).
- O servidor local (`127.0.0.1:8000`, `run.py`) carrega o código Python na partida. Depois de mudar `consulta_correios.py`, `cards.py` ou `frete/report.py`, reinicie: encerre só o processo `python ... run.py` que ouve a porta 8000 (confirme o PID com `Get-NetTCPConnection -LocalPort 8000 -State Listen` e a linha de comando) e suba de novo com `Start-Process -FilePath "Arquivos\venv\Scripts\python.exe" -ArgumentList 'run.py' -WorkingDirectory <raiz> -WindowStyle Hidden`. Confira que só uma instância ouve a porta.
- PowerShell 5.1: não use `Set-Content`/`Out-File` em arquivos do projeto (gravam BOM e quebram acentos); edite com a ferramenta de edição. Arquivos podem ter CRLF.
- Não toque em `web/js/logs.js` linha ~21 (`message.includes('✅')`): é o reconhecimento de linhas do log do servidor, não UI.
- Escreva comentários e textos em português, no mesmo estilo do código ao redor.

## Tarefas (na ordem)

### T1 [P1] Tabela de atrasados que cabe e mostra a ação
Arquivo: `Arquivos/consulta_correios.py`, bloco "GERA PÁGINA DE PEDIDOS ATRASADOS" (`rows_html`, `tabela_conteudo`, `resumo_html`). CSS em `web/css/components.css`.
1. Remova a coluna "Urgência" (`urgencia-tag`): o `dias-badge` já carrega a classe `urgencia-*` (cor) e passa a dizer "N dias · Crítico/Alto/Atenção" (rótulo em caixa de frase).
2. Remova a coluna "Status" quando todas as linhas tiverem o mesmo status (hoje sempre "Em trânsito"); mantenha-a se houver mistura.
3. Todos os `<th>` com `scope="col"`; adicione `<caption class="sr-only">Pedidos com mais de 3 dias em trânsito</caption>` (crie `.sr-only` se não existir, com o padrão clip/1px).
4. `white-space: nowrap` em `.dias-badge`, `td[data-label="Rastreio"]` e `td[data-label="Ações"]`.
5. "Último evento": `max-width: 260px`, texto em até 2 linhas (`-webkit-line-clamp: 2`) e o texto completo no `title` da célula (com `escape(..., quote=True)`).
6. Celular (≤640px): `.summary` em 2 colunas; nas linhas empilhadas mostre só Pedido, Cliente (se houver), Rastreio, Dias e Ações (oculte Postagem, Último evento e Local com uma classe, por exemplo `td.col-secundaria`).
7. Vazio ("Nada atrasado"): acrescente um link de saída `<a href="relatorio_rastreio.html" class="btn-link">Ver o painel</a>`.
Aceite: com 3 atrasados de exemplo, em 1280px a tabela não rola na horizontal e "Copiar rastreio" fica visível; em 375px cada pedido ocupa no máximo ~300px. Atualize `tests/test_regerar.py` (o teste de atrasados com cliente usa `data-label="Cliente"` e `<th>Cliente</th>`; troque por `<th scope="col">Cliente</th>`).

### T2 [P2] Frete: busca, grid e selo repetido
Arquivo: `Arquivos/frete/report.py` (e `tests/test_frete.py`).
1. Campo de busca acima do filtro de valor, reaproveitando o estilo de `.search-input` do painel (copie as regras para o CSS inline): filtra por número do pedido, cliente, cidade e CEP (texto do cartão), combinado com o filtro de valor no mesmo `filtrarPorValor` (renomeie para `aplicarFiltros`). A tecla `/` foca a busca e Esc limpa. O resumo e o vazio continuam reagindo.
2. `.servicos-grid`: troque `repeat(auto-fit, minmax(200px, 1fr))` por `repeat(auto-fill, minmax(200px, 280px))` com `justify-content: start`, para um serviço sozinho não esticar.
3. Resumo no celular: grade `repeat(auto-fit, minmax(0, 1fr))` para não sobrar coluna vazia quando o cartão de prazo longo está oculto.
4. `.pedido-badge` ("Em aberto"): só renderize quando a situação do pedido for diferente da mais comum no lote.
5. Reduza travessões no corpo (o detector contou 22): no título do cartão, separe número e cliente com quebra/elemento próprio em vez de " — "; mantenha o `<title>`.
Aceite: digitar um número de pedido mostra só ele; `/` foca a busca; um pedido com um único serviço mostra um cartão de no máximo 280px alinhado à esquerda.

### T3 [P2] Painel: visão visível, botão flutuante e "Ver cartão"
Arquivos: `Arquivos/consulta_correios.py` (template, bloco `list-meta`/`options-menu`), `Arquivos/demo_data.py` (mesmo markup), `web/js/dashboard.js`, `web/css/components.css`.
1. Tire o `<select id="viewSelect">` de dentro do popover "Opções" e coloque um controle segmentado na linha `list-meta`, ao lado do contador: `<div class="view-switch" role="group" aria-label="Visão">` com três `<button type="button" data-view="cartoes|compacta|tabela" aria-pressed>` (Cartões, Compacta, Tabela). Adapte `definirVisao`/inicialização para usar os botões (mantenha a preferência `painel.visao`, a regra que esconde/desativa Tabela no celular via `matchMedia` com listener, e a classe `view-tabela` no body). Alvos de 40px no desktop, 44px no celular.
2. "Opções" fica só com Ordenar por, Recarregar dados salvos e Expandir históricos, numa grade de 2 colunas (rótulo | controle) alinhada.
3. `verCartao` (dashboard.js ~173): não grave a preferência ao voltar para Cartões (remova `gravarPreferencia('visao', 'cartoes')`).
4. Botão flutuante: dê `padding-bottom: 96px` ao `main.orders-list` e ao `.orders-table-wrap` no desktop e `80px` no celular, para o botão nunca cobrir a última ação visível ao rolar até o fim.
Aceite: a visão troca sem abrir "Opções"; `aria-pressed` acompanha; no celular o botão Tabela fica desativado; teste em `tests/test_regerar.py` que o HTML tem `class="view-switch"` e não tem `id="viewSelect"`.

### T4 [P3] Título do cartão e "Limpar filtros" sem salto
Arquivos: `Arquivos/correios/cards.py`, `Arquivos/consulta_correios.py` (chamada de `montar_card_pedido`), `Arquivos/demo_data.py`, `web/css/components.css`, `tests/test_cards.py`.
1. `montar_card_pedido` ganha parâmetros opcionais `numero_txt`, `cliente` (já existe) e `rastreio` (já existe) e monta o `<h2 class="order-title">` com spans: `<span class="order-num">Pedido Tiny #N</span>` (700), `<span class="order-client">cliente</span>` (600) e `<span class="order-code">CÓDIGO</span>` (400, 0.875rem, `--color-text-muted`). Sem cliente, só número e código. Mantenha o texto acessível equivalente ao atual (o título continua contendo "Pedido Tiny #N", o cliente e o código), e mantenha `escape`. Se `titulo` for passado sozinho (compatibilidade), continue aceitando.
2. Atualize os testes de `tests/test_cards.py` e `tests/test_regerar.py` que comparam o título exato (`<h2 class="order-title">Pedido Tiny #1 — AB123BR</h2>` e "Pedido Tiny #7001 — Maria &lt;b&gt;Souza&lt;/b&gt; (AE000000001BR)") para verificar as partes.
3. `.btn-clear-filter`: em vez de `display: none` até ficar visível, reserve o espaço (`visibility: hidden` + `display: inline-flex`) para a faixa de pílulas não pular; quando visível, `visibility: visible`. Em 1280px as 7 pílulas mais o botão devem continuar numa linha; se não couberem, mova o botão para a linha `list-meta`, ao lado do contador.

### T5 [P3] Contraste e emoji nos toasts
1. `web/js/app.js` ~135, `web/js/logs.js` ~79 e ~178: remova o "✅ " das mensagens de toast e troque `'#16a34a'` por `'#15803d'` (verde com ≥4,5:1 com texto branco).
2. `web/css/components.css` linha ~789 `.num-total { color: var(--color-primary); }`: use `var(--color-link)` (azul claro no escuro, ≥4,5:1).

### T6 [P3] Limpeza
1. `web/js/dashboard.js` ~337: remova o bloco do `filterBanner` (o elemento não existe mais no HTML) e as variáveis ligadas a ele.
2. `web/css/components.css`: remova as regras de `.filter-banner*` e `.dash-clickable` que não têm mais uso (confirme com busca no projeto antes de apagar).
3. `DESIGN.md`: corrija a frase "A página de frete ainda não carrega o arquivo e usa o fallback" (agora carrega) e documente o controle segmentado de visão e a busca do frete.

## Verificação (obrigatória antes de avisar o usuário)
1. `python -m ruff check Arquivos tests` limpo e `python -m pytest -q` todo verde (hoje 219 testes; some os novos).
2. Regenerar painel/atrasados (cache) e frete (script acima); reiniciar o servidor conforme as regras.
3. Navegador embutido (aba nova; navegue antes de redimensionar; defina o tema por `document.documentElement.dataset.theme`), em 1280px claro, 1280px escuro e 375px:
   - painel: troca de visão pelo controle segmentado, Tabela desativada no celular, botão flutuante não cobre a última ação, sem overflow;
   - atrasados: injete no DOM, só em memória, 3 linhas no formato do gerador para conferir que a tabela cabe em 1280px e a ação aparece; em 375px, altura por pedido;
   - frete: busca e `/`, cartão de serviço único com até 280px, resumo reagindo.
   Injete `*{transition:none!important;animation:none!important}` antes de medir contraste (≥4,5:1 em texto normal).
4. Detector: `"C:/Users/yansa/.claude/skills/impeccable/scripts/impeccable.cmd" detect --json relatorio_rastreio.html pedidos_atrasados.html opcoes_frete.html web` — o número de achados não pode subir (hoje 12; travessões do frete devem cair).
5. Relate ao usuário em português: o que mudou por tarefa, resultados das verificações, o que não deu para verificar, e pergunte se pode fazer commit e push.
