/**
 * Busca Instantânea, Filtros por Status e Interações do Dashboard.
 */

var activeStatusFilter = null;
var currentSearchTerm = '';
var initialRenderDone = false;

// Rótulos amigáveis para exibição de filtros
var STATUS_LABELS = {
    'nao_enviado': 'Não enviados',
    'em_transito': 'Em trânsito',
    'entregue': 'Entregues',
    'atrasado': 'Atrasados',
    'aguardando_retirada': 'Aguardando retirada',
    'devolvido': 'Devolvidos ao Remetente',
};

function updateClearButton() {
    var btn = document.getElementById('btnClearFilter');
    if (!btn) return;
    if (activeStatusFilter || currentSearchTerm.trim()) {
        btn.classList.add('visible');
    } else {
        btn.classList.remove('visible');
    }
}

// Mensagens do estado vazio: filtro sem pedidos pode ser boa notícia; busca sem resultado oferece a saída
var MENSAGENS_VAZIO = {
    'atrasado': 'Nenhum pedido atrasado. Tudo dentro do prazo.',
    'aguardando_retirada': 'Nenhum objeto aguardando retirada.',
};

function preencherVazio(caixa, termo) {
    var texto;
    if (termo) {
        var filtro = activeStatusFilter ? ' em ' + (STATUS_LABELS[activeStatusFilter] || activeStatusFilter) : '';
        texto = 'Nenhum pedido encontrado para “' + termo + '”' + filtro + '.';
    } else {
        texto = MENSAGENS_VAZIO[activeStatusFilter] || 'Nenhum pedido em ' + (STATUS_LABELS[activeStatusFilter] || 'este filtro') + '.';
    }
    var icone = termo ? 'i-search' : 'i-check-circle';
    while (caixa.firstChild) caixa.removeChild(caixa.firstChild);

    var emoji = document.createElement('div');
    emoji.className = 'emoji';
    emoji.innerHTML = '<svg class="icon" aria-hidden="true" focusable="false"><use href="#' + icone + '"></use></svg>';
    var p = document.createElement('p');
    p.textContent = texto;
    caixa.appendChild(emoji);
    caixa.appendChild(p);

    if (termo || activeStatusFilter) {
        var botao = document.createElement('button');
        botao.type = 'button';
        botao.className = 'btn-link';
        botao.textContent = termo ? 'Limpar busca' : 'Mostrar todos os pedidos';
        botao.addEventListener('click', termo ? limparBusca : clearAllFilters);
        caixa.appendChild(botao);
    }
}

function limparBusca() {
    currentSearchTerm = '';
    var campo = document.getElementById('searchInput');
    if (campo) {
        campo.value = '';
        campo.focus();
    }
    salvarFiltro();
    applyFilters();
}

// Visão em tabela: uma linha por pedido visível, ordenável pelos cabeçalhos, com ações por linha
var listaPedidos = null;
var ordemTabela = { chave: 'ordem', dir: 1 };
var COLUNAS_TABELA = [
    { chave: 'pedido', rotulo: 'Pedido' },
    { chave: 'cliente', rotulo: 'Cliente' },
    { chave: 'rastreio', rotulo: 'Rastreio' },
    { chave: 'status', rotulo: 'Status' },
    { chave: 'idade', rotulo: 'Último evento' },
    { chave: 'tiny', rotulo: 'Tiny' },
];

// Visão ativa: o controle segmentado da linha da lista mostra qual está em uso (aria-pressed)
var visaoAtiva = 'cartoes';

function marcarVisao(modo) {
    document.querySelectorAll('.view-switch [data-view]').forEach(function(botao) {
        marcarPressionado(botao, botao.getAttribute('data-view') === modo);
    });
}

function definirVisao(modo) {
    if (!listaPedidos) return;
    visaoAtiva = modo;
    marcarVisao(modo);
    listaPedidos.classList.toggle('is-compact', modo === 'compacta');
    listaPedidos.hidden = modo === 'tabela';
    // Na tabela a ordem vem dos cabeçalhos: o select "Ordenar por" some para não haver dois controles de ordem
    document.body.classList.toggle('view-tabela', modo === 'tabela');
    // Na compacta o histórico fica escondido (CSS): o controle "Expandir históricos" também some ali
    document.body.classList.toggle('view-compacta', modo === 'compacta');
    var envoltorio = document.getElementById('ordersTableWrap');
    if (modo === 'tabela') {
        if (!envoltorio) {
            envoltorio = document.createElement('div');
            envoltorio.id = 'ordersTableWrap';
            envoltorio.className = 'table-wrapper orders-table-wrap';
            listaPedidos.parentNode.insertBefore(envoltorio, listaPedidos);
        }
        envoltorio.hidden = false;
        atualizarTabela();
    } else if (envoltorio) {
        envoltorio.hidden = true;
    }
}

function textoDe(elemento) {
    return elemento ? elemento.textContent.replace(/\s+/g, ' ').trim() : '';
}

function linhasDaTabela() {
    var linhas = [];
    document.querySelectorAll('.order-card:not(.order-hidden)').forEach(function(card) {
        var dias = parseFloat(card.getAttribute('data-idade'));
        var tiny = textoDe(card.querySelector('.order-tiny-status')).replace(/^Situação no Tiny:\s*/, '');
        var selo = card.querySelector('.badge');
        linhas.push({
            card: card,
            ordem: Number(card.getAttribute('data-ordem')) || 0,
            pedido: parseFloat(card.getAttribute('data-pedido')),
            cliente: card.getAttribute('data-cliente') || '',
            rastreio: card.getAttribute('data-rastreio') || '',
            status: textoDe(selo),
            urgencia: urgenciaDe(card),
            classeSelo: selo ? selo.className : 'badge',
            idade: isNaN(dias) ? null : dias,
            idadeTexto: textoDe(card.querySelector('.order-age')) || '—',
            tiny: tiny,
        });
    });
    return linhas;
}

// Prioridade do status na ordenação (a mesma ordem de urgência do servidor): quem pede ação vem primeiro
var URGENCIA_STATUS = { aguardando_retirada: 0, atrasado: 1, sem_postagem: 2, em_transito: 3, nao_enviado: 4, devolvido: 5, entregue: 6 };

function urgenciaDe(card) {
    if (/sem postagem/i.test(textoDe(card.querySelector('.badge')))) return URGENCIA_STATUS.sem_postagem;
    var melhor = 99;
    (card.getAttribute('data-status') || '').split(/\s+/).forEach(function(token) {
        if (URGENCIA_STATUS[token] !== undefined && URGENCIA_STATUS[token] < melhor) melhor = URGENCIA_STATUS[token];
    });
    return melhor;
}

function compararLinhas(a, b) {
    var chave = ordemTabela.chave === 'status' ? 'urgencia' : ordemTabela.chave;
    var va = a[chave], vb = b[chave];
    var vazioA = va === null || va === undefined || va === '' || (typeof va === 'number' && isNaN(va));
    var vazioB = vb === null || vb === undefined || vb === '' || (typeof vb === 'number' && isNaN(vb));
    if (vazioA || vazioB) return vazioA === vazioB ? a.ordem - b.ordem : (vazioA ? 1 : -1);
    var resultado = typeof va === 'number' ? va - vb : String(va).localeCompare(String(vb), 'pt-BR', { sensitivity: 'base', numeric: true });
    return (resultado * ordemTabela.dir) || (a.ordem - b.ordem);
}

function ordenarTabelaPor(chave) {
    if (ordemTabela.chave === chave) {
        ordemTabela.dir = -ordemTabela.dir;
    } else {
        ordemTabela = { chave: chave, dir: 1 };
    }
    atualizarTabela();
    // A tabela é reconstruída: o foco volta ao cabeçalho que o teclado acabou de usar
    var cabecalhos = document.querySelectorAll('#ordersTableWrap .th-sort');
    COLUNAS_TABELA.forEach(function(coluna, i) {
        if (coluna.chave === chave && cabecalhos[i]) cabecalhos[i].focus();
    });
}

function verCartao(card) {
    // Não grava a preferência: a visão escolhida pelo operador continua salva
    definirVisao('cartoes');
    card.scrollIntoView({ block: 'start' });
    card.setAttribute('tabindex', '-1');
    card.focus();
}

function celula(texto, rotulo) {
    var td = document.createElement('td');
    td.setAttribute('data-label', rotulo);
    td.textContent = texto;
    return td;
}

function botaoDeLinha(rotulo, aoClicar) {
    var botao = document.createElement('button');
    botao.type = 'button';
    botao.className = 'btn-copy';
    botao.textContent = rotulo;
    if (aoClicar) botao.addEventListener('click', aoClicar);  // "Copiar rastreio" é tratado em app.js
    return botao;
}

function atualizarTabela() {
    var envoltorio = document.getElementById('ordersTableWrap');
    if (!envoltorio || envoltorio.hidden) return;
    var linhas = linhasDaTabela().sort(compararLinhas);

    var tabela = document.createElement('table');
    tabela.className = 'orders-table';
    var cabeca = tabela.createTHead().insertRow();
    COLUNAS_TABELA.forEach(function(coluna) {
        var th = document.createElement('th');
        th.scope = 'col';
        var ativa = ordemTabela.chave === coluna.chave;
        th.setAttribute('aria-sort', ativa ? (ordemTabela.dir === 1 ? 'ascending' : 'descending') : 'none');
        var botao = document.createElement('button');
        botao.type = 'button';
        botao.className = 'th-sort';
        botao.textContent = coluna.rotulo;
        if (ativa) {
            // O glifo é só visual: o estado já chega a leitores de tela por aria-sort
            var seta = document.createElement('span');
            seta.setAttribute('aria-hidden', 'true');
            seta.textContent = ordemTabela.dir === 1 ? ' ▲' : ' ▼';
            botao.appendChild(seta);
        }
        botao.addEventListener('click', function() { ordenarTabelaPor(coluna.chave); });
        th.appendChild(botao);
        cabeca.appendChild(th);
    });
    var thAcoes = document.createElement('th');
    thAcoes.scope = 'col';
    thAcoes.textContent = 'Ações';
    cabeca.appendChild(thAcoes);

    var corpo = tabela.createTBody();
    if (!linhas.length) {
        var tdVazio = corpo.insertRow().insertCell();
        tdVazio.colSpan = COLUNAS_TABELA.length + 1;
        tdVazio.className = 'empty-state';
        tdVazio.setAttribute('role', 'status');
        preencherVazio(tdVazio, currentSearchTerm.toLowerCase().trim());
    }
    linhas.forEach(function(l) {
        var tr = corpo.insertRow();
        tr.appendChild(celula(isNaN(l.pedido) ? '—' : '#' + l.pedido, 'Pedido'));
        tr.appendChild(celula(l.cliente || '—', 'Cliente'));
        tr.appendChild(celula(l.rastreio || '—', 'Rastreio'));
        var tdStatus = document.createElement('td');
        tdStatus.setAttribute('data-label', 'Status');
        var selo = document.createElement('span');
        selo.className = l.classeSelo;
        selo.textContent = l.status || '—';
        tdStatus.appendChild(selo);
        tr.appendChild(tdStatus);
        tr.appendChild(celula(l.idadeTexto.replace(/^Último evento\s*/, '') || '—', 'Último evento'));
        tr.appendChild(celula(l.tiny || '—', 'Tiny'));

        var tdAcoes = document.createElement('td');
        tdAcoes.setAttribute('data-label', 'Ações');
        tdAcoes.className = 'orders-table-actions';
        if (l.rastreio) {
            var copiar = botaoDeLinha('Copiar rastreio', null);
            copiar.setAttribute('data-copy', l.rastreio);
            // O nome acessível começa com o texto visível (WCAG 2.5.3, Label in Name)
            copiar.setAttribute('aria-label', 'Copiar rastreio ' + l.rastreio);
            tdAcoes.appendChild(copiar);
        }
        var ver = botaoDeLinha('Ver cartão', function() { verCartao(l.card); });
        ver.classList.add('btn-ver-cartao');
        if (!isNaN(l.pedido)) ver.setAttribute('aria-label', 'Ver cartão do pedido #' + l.pedido);
        tdAcoes.appendChild(ver);
        tr.appendChild(tdAcoes);
    });

    while (envoltorio.firstChild) envoltorio.removeChild(envoltorio.firstChild);
    envoltorio.appendChild(tabela);
}

function marcarPressionado(elemento, ativo) {
    elemento.classList.toggle('active', ativo);
    elemento.setAttribute('aria-pressed', ativo ? 'true' : 'false');
}

// Texto que a busca enxerga: como textContent, mas sem os .sr-only (descrição do selo para leitor de tela).
// Sem isso, buscar "trânsito" acharia cartões só pela descrição que nenhum operador vê.
function textoDeBusca(no) {
    if (no.nodeType === Node.TEXT_NODE) return no.nodeValue;
    if (no.nodeType !== Node.ELEMENT_NODE || no.classList.contains('sr-only')) return '';
    var texto = '';
    for (var i = 0; i < no.childNodes.length; i++) texto += textoDeBusca(no.childNodes[i]);
    return texto;
}

function applyFilters() {
    var cards = document.querySelectorAll('.order-card');
    var term = currentSearchTerm.toLowerCase().trim();
    var visibleCount = 0;

    cards.forEach(function(card) {
        var cardStatus = card.getAttribute('data-status') || '';
        var cardText = textoDeBusca(card).toLowerCase();

        // Condição 1: Filtro de status
        // data-status aceita várias categorias separadas por espaço (ex.: "em_transito atrasado")
        var matchesStatus = !activeStatusFilter || cardStatus.split(/\s+/).indexOf(activeStatusFilter) !== -1;

        // Condição 2: Busca por texto (número, cliente, código, cidade)
        var matchesSearch = !term || cardText.includes(term);

        if (matchesStatus && matchesSearch) {
            if (card.classList.contains('order-hidden')) {
                card.classList.remove('order-hidden');
                // Anima só quando o cartão reaparece por ação do usuário, nunca na carga da página
                if (initialRenderDone) {
                    card.classList.remove('is-entering');
                    void card.offsetWidth;
                    card.classList.add('is-entering');
                }
            }
            visibleCount++;
        } else {
            card.classList.add('order-hidden');
        }
    });

    // Atualiza contador na interface — texto curto e natural
    var countDisplay = document.getElementById('filterCount');
    if (countDisplay) {
        var total = cards.length;
        if (activeStatusFilter || term) {
            countDisplay.textContent = visibleCount + ' de ' + total + ' pedidos';
        } else {
            countDisplay.textContent = total + ' pedidos';
        }
    }

    // Estado vazio quando a busca ou o filtro não encontra nenhum pedido
    var noResults = document.getElementById('noResults');
    if (cards.length && visibleCount === 0) {
        if (!noResults) {
            noResults = document.createElement('div');
            noResults.id = 'noResults';
            noResults.className = 'empty-state';
            noResults.setAttribute('role', 'status');
            cards[0].parentNode.insertBefore(noResults, cards[0]);
        }
        preencherVazio(noResults, term);
        noResults.hidden = false;
    } else if (noResults) {
        noResults.hidden = true;
    }

    // Atualiza classes ativas nos cards de resumo e botões de filtro
    // aria-pressed acompanha a classe: o estado do filtro também chega a leitores de tela
    document.querySelectorAll('.action-chip').forEach(function(el) {
        marcarPressionado(el, !!activeStatusFilter && el.getAttribute('data-filter') === activeStatusFilter);
    });

    document.querySelectorAll('.filter-pill').forEach(function(pill) {
        marcarPressionado(pill, pill.getAttribute('data-filter') === (activeStatusFilter || 'all'));
    });

    // Mostra/esconde botão Limpar
    updateClearButton();
    initialRenderDone = true;
    atualizarTabela();
}

// Filtro e busca sobrevivem à atualização da página (sessionStorage: só nesta aba)
function salvarFiltro() {
    try {
        sessionStorage.setItem('painel.filtro', JSON.stringify({ status: activeStatusFilter, busca: currentSearchTerm }));
    } catch (e) {
        // Sem persistência: o filtro vale só enquanto a página estiver aberta
    }
}

function restaurarFiltro() {
    try {
        var salvo = JSON.parse(sessionStorage.getItem('painel.filtro') || 'null');
        if (!salvo) return;
        var statusValidos = ['nao_enviado', 'em_transito', 'entregue', 'atrasado', 'aguardando_retirada', 'devolvido'];
        if (statusValidos.indexOf(salvo.status) !== -1) activeStatusFilter = salvo.status;
        if (typeof salvo.busca === 'string') {
            currentSearchTerm = salvo.busca;
            var campo = document.getElementById('searchInput');
            if (campo) campo.value = salvo.busca;
        }
    } catch (e) {
        // Dado inválido ou storage indisponível: começa sem filtro
    }
}

function filterOrders(status) {
    if (status === 'all' || status === null || status === activeStatusFilter) {
        activeStatusFilter = null;
    } else {
        activeStatusFilter = status;
    }
    salvarFiltro();
    applyFilters();

    if (activeStatusFilter) {
        var firstVisible = document.querySelector('.order-card:not(.order-hidden)');
        var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (firstVisible) {
            firstVisible.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
        }
    }
}

// Ordenação: a ordem de urgência vem do servidor; guardamos o índice inicial para poder voltar a ela
function ordenarPedidos(modo) {
    var lista = document.querySelector('.orders-list');
    if (!lista) return;
    var cartoes = Array.prototype.slice.call(lista.querySelectorAll('.order-card'));
    var numero = function(valor) { var n = parseFloat(valor); return isNaN(n) ? null : n; };

    cartoes.sort(function(a, b) {
        var ia = numero(a.getAttribute('data-idade')), ib = numero(b.getAttribute('data-idade'));
        var pa = numero(a.getAttribute('data-pedido')), pb = numero(b.getAttribute('data-pedido'));
        var porOrdem = Number(a.getAttribute('data-ordem')) - Number(b.getAttribute('data-ordem'));
        // Itens sem o dado vão para o fim, nas duas direções
        if (modo === 'recente' || modo === 'antigo') {
            if (ia === null || ib === null) return ia === ib ? porOrdem : (ia === null ? 1 : -1);
            return (modo === 'recente' ? ia - ib : ib - ia) || porOrdem;
        }
        if (modo === 'pedido') {
            if (pa === null || pb === null) return pa === pb ? porOrdem : (pa === null ? 1 : -1);
            return (pb - pa) || porOrdem;
        }
        return porOrdem;
    });

    cartoes.forEach(function(cartao) { lista.appendChild(cartao); });
}

// Preferências da tela (ordem e históricos abertos) sobrevivem à atualização da página
function lerPreferencia(chave) {
    try {
        return localStorage.getItem('painel.' + chave);
    } catch (e) {
        return null;
    }
}

function gravarPreferencia(chave, valor) {
    try {
        localStorage.setItem('painel.' + chave, valor);
    } catch (e) {
        // Sem persistência: a escolha vale só para esta página
    }
}

function definirHistoricos(abrir) {
    var botao = document.getElementById('btnToggleHistory');
    document.querySelectorAll('.order-card details.order-history').forEach(function(d) { d.open = abrir; });
    if (botao) botao.textContent = abrir ? 'Recolher históricos' : 'Expandir históricos';
}

function alternarHistoricos() {
    var detalhes = document.querySelectorAll('.order-card:not(.order-hidden) details.order-history');
    if (!detalhes.length) return;
    var abrir = Array.prototype.some.call(detalhes, function(d) { return !d.open; });
    definirHistoricos(abrir);
    gravarPreferencia('historicos', abrir ? 'abertos' : 'recolhidos');
}

function clearAllFilters() {
    activeStatusFilter = null;
    currentSearchTerm = '';
    var searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.value = '';
    }
    salvarFiltro();
    applyFilters();
}

// Inicializa listeners do dashboard
document.addEventListener('DOMContentLoaded', function() {
    // 1. Campo de Busca Instantânea
    var searchInput = document.getElementById('searchInput');
    // Celular: placeholder curto para caber em 360px; o desktop mantém a lista completa (data-placeholder-*)
    if (searchInput && window.matchMedia) {
        var telaPequena = window.matchMedia('(max-width: 640px)');
        var ajustarPlaceholder = function() {
            var curto = searchInput.getAttribute('data-placeholder-curto');
            var longo = searchInput.getAttribute('data-placeholder-longo');
            var texto = telaPequena.matches && curto ? curto : longo;
            // Sem valor nos atributos, mantém o placeholder que já está no HTML (evita o texto "null")
            if (texto) searchInput.placeholder = texto;
        };
        ajustarPlaceholder();
        if (telaPequena.addEventListener) telaPequena.addEventListener('change', ajustarPlaceholder);
    }
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            currentSearchTerm = e.target.value;
            salvarFiltro();
            applyFilters();
        });
    }

    // 2. Botão Limpar Filtros
    var clearBtn = document.getElementById('btnClearFilter');
    if (clearBtn) {
        clearBtn.addEventListener('click', clearAllFilters);
    }

    // 3. Os cartões de resumo só informam; quem filtra são a faixa "Precisam de ação" e as pílulas.
    // 3b. Botões da faixa "Precisam de ação" (são <button>: Enter e Espaço já funcionam)
    document.querySelectorAll('.action-chip[data-filter]').forEach(function(chip) {
        chip.addEventListener('click', function() {
            if (chip.getAttribute('aria-disabled') === 'true') return;
            filterOrders(chip.getAttribute('data-filter'));
        });
    });

    // 4. Clique nas Pílulas de Filtro
    document.querySelectorAll('.filter-pill[data-filter]').forEach(function(pill) {
        pill.addEventListener('click', function() {
            if (pill.getAttribute('aria-disabled') === 'true') return;
            var filter = pill.getAttribute('data-filter');
            filterOrders(filter);
        });
    });

    // 5. Ordenação e histórico recolhido/expandido
    document.querySelectorAll('.order-card').forEach(function(cartao, indice) {
        cartao.setAttribute('data-ordem', indice);
    });
    var seletorOrdem = document.getElementById('sortSelect');
    if (seletorOrdem) {
        seletorOrdem.addEventListener('change', function() {
            ordenarPedidos(seletorOrdem.value);
            gravarPreferencia('ordem', seletorOrdem.value);
        });
        // Restaura a ordem escolhida antes da última atualização (só valores que o seletor oferece)
        var ordemSalva = lerPreferencia('ordem');
        var existe = ordemSalva && Array.prototype.some.call(seletorOrdem.options, function(o) { return o.value === ordemSalva; });
        if (existe && ordemSalva !== 'urgencia') {
            seletorOrdem.value = ordemSalva;
            ordenarPedidos(ordemSalva);
        }
    }
    if (lerPreferencia('historicos') === 'abertos') {
        definirHistoricos(true);
    }
    var botaoHistoricos = document.getElementById('btnToggleHistory');
    if (botaoHistoricos) {
        botaoHistoricos.addEventListener('click', alternarHistoricos);
    }

    // 5a. Visão (cartões, compacta ou tabela ordenável), lembrada entre atualizações
    var controleVisao = document.querySelector('.view-switch');
    listaPedidos = document.querySelector('.orders-list');
    if (controleVisao && listaPedidos) {
        var botaoTabela = controleVisao.querySelector('[data-view="tabela"]');
        // No celular a tabela vira uma pilha de campos (7 linhas por pedido) e perde a ordenação: fica indisponível.
        // aria-disabled (e não disabled) mantém o botão focável e tocável, para o motivo chegar a leitores e ao toque.
        var motivoTabela = 'Tabela indisponível no celular';
        var dicaTabela = document.createElement('span');
        dicaTabela.id = 'dicaTabelaCelular';
        dicaTabela.className = 'sr-only';
        dicaTabela.textContent = motivoTabela + '. A preferência é mantida e a tabela volta em tela maior.';
        if (botaoTabela) {
            controleVisao.appendChild(dicaTabela);
            botaoTabela.setAttribute('aria-describedby', dicaTabela.id);
        }
        var consultaCelular = window.matchMedia ? window.matchMedia('(max-width: 640px)') : null;
        var celular = !!(consultaCelular && consultaCelular.matches);
        function ajustarTabelaAoTamanho(pequeno) {
            if (botaoTabela) {
                if (pequeno) {
                    botaoTabela.setAttribute('aria-disabled', 'true');
                    botaoTabela.title = motivoTabela;
                } else {
                    botaoTabela.removeAttribute('aria-disabled');
                    botaoTabela.removeAttribute('title');
                }
            }
            // A tela encolheu (ou o aparelho girou) com a tabela aberta: mostra a compacta, mas NÃO grava a preferência
            if (pequeno && visaoAtiva === 'tabela') definirVisao('compacta');
            // Voltou a tela grande: a tabela reaparece se for a preferência salva
            if (!pequeno && lerPreferencia('visao') === 'tabela' && visaoAtiva !== 'tabela') definirVisao('tabela');
        }
        ajustarTabelaAoTamanho(celular);
        if (consultaCelular && consultaCelular.addEventListener) {
            consultaCelular.addEventListener('change', function(e) { ajustarTabelaAoTamanho(e.matches); });
        }
        controleVisao.querySelectorAll('[data-view]').forEach(function(botao) {
            botao.addEventListener('click', function() {
                if (botao.getAttribute('aria-disabled') === 'true') {
                    showToast(motivoTabela + '.', 'var(--color-warning)', 3000);
                    return;
                }
                var modo = botao.getAttribute('data-view');
                definirVisao(modo);
                gravarPreferencia('visao', modo);
            });
        });
        var visaoSalva = lerPreferencia('visao');
        if (visaoSalva === 'tabela' && celular) visaoSalva = 'compacta';
        definirVisao(visaoSalva === 'compacta' || visaoSalva === 'tabela' ? visaoSalva : 'cartoes');
    }

    // 5c. Contagem nas pílulas e cartões de resumo zerados desativados (um clique ali só esvaziaria a lista)
    var totais = {};
    // Conta todos os cartões: o filtro "Todos" mostra todos, e order-hidden é o estado de filtro, não de dados
    document.querySelectorAll('.order-card').forEach(function(card) {
        (card.getAttribute('data-status') || '').split(/\s+/).forEach(function(t) { if (t) totais[t] = (totais[t] || 0) + 1; });
    });
    document.querySelectorAll('.filter-pill[data-filter]').forEach(function(pill) {
        var filtro = pill.getAttribute('data-filter');
        var n = filtro === 'all' ? document.querySelectorAll('.order-card').length : (totais[filtro] || 0);
        var marca = document.createElement('span');
        marca.className = 'pill-count';
        marca.textContent = String(n);
        pill.appendChild(marca);
    });
    // Pílulas e chips sem pedidos não filtram (a lista só ficaria vazia) nem entram na ordem do Tab; "Todos" fica sempre ativa
    document.querySelectorAll('.filter-pill[data-filter], .action-chip[data-filter]').forEach(function(el) {
        var filtro = el.getAttribute('data-filter');
        if (filtro !== 'all' && !totais[filtro]) {
            el.setAttribute('aria-disabled', 'true');
            el.setAttribute('tabindex', '-1');
            el.title = 'Nenhum pedido neste status';
        }
    });
    // Pílulas ativas primeiro: as zeradas vão para o fim da faixa, onde não escondem o filtro útil
    var faixaPilulas = document.querySelector('.filter-pills');
    if (faixaPilulas) {
        Array.prototype.slice.call(faixaPilulas.querySelectorAll('.filter-pill[aria-disabled="true"]')).forEach(function(pill) {
            faixaPilulas.appendChild(pill);
        });
        // O foco do Tab não rola uma pílula já parcialmente visível; esta rolagem leva cada uma até ficar inteira
        faixaPilulas.addEventListener('focusin', function(e) {
            if (e.target.classList && e.target.classList.contains('filter-pill')) {
                e.target.scrollIntoView({ block: 'nearest', inline: 'nearest' });
            }
        });
    }

    // 5b. O menu Opções (popover no desktop) fecha com Esc ou com um clique fora dele
    var menuOpcoes = document.querySelector('.options-menu');
    if (menuOpcoes) {
        document.addEventListener('click', function(e) {
            if (menuOpcoes.open && !menuOpcoes.contains(e.target)) menuOpcoes.open = false;
        });
        // Esc fecha o menu de qualquer ponto da página; o foco só volta ao botão quando estava dentro dele
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && menuOpcoes.open) {
                var estavaDentro = menuOpcoes.contains(document.activeElement);
                menuOpcoes.open = false;
                if (estavaDentro) menuOpcoes.querySelector('summary').focus();
            }
        });
    }

    // 6. Atalho "/" foca a busca (fora de campos de texto); Esc limpa a busca
    document.addEventListener('keydown', function(e) {
        var alvo = e.target;
        var emCampo = alvo && (alvo.tagName === 'INPUT' || alvo.tagName === 'TEXTAREA' || alvo.tagName === 'SELECT' || alvo.isContentEditable);
        if (e.key === '/' && !emCampo && !e.ctrlKey && !e.metaKey && !e.altKey) {
            var busca = document.getElementById('searchInput');
            if (busca) {
                e.preventDefault();
                busca.focus();
                busca.select();
            }
        }
    });
    if (searchInput) {
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && searchInput.value) {
                searchInput.value = '';
                currentSearchTerm = '';
                salvarFiltro();
                applyFilters();
            }
        });
    }

    // Restaura filtro e busca da sessão antes da primeira renderização
    restaurarFiltro();

    // Aplica contagem inicial
    applyFilters();
});
