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

// Texto do toast: branco ou escuro, o que tiver mais contraste sobre o fundo já resolvido pelo navegador.
// Os tons de sucesso e erro do tema escuro são claros, então o texto deve ser escuro neles (0,179 é o ponto de empate).
function corTextoToast(fundoCss) {
    var n = (fundoCss || '').match(/[\d.]+/g);
    if (!n || n.length < 3) return 'var(--console-text)';
    var linear = function(c) {
        c = Number(c) / 255;
        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    };
    var luminancia = 0.2126 * linear(n[0]) + 0.7152 * linear(n[1]) + 0.0722 * linear(n[2]);
    return luminancia > 0.179 ? 'var(--console-bg)' : 'var(--console-text)';
}

var toastDuracao = 3500;
var toastPersistente = false;

function fecharToast() {
    var toast = document.getElementById('toast');
    if (toast) toast.style.display = 'none';
    toastTimeout = null;
}

function agendarFechamento(duracao) {
    if (toastTimeout) clearTimeout(toastTimeout);
    toastTimeout = null;
    // Erros ficam abertos até o usuário fechar: sem temporizador
    if (toastPersistente) return;
    toastTimeout = setTimeout(fecharToast, duracao);
}

function pausarFechamento() {
    if (toastTimeout) clearTimeout(toastTimeout);
    toastTimeout = null;
}

// Hover, foco ou toque seguram o toast (para dar tempo de copiar); um toque ou clique fecha,
// exceto quando o usuário selecionou texto dentro dele
function ligarInteracaoToast(toast) {
    if (toast.dataset.interativo) return;
    toast.dataset.interativo = '1';
    toast.tabIndex = -1;
    toast.addEventListener('mouseenter', pausarFechamento);
    toast.addEventListener('focusin', pausarFechamento);
    toast.addEventListener('touchstart', pausarFechamento);
    toast.addEventListener('mouseleave', function() { agendarFechamento(toastDuracao); });
    toast.addEventListener('focusout', function() { agendarFechamento(toastDuracao); });
    toast.addEventListener('touchend', function() { agendarFechamento(toastDuracao); });
    toast.addEventListener('click', function() {
        var selecao = window.getSelection ? window.getSelection().toString() : '';
        if (!selecao && !toastPersistente) fecharToast();
    });
}

// Botão "Fechar" do toast de erro: focável pelo teclado, fecha o toast
function botaoFecharToast() {
    var botao = document.createElement('button');
    botao.type = 'button';
    botao.textContent = 'Fechar';
    botao.style.cssText = 'margin-left:12px;padding:2px 10px;background:transparent;color:inherit;border:1px solid currentColor;border-radius:var(--radius-sm);font:inherit;cursor:pointer;';
    botao.addEventListener('click', fecharToast);
    return botao;
}

// tipo 'erro': role="alert", fica aberto até o usuário fechar. Sem tipo: role="status", some sozinho
function showToast(mensagem, cor, duracao, tipo) {
    cor = cor || 'var(--color-primary)';
    duracao = duracao || 3500;
    var erro = tipo === 'erro';
    var toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        document.body.appendChild(toast);
    }

    toast.setAttribute('role', erro ? 'alert' : 'status');
    if (erro) {
        toast.removeAttribute('aria-live');
    } else {
        toast.setAttribute('aria-live', 'polite');
    }
    var texto = document.createElement('span');
    texto.textContent = mensagem;
    toast.replaceChildren(texto);
    toast.style.backgroundColor = cor;
    // Lê a cor já resolvida (mesmo quando cor é variável do tema) para escolher o texto
    toast.style.color = corTextoToast(getComputedStyle(toast).backgroundColor);
    // Permite selecionar o texto: o código de rastreio pode precisar ser copiado à mão
    toast.style.userSelect = 'text';
    if (erro) {
        toast.appendChild(botaoFecharToast());
    }
    toast.style.display = 'block';

    toastPersistente = erro;
    toastDuracao = duracao;
    ligarInteracaoToast(toast);
    agendarFechamento(duracao);
}

// 2b. Copiar o código de rastreio: um só ouvinte para os botões do painel, da tabela e da página de atrasados
// Caminho antigo: textarea oculto + execCommand. Serve quando a Clipboard API falta ou recusa (http na rede local, no celular)
function copiarPeloCampoOculto(codigo, aoCopiar, aoFalhar) {
    // O select() tira o foco de quem usa teclado: ele volta para o mesmo lugar depois
    var focoAnterior = document.activeElement;
    var campo = document.createElement('textarea');
    campo.value = codigo;
    campo.setAttribute('readonly', '');
    campo.style.position = 'fixed';
    campo.style.opacity = '0';
    document.body.appendChild(campo);
    var copiou = false;
    try {
        campo.select();
        copiou = document.execCommand('copy');
    } catch (e) {
        copiou = false;
    } finally {
        document.body.removeChild(campo);
        if (focoAnterior && focoAnterior.focus) focoAnterior.focus({ preventScroll: true });
    }
    if (copiou) {
        aoCopiar();
    } else {
        aoFalhar();
    }
}

function copiarRastreio(botao) {
    var codigo = botao.getAttribute('data-copy');
    var aoCopiar = function() {
        showToast('Rastreio ' + codigo + ' copiado', 'var(--color-success)', 2000);
    };
    var aoFalhar = function() {
        // Sem cópia automática: o código fica no toast para ser copiado à mão
        showToast('Copie manualmente: ' + codigo, 'var(--color-danger)', 5000, 'erro');
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(codigo).then(aoCopiar, function() {
            // A API existe, mas recusou (contexto não seguro, permissão): tenta o caminho antigo
            copiarPeloCampoOculto(codigo, aoCopiar, aoFalhar);
        });
        return;
    }
    copiarPeloCampoOculto(codigo, aoCopiar, aoFalhar);
}

document.addEventListener('click', function(e) {
    var botao = e.target && e.target.closest ? e.target.closest('.btn-copy[data-copy]') : null;
    if (botao) copiarRastreio(botao);
});

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
        showToast('Painel atualizado com sucesso!', 'var(--color-success)');
        if (window.history.replaceState) {
            var cleanUrl = window.location.protocol + "//" + window.location.host + window.location.pathname;
            window.history.replaceState({ path: cleanUrl }, '', cleanUrl);
        }
    }
});
