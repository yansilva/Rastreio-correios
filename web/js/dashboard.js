/**
 * Busca Instantânea, Filtros por Status e Interações do Dashboard.
 */

var activeStatusFilter = null;
var currentSearchTerm = '';
var initialRenderDone = false;

// Rótulos amigáveis para exibição de filtros
var STATUS_LABELS = {
    'nao_enviado': 'Não Enviados',
    'em_transito': 'Em Trânsito',
    'entregue': 'Entregues',
    'atrasado': 'Atrasados',
    'aguardando_retirada': 'Aguardando Retirada',
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

function applyFilters() {
    var cards = document.querySelectorAll('.order-card');
    var term = currentSearchTerm.toLowerCase().trim();
    var visibleCount = 0;

    cards.forEach(function(card) {
        var cardStatus = card.getAttribute('data-status') || '';
        var cardText = card.textContent.toLowerCase();

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
            noResults.innerHTML = '<div class="emoji"><svg class="icon" aria-hidden="true" focusable="false"><use href="#i-search"></use></svg></div><p>Nenhum pedido corresponde ao filtro ou à busca.</p>';
            cards[0].parentNode.insertBefore(noResults, cards[0]);
        }
        noResults.hidden = false;
    } else if (noResults) {
        noResults.hidden = true;
    }

    // Atualiza banner de filtro
    var banner = document.getElementById('filterBanner');
    var bannerText = document.getElementById('filterBannerText');
    if (banner && bannerText) {
        if (activeStatusFilter || term) {
            var label = activeStatusFilter ? (STATUS_LABELS[activeStatusFilter] || activeStatusFilter) : '';
            if (term) {
                label = label ? label + ' + busca: "' + term + '"' : 'Busca: "' + term + '"';
            }
            bannerText.textContent = 'Filtro ativo: ' + label;
            banner.classList.add('visible');
        } else {
            banner.classList.remove('visible');
        }
    }

    // Atualiza classes ativas nos cards de resumo e botões de filtro
    document.querySelectorAll('.dash-card').forEach(function(dc) {
        if (activeStatusFilter && dc.getAttribute('data-filter') === activeStatusFilter) {
            dc.classList.add('active');
        } else {
            dc.classList.remove('active');
        }
    });

    document.querySelectorAll('.action-chip').forEach(function(chip) {
        if (activeStatusFilter && chip.getAttribute('data-filter') === activeStatusFilter) {
            chip.classList.add('active');
        } else {
            chip.classList.remove('active');
        }
    });

    document.querySelectorAll('.filter-pill').forEach(function(pill) {
        if (pill.getAttribute('data-filter') === (activeStatusFilter || 'all')) {
            pill.classList.add('active');
        } else {
            pill.classList.remove('active');
        }
    });

    // Mostra/esconde botão Limpar
    updateClearButton();
    initialRenderDone = true;
}

function filterOrders(status) {
    if (status === 'all' || status === null || status === activeStatusFilter) {
        activeStatusFilter = null;
    } else {
        activeStatusFilter = status;
    }
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
    applyFilters();
}

// Inicializa listeners do dashboard
document.addEventListener('DOMContentLoaded', function() {
    // 1. Campo de Busca Instantânea
    var searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            currentSearchTerm = e.target.value;
            applyFilters();
        });
    }

    // 2. Botão Limpar Filtros
    var clearBtn = document.getElementById('btnClearFilter');
    if (clearBtn) {
        clearBtn.addEventListener('click', clearAllFilters);
    }

    // 3. Clique nos Cards de Resumo
    document.querySelectorAll('.dash-card[data-filter]').forEach(function(card) {
        card.addEventListener('click', function() {
            var filter = card.getAttribute('data-filter');
            filterOrders(filter);
        });
        // Cartões são divs: ativá-los com Enter ou Espaço, como um botão
        card.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                filterOrders(card.getAttribute('data-filter'));
            }
        });
    });

    // 3b. Botões da faixa "Precisam de ação" (são <button>: Enter e Espaço já funcionam)
    document.querySelectorAll('.action-chip[data-filter]').forEach(function(chip) {
        chip.addEventListener('click', function() {
            filterOrders(chip.getAttribute('data-filter'));
        });
    });

    // 4. Clique nas Pílulas de Filtro
    document.querySelectorAll('.filter-pill[data-filter]').forEach(function(pill) {
        pill.addEventListener('click', function() {
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
                applyFilters();
            }
        });
    }

    // Aplica contagem inicial
    applyFilters();
});
