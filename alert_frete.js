(function() {
    const pedidosComPrazo = [];
    if (pedidosComPrazo.length > 0) {
        const cacheKey = "alerta_prazo_v2_" + pedidosComPrazo.join("_");
        if (!localStorage.getItem(cacheKey)) {
            
            // 1. Mostrar o Modal Visual no Centro da Tela
            const overlay = document.createElement('div');
            overlay.style.position = 'fixed';
            overlay.style.top = '0';
            overlay.style.left = '0';
            overlay.style.width = '100vw';
            overlay.style.height = '100vh';
            overlay.style.backgroundColor = 'rgba(0,0,0,0.5)';
            overlay.style.display = 'flex';
            overlay.style.alignItems = 'center';
            overlay.style.justifyContent = 'center';
            overlay.style.zIndex = '99999';
            overlay.style.backdropFilter = 'blur(4px)';

            const modal = document.createElement('div');
            modal.style.backgroundColor = 'var(--card-bg, #ffffff)';
            modal.style.padding = '30px';
            modal.style.borderRadius = '16px';
            modal.style.boxShadow = '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)';
            modal.style.maxWidth = '400px';
            modal.style.textAlign = 'center';
            modal.style.color = 'var(--text-main, #1e293b)';
            modal.style.fontFamily = 'system-ui, -apple-system, sans-serif';

            const icon = document.createElement('div');
            icon.innerHTML = '&#9888;&#65039;'; // Unicode HTML Entity for Warning sign to avoid encoding bugs
            icon.style.fontSize = '3rem';
            icon.style.marginBottom = '15px';

            const title = document.createElement('h2');
            title.innerText = 'Atencao aos Prazos';
            title.style.margin = '0 0 10px 0';
            title.style.fontSize = '1.4rem';

            const text = document.createElement('p');
            text.innerText = "Os pedidos " + pedidosComPrazo.join(", ") + " possuem prazos de entrega superiores a 3 dias uteis.";
            text.style.margin = '0 0 20px 0';
            text.style.lineHeight = '1.5';
            text.style.color = 'var(--text-sub, #64748b)';

            const btnWrap = document.createElement('div');
            btnWrap.style.display = 'flex';
            btnWrap.style.gap = '10px';
            btnWrap.style.justifyContent = 'center';

            const btnFechar = document.createElement('button');
            btnFechar.innerText = 'Fechar';
            btnFechar.style.padding = '10px 20px';
            btnFechar.style.border = '1px solid var(--border, #e2e8f0)';
            btnFechar.style.borderRadius = '8px';
            btnFechar.style.backgroundColor = 'transparent';
            btnFechar.style.color = 'var(--text-main, #1e293b)';
            btnFechar.style.cursor = 'pointer';
            btnFechar.onclick = function() {
                document.body.removeChild(overlay);
            };

            const btnIr = document.createElement('button');
            btnIr.innerText = 'Ver Opcoes de Frete';
            btnIr.style.padding = '10px 20px';
            btnIr.style.border = 'none';
            btnIr.style.borderRadius = '8px';
            btnIr.style.backgroundColor = '#ea580c';
            btnIr.style.color = 'white';
            btnIr.style.fontWeight = 'bold';
            btnIr.style.cursor = 'pointer';
            btnIr.onclick = function() {
                window.location.href = 'opcoes_frete.html';
            };

            btnWrap.appendChild(btnFechar);
            btnWrap.appendChild(btnIr);

            modal.appendChild(icon);
            modal.appendChild(title);
            modal.appendChild(text);
            modal.appendChild(btnWrap);
            overlay.appendChild(modal);

            document.body.appendChild(overlay);

            // 2. Mostrar a Notificacao do Windows / Navegador
            if ("Notification" in window) {
                function showNotif() {
                    let n = new Notification("Alerta de Frete: Prazo Longo (>3 dias)", {
                        body: "Os pedidos " + pedidosComPrazo.join(", ") + " possuem prazos superiores a 3 dias uteis.",
                        icon: "https://cdn-icons-png.flaticon.com/512/1055/1055065.png"
                    });
                    n.onclick = function() {
                        window.location.href = "opcoes_frete.html";
                    };
                }
                
                if (Notification.permission === "granted") {
                    showNotif();
                } else if (Notification.permission !== "denied") {
                    Notification.requestPermission().then(function(p) {
                        if (p === "granted") showNotif();
                    });
                }
            }

            // Registrar que ja avisamos sobre esse grupo de pedidos
            localStorage.setItem(cacheKey, "true");
        }
    }
})();