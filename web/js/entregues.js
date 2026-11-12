// Página Entregues: alterna entre a semana atual e a anterior.
// Só mostra o painel da semana escolhida; a escolha não é salva.
(function () {
    var botoes = document.querySelectorAll('.entregues-seletor [data-semana]');
    var paineis = document.querySelectorAll('.entregues-painel[data-painel-semana]');
    var anuncio = document.getElementById('entregues-anuncio');

    function mostrarSemana(indice) {
        botoes.forEach(function (botao) {
            var ativo = botao.getAttribute('data-semana') === indice;
            botao.setAttribute('aria-pressed', ativo ? 'true' : 'false');
        });
        paineis.forEach(function (painel) {
            var escolhido = painel.getAttribute('data-painel-semana') === indice;
            painel.hidden = !escolhido;
            // Anuncia a semana escolhida ("Esta semana: 3 entregas") para quem usa leitor de tela
            if (escolhido && anuncio) {
                anuncio.textContent = painel.getAttribute('data-anuncio') || '';
            }
        });
    }

    botoes.forEach(function (botao) {
        botao.addEventListener('click', function () {
            mostrarSemana(botao.getAttribute('data-semana'));
        });
    });
})();
