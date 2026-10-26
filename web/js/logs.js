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
    try {
        const keysToRemove = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && (key.startsWith('alerta_prazo_v2_') || key.startsWith('modal_frete_'))) {
                keysToRemove.push(key);
            }
        }
        keysToRemove.forEach(k => localStorage.removeItem(k));
    } catch (e) {
        // Storage indisponível: nada a limpar
    }

    try {
        if (btn) btn.disabled = true;
        if (spinner) spinner.style.display = 'block';
        if (btnText) btnText.textContent = 'Consultando...';

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

            // Se o streaming cair antes do fim, libera o botão: sem isso ele ficava desabilitado para sempre
            eventSource.onerror = function () {
                if (eventSource) {
                    eventSource.close();
                }
                addLog('[ERRO] Conexão com o servidor perdida antes do fim da atualização.');
                showToast('❌ Conexão de logs interrompida. Tente atualizar novamente.', '#dc2626');
                if (btn) btn.disabled = false;
                if (spinner) spinner.style.display = 'none';
                if (btnText) btnText.textContent = 'Consultar Tiny e Correios';
            };
        } else if (response.status === 429) {
            let remaining = 0;
            try {
                const data = await response.json();
                remaining = Math.max(0, Number(data.remaining) || 0);
            } catch (e) {
                // Corpo inválido: mostra o aviso sem o tempo restante
            }
            const min = Math.floor(remaining / 60);
            const sec = remaining % 60;
            showToast(`⏳ Cooldown ativo! Próxima atualização permitida em ${min}m ${sec}s`, '#b45309');
            if (consoleDiv) consoleDiv.style.display = 'none';
            if (btn) btn.disabled = false;
            if (spinner) spinner.style.display = 'none';
            if (btnText) btnText.textContent = 'Consultar Tiny e Correios';
        } else {
            showToast('❌ Erro na resposta do servidor.', '#dc2626');
            if (btn) btn.disabled = false;
            if (spinner) spinner.style.display = 'none';
            if (btnText) btnText.textContent = 'Consultar Tiny e Correios';
        }
    } catch (err) {
        console.error('Falha ao conectar com o servidor:', err);
        showToast('❌ Servidor offline ou inacessível.', '#dc2626');
        if (btn) btn.disabled = false;
        if (spinner) spinner.style.display = 'none';
        if (btnText) btnText.textContent = 'Consultar Tiny e Correios';
    }
}

// Idade dos dados ("há 12 min"), atualizada na tela; acima de 2 h o aviso ganha destaque
function atualizarIdadeDados() {
    const marca = document.getElementById('dadosEm');
    const alvo = document.getElementById('dadosIdade');
    if (!marca || !alvo) return;

    const instante = new Date(marca.getAttribute('datetime'));
    if (isNaN(instante.getTime())) return;

    const minutos = Math.max(0, Math.round((Date.now() - instante.getTime()) / 60000));
    let texto;
    if (minutos < 1) {
        texto = '(agora)';
    } else if (minutos < 60) {
        texto = `(há ${minutos} min)`;
    } else if (minutos < 24 * 60) {
        texto = `(há ${Math.floor(minutos / 60)} h)`;
    } else {
        const dias = Math.floor(minutos / (24 * 60));
        texto = `(há ${dias} ${dias === 1 ? 'dia' : 'dias'})`;
    }
    alvo.textContent = texto;
    alvo.classList.toggle('meta-idade-antiga', minutos >= 120);
}

// Regera a página a partir do cache em disco, sem consultar o Tiny nem os Correios
async function regerarPagina() {
    const btn = document.getElementById('btnRegenerate');
    const rotulo = btn ? btn.textContent : '';
    const restaurar = () => {
        if (btn) {
            btn.disabled = false;
            btn.textContent = rotulo;
        }
    };

    try {
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Regerando...';
        }
        const response = await fetch(`${getBaseUrl()}/regerar`, { method: 'POST' });
        let data = {};
        try {
            data = await response.json();
        } catch (e) {
            // Corpo inválido: usa a mensagem padrão abaixo
        }

        if (response.ok) {
            showToast('✅ Página regerada com os últimos dados consultados.', '#16a34a');
            setTimeout(() => {
                window.location.href = window.location.pathname + '?updated=true';
            }, 700);
        } else {
            showToast(`❌ ${data.erro || 'Não foi possível regerar a página.'}`, '#dc2626', 6000);
            restaurar();
        }
    } catch (err) {
        console.error('Falha ao regerar a página:', err);
        showToast('❌ Servidor offline ou inacessível.', '#dc2626');
        restaurar();
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

    const btnRegenerate = document.getElementById('btnRegenerate');
    if (btnRegenerate) {
        btnRegenerate.addEventListener('click', regerarPagina);
    }

    atualizarIdadeDados();
    setInterval(atualizarIdadeDados, 30000);

    // 2. Sincronização periódica da próxima atualização com o backend
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
