/**
 * Streaming SSE de Logs, Controle do Botão de Atualização e Timer em Tempo Real.
 */

let eventSource = null;

function getBaseUrl() {
    return window.location.protocol === 'file:' ? 'http://localhost:8000' : '';
}

const ROTULO_CONSULTA = 'Consultar Tiny e Correios';

// Texto visível e nome acessível do botão andam juntos. O aria-label do HTML traz o rótulo normal,
// então durante a consulta ele vira "Consultando..." e volta ao rótulo no fim
function ajustarBotaoConsulta(consultando) {
    const btn = document.getElementById('btnUpdate');
    const btnText = document.getElementById('btnUpdateText');
    if (btnText) btnText.textContent = consultando ? 'Consultando...' : ROTULO_CONSULTA;
    if (btn) {
        btn.setAttribute('aria-label', consultando ? 'Consultando...' : ROTULO_CONSULTA);
        if (consultando) {
            btn.setAttribute('aria-busy', 'true');
        } else {
            btn.removeAttribute('aria-busy');
        }
    }
}

// Botão de consulta desativado por aria-disabled (e não disabled): com disabled o foco cai no body,
// e aqui o clique é bloqueado no próprio script. Serve à consulta em andamento e à espera do cooldown.
function desativarBotaoConsulta(ativo) {
    const btn = document.getElementById('btnUpdate');
    if (!btn) return;
    if (ativo) {
        btn.setAttribute('aria-disabled', 'true');
    } else {
        btn.removeAttribute('aria-disabled');
    }
}

let esperaConsultaId = null;

// Tempo curto: "2:13" abaixo de 10 minutos e "12m" a partir daí (cabe no círculo de 52px do celular)
function tempoEspera(segundos) {
    if (segundos >= 600) return `${Math.floor(segundos / 60)}m`;
    const min = Math.floor(segundos / 60);
    const sec = String(segundos % 60).padStart(2, '0');
    return `${min}:${sec}`;
}

function mostrarEsperaConsulta(segundos) {
    const btn = document.getElementById('btnUpdate');
    const btnText = document.getElementById('btnUpdateText');
    const tempo = tempoEspera(segundos);
    // O prefixo "Disponível em" some no celular (CSS); o nome acessível sempre o traz
    if (btnText) {
        const prefixo = document.createElement('span');
        prefixo.className = 'espera-prefixo';
        prefixo.textContent = 'Disponível em ';
        const valor = document.createElement('span');
        valor.className = 'espera-tempo';
        valor.textContent = tempo;
        btnText.replaceChildren(prefixo, valor);
    }
    if (btn) {
        btn.setAttribute('aria-label', `Disponível em ${tempo}`);
        btn.classList.add('is-espera');
    }
}

function pararEsperaConsulta() {
    if (esperaConsultaId !== null) {
        clearInterval(esperaConsultaId);
        esperaConsultaId = null;
    }
}

// Fim da espera: o botão volta ao rótulo normal, sem o tempo nem a classe de espera
function encerrarEsperaConsulta() {
    pararEsperaConsulta();
    const btn = document.getElementById('btnUpdate');
    if (btn) btn.classList.remove('is-espera');
    desativarBotaoConsulta(false);
    ajustarBotaoConsulta(false);
}

// Mostra o tempo que falta do cooldown (o servidor informa os segundos) e libera o botão ao zerar
function iniciarEsperaConsulta(segundos) {
    pararEsperaConsulta();
    let restante = Math.max(0, Math.ceil(Number(segundos) || 0));
    if (restante === 0) {
        encerrarEsperaConsulta();
        return;
    }
    desativarBotaoConsulta(true);
    mostrarEsperaConsulta(restante);
    esperaConsultaId = setInterval(function () {
        restante -= 1;
        if (restante <= 0) {
            encerrarEsperaConsulta();
        } else {
            mostrarEsperaConsulta(restante);
        }
    }, 1000);
}

// Ao abrir a página, o botão já nasce desativado se o cooldown ainda estiver ativo no servidor (leitura só)
async function verificarCooldownConsulta() {
    try {
        const res = await fetch(`${getBaseUrl()}/api/status`);
        if (!res.ok) return;
        const data = await res.json();
        iniciarEsperaConsulta(data.cooldown_remaining);
    } catch {
        // Servidor offline: o botão segue normal; a consulta mostra o erro ao ser tentada
    }
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
    // Clique durante a consulta ou a espera do cooldown não faz nada (o botão está com aria-disabled)
    if (btn && btn.getAttribute('aria-disabled') === 'true') return;
    const spinner = document.getElementById('spinner');
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
        desativarBotaoConsulta(true);
        if (spinner) spinner.style.display = 'block';
        ajustarBotaoConsulta(true);

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
                    showToast('Atualização concluída com sucesso!', 'var(--color-success)');
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
                showToast('❌ Conexão de logs interrompida. Tente atualizar novamente.', 'var(--color-danger)', null, 'erro');
                desativarBotaoConsulta(false);
                if (spinner) spinner.style.display = 'none';
                ajustarBotaoConsulta(false);
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
            showToast(`⏳ Cooldown ativo! Próxima atualização permitida em ${min}m ${sec}s`, 'var(--color-warning)');
            if (consoleDiv) consoleDiv.style.display = 'none';
            if (spinner) spinner.style.display = 'none';
            // O botão fica desativado com o tempo que falta, e libera sozinho ao zerar
            ajustarBotaoConsulta(false);
            iniciarEsperaConsulta(remaining);
        } else {
            showToast('❌ Erro na resposta do servidor.', 'var(--color-danger)', null, 'erro');
            desativarBotaoConsulta(false);
            if (spinner) spinner.style.display = 'none';
            ajustarBotaoConsulta(false);
        }
    } catch (err) {
        console.error('Falha ao conectar com o servidor:', err);
        showToast('❌ Servidor offline ou inacessível.', 'var(--color-danger)', null, 'erro');
        desativarBotaoConsulta(false);
        if (spinner) spinner.style.display = 'none';
        ajustarBotaoConsulta(false);
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
            showToast('Página regerada com os últimos dados consultados.', 'var(--color-success)');
            setTimeout(() => {
                window.location.href = window.location.pathname + '?updated=true';
            }, 700);
        } else {
            showToast(`❌ ${data.erro || 'Não foi possível regerar a página.'}`, 'var(--color-danger)', null, 'erro');
            restaurar();
        }
    } catch (err) {
        console.error('Falha ao regerar a página:', err);
        showToast('❌ Servidor offline ou inacessível.', 'var(--color-danger)', null, 'erro');
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
        // Duas versões do mesmo texto: o CSS mostra a curta (só minutos, sem horário) abaixo de 640px e a completa acima
        const minutes = Math.floor(remainingSeconds / 60);
        const seconds = remainingSeconds % 60;
        const curta = document.createElement('span');
        curta.className = 'contagem-curta';
        curta.textContent = minutes < 1 ? 'menos de 1 min' : `${minutes} min`;
        const completa = document.createElement('span');
        completa.className = 'contagem-completa';
        completa.textContent = `${minutes}m ${seconds.toString().padStart(2, '0')}s (às ${nextTimeStr})`;
        timerEl.replaceChildren(curta, completa);
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
        verificarCooldownConsulta();
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
