/**
 * Gerenciamento de Tema, Notificações Toast e Inicialização Global.
 * Responsabilidade Única: Controle exclusivo de tema e toasts do painel.
 */

// Acesso ao localStorage pode falhar (modo privado, cookies bloqueados): o tema segue sem persistir
function readStoredTheme() {
    try {
        return localStorage.getItem('theme');
    } catch (e) {
        return null;
    }
}

function storeTheme(theme) {
    try {
        localStorage.setItem('theme', theme);
    } catch (e) {
        // Sem persistência: o tema vale só para esta página
    }
}

// 1. Controle de Tema (Dark / Light Mode)
function getCurrentTheme() {
    return document.documentElement.getAttribute('data-theme') || readStoredTheme() || 'light';
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    storeTheme(theme);

    var themeBtn = document.getElementById('btnThemeText');
    var themeContainer = document.getElementById('btnTheme');

    if (themeBtn) {
        // O ícone (sol ou lua) é alternado por CSS conforme o tema; aqui só o texto
        themeBtn.textContent = theme === 'dark' ? 'Claro' : 'Escuro';
    }
    if (themeContainer) {
        themeContainer.setAttribute('aria-label',
            theme === 'dark' ? 'Mudar para tema claro' : 'Mudar para tema escuro');
    }
}

function toggleTheme() {
    var current = getCurrentTheme();
    var next = current === 'light' ? 'dark' : 'light';
    // Sem transições durante a troca: cada elemento mudaria de cor em um ritmo e a tela piscaria
    var raiz = document.documentElement;
    raiz.classList.add('theme-switching');
    setTheme(next);
    window.setTimeout(function() { raiz.classList.remove('theme-switching'); }, 80);
}

// Inicializa o tema imediatamente para evitar FOUC (Flash of Unstyled Content)
(function initTheme() {
    var saved = readStoredTheme();
    if (saved) {
        document.documentElement.setAttribute('data-theme', saved);
    } else {
        var prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
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

// 3. Inicialização e Event Listeners exclusivos do app.js
document.addEventListener('DOMContentLoaded', function() {
    // Sincroniza o estado visual do botão com o tema ativo
    setTheme(getCurrentTheme());

    // Registra listener exclusivo do Botão de Tema (com prevenção contra duplicatas)
    var btnTheme = document.getElementById('btnTheme');
    if (btnTheme) {
        btnTheme.removeEventListener('click', toggleTheme);
        btnTheme.addEventListener('click', toggleTheme);
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
