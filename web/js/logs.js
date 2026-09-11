/**
 * Streaming SSE de Logs, Controle do Botão de Atualização e Timer em Tempo Real.
 */

let eventSource = null;

function getBaseUrl() {
    return window.location.protocol === 'file:' ? 'http://localhost:8000' : '';
}

function addLog(message) {
    const consoleBody = document.getElementById('consoleBody');
    if (!consoleBody) return;

    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.textContent = message;

    if (message.includes('❌') || message.includes('[ERRO]')) {
        entry.style.color = '#f87171';
    } else if (message.includes('✅')) {
        entry.style.color = '#4ade80';
    } else if (message.includes('🚀') || message.includes('>>')) {
        entry.style.color = '#60a5fa';
    }

    consoleBody.appendChild(entry);
    consoleBody.scrollTop = consoleBody.scrollHeight;
}

async function atualizarDados() {
    const btn = document.getElementById('btnUpdate');
    const spinner = document.getElementById('spinner');
    const btnText = document.getElementById('btnUpdateText');
    const consoleDiv = document.getElementById('console');
    const consoleBody = document.getElementById('consoleBody');

    // Limpa caches locais de alertas antigos
    const keysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && (key.startsWith('alerta_prazo_v2_') || key.startsWith('modal_frete_'))) {
            keysToRemove.push(key);
        }
    }
    keysToRemove.forEach(k => localStorage.removeItem(k));

    try {
        if (btn) btn.disabled = true;
        if (spinner) spinner.style.display = 'block';
        if (btnText) btnText.textContent = 'Atualizando...';

        if (consoleBody) consoleBody.innerHTML = '';
        if (consoleDiv) consoleDiv.style.display = 'block';
        addLog('>> Conectando ao servidor para sincronização...');

        const baseUrl = getBaseUrl();
        const response = await fetch(`${baseUrl}/atualizar`, { method: 'POST' });

        if (response.status === 200) {
            // Conecta ao streaming de logs via Server-Sent Events (SSE)
            if (eventSource) {
                eventSource.close();
            }

            eventSource = new EventSource(`${baseUrl}/logs`);

            eventSource.onmessage = function (event) {
                if (!event.data || event.data === ': keep-alive') return;

                addLog(event.data);

                if (event.data.includes('✅ PROCESSO FINALIZADO')) {
                    eventSource.close();
                    showToast('✅ Atualização concluída com sucesso!', '#16a34a');
                    setTimeout(() => {
                        const targetUrl = window.location.pathname + '?updated=true';
                        window.location.href = targetUrl;
                    }, 1800);
                }
            };

            eventSource.onerror = function () {
                if (eventSource) {
                    eventSource.close();
                }
            };
        } else if (response.status === 429) {
            const data = await response.json();
            const min = Math.floor(data.remaining / 60);
            const sec = data.remaining % 60;
            showToast(`⏳ Cooldown ativo! Próxima atualização permitida em ${min}m ${sec}s`, '#d97706');
            if (consoleDiv) consoleDiv.style.display = 'none';
            if (btn) btn.disabled = false;
            if (spinner) spinner.style.display = 'none';
            if (btnText) btnText.textContent = '🔄 Atualizar Dados';
        } else {
            showToast('❌ Erro na resposta do servidor.', '#dc2626');
            if (btn) btn.disabled = false;
            if (spinner) spinner.style.display = 'none';
            if (btnText) btnText.textContent = '🔄 Atualizar Dados';
        }
    } catch (err) {
        console.error('Falha ao conectar com o servidor:', err);
        showToast('❌ Servidor offline ou inacessível.', '#dc2626');
        if (btn) btn.disabled = false;
        if (spinner) spinner.style.display = 'none';
        if (btnText) btnText.textContent = '🔄 Atualizar Dados';
    }
}

// Monitora o horário da próxima atualização automática com contagem regressiva fluida
let remainingSeconds = 0;
let nextTimeStr = '--:--';

function atualizarElementoContador() {
    const timerEl = document.getElementById('countdown-timer') || document.getElementById('autoUpdateTimer');
    if (!timerEl) return;

    if (remainingSeconds <= 0) {
        timerEl.textContent = 'iniciando verificação...';
    } else {
        const minutes = Math.floor(remainingSeconds / 60);
        const seconds = remainingSeconds % 60;
        timerEl.textContent = `${minutes}m ${seconds.toString().padStart(2, '0')}s (às ${nextTimeStr})`;
    }
}

async function verificarProximaAtualizacao() {
    try {
        const baseUrl = getBaseUrl();
        const res = await fetch(`${baseUrl}/proxima-atualizacao`);
        if (res.ok) {
            const data = await res.json();
            remainingSeconds = data.remaining || 0;
            nextTimeStr = data.next_time || '--:--';
            atualizarElementoContador();
        } else {
            const timerEl = document.getElementById('countdown-timer') || document.getElementById('autoUpdateTimer');
            if (timerEl) {
                timerEl.textContent = 'indisponível (erro do servidor)';
            }
        }
    } catch {
        const timerEl = document.getElementById('countdown-timer') || document.getElementById('autoUpdateTimer');
        if (timerEl) {
            timerEl.textContent = 'indisponível (servidor offline)';
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // 1. Botão de Atualizar
    const btnUpdate = document.getElementById('btnUpdate');
    if (btnUpdate) {
        btnUpdate.addEventListener('click', atualizarDados);
    }

    // 2. Botão de Tema
    const btnTheme = document.getElementById('btnTheme');
    if (btnTheme) {
        btnTheme.addEventListener('click', toggleTheme);
    }

    // 3. Sincronização periódica da próxima atualização com o backend
    verificarProximaAtualizacao();
    setInterval(verificarProximaAtualizacao, 10000);

    // 4. Decremento visual fluido a cada segundo
    setInterval(() => {
        if (remainingSeconds > 0) {
            remainingSeconds--;
            atualizarElementoContador();
        }
    }, 1000);
});
