/**
 * Gerenciamento de Tema, Notificações Toast e Inicialização Global.
 */

// 1. Controle de Tema (Dark / Light Mode)
function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    var themeBtn = document.getElementById('btnThemeText');
    var themeContainer = document.getElementById('btnTheme');
    if (themeBtn) {
        themeBtn.textContent = theme === 'dark' ? '☀️ Claro' : '🌙 Escuro';
    }
    if (themeContainer) {
        themeContainer.setAttribute('aria-label',
            theme === 'dark' ? 'Mudar para tema claro' : 'Mudar para tema escuro');
    }
}

function toggleTheme() {
    var current = localStorage.getItem('theme') || 'light';
    var next = current === 'light' ? 'dark' : 'light';
    setTheme(next);
}

// Inicializa o tema salvo ou preferência do sistema
(function initTheme() {
    var saved = localStorage.getItem('theme');
    if (saved) {
        setTheme(saved);
    } else {
        var prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        setTheme(prefersDark ? 'dark' : 'light');
    }
})();

// 2. Sistema de Notificações Toast
var toastTimeout = null;

function showToast(mensagem, cor, duracao) {
    cor = cor || '#2563eb';
    duracao = duracao || 3500;
    var toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        document.body.appendChild(toast);
    }

    toast.textContent = mensagem;
    toast.style.backgroundColor = cor;
    toast.style.display = 'block';

    if (toastTimeout) {
        clearTimeout(toastTimeout);
    }

    toastTimeout = setTimeout(function() {
        toast.style.display = 'none';
    }, duracao);
}

// 3. Event Listeners — inicializa ao carregar a DOM
document.addEventListener('DOMContentLoaded', function() {
    // Botão de Tema
    var btnTheme = document.getElementById('btnTheme');
    if (btnTheme) {
        btnTheme.addEventListener('click', toggleTheme);
    }

    // Botão de Atualização
    var btnUpdate = document.getElementById('btnUpdate');
    if (btnUpdate) {
        btnUpdate.addEventListener('click', function() {
            if (typeof atualizarDados === 'function') {
                atualizarDados();
            }
        });
    }

    // Verifica retorno pós-atualização via query param
    if (window.location.search.indexOf('updated=true') !== -1) {
        showToast('✅ Painel atualizado com sucesso!', '#16a34a');
        if (window.history.replaceState) {
            var cleanUrl = window.location.protocol + "//" + window.location.host + window.location.pathname;
            window.history.replaceState({ path: cleanUrl }, '', cleanUrl);
        }
    }
});
