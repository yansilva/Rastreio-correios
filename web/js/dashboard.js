/**
 * Busca Instantânea, Filtros por Status e Interações do Dashboard.
 */

var activeStatusFilter = null;
var currentSearchTerm = '';

// Rótulos amigáveis para exibição de filtros
var STATUS_LABELS = {
    'nao_enviado': '📭 Não Enviados',
    'em_transito': '🚚 Em Trânsito',
    'entregue': '✅ Entregues',
    'atrasado': '⏰ Atrasados',
    'aguardando_retirada': '🏢 Aguardando Retirada',
    'devolvido': '↩️ Devolvidos ao Remetente',
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
        var matchesStatus = !activeStatusFilter || cardStatus === activeStatusFilter;

        // Condição 2: Busca por texto (número, cliente, código, cidade)
        var matchesSearch = !term || cardText.includes(term);

        if (matchesStatus && matchesSearch) {
            card.classList.remove('order-hidden');
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

    document.querySelectorAll('.filter-pill').forEach(function(pill) {
        if (pill.getAttribute('data-filter') === (activeStatusFilter || 'all')) {
            pill.classList.add('active');
        } else {
            pill.classList.remove('active');
        }
    });

    // Mostra/esconde botão Limpar
    updateClearButton();
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
        if (firstVisible) {
            firstVisible.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
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
    });

    // 4. Clique nas Pílulas de Filtro
    document.querySelectorAll('.filter-pill[data-filter]').forEach(function(pill) {
        pill.addEventListener('click', function() {
            var filter = pill.getAttribute('data-filter');
            filterOrders(filter);
        });
    });

    // Aplica contagem inicial
    applyFilters();
});
