"""Testes do cache dos Correios e da regeração do relatório sem chamar as APIs."""
import io
import os
import re
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_arquivos = os.path.join(_raiz, "Arquivos")
for _caminho in (_raiz, _arquivos):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

import consulta_correios  # noqa: E402
from correios import TrackingService  # noqa: E402
from correios.cache import carregar_cache, salvar_cache  # noqa: E402
from server.config import ServerConfig  # noqa: E402
from server.handler import RastreioRequestHandler  # noqa: E402
from server.logger import ServerLogQueue  # noqa: E402
from server.service import UpdateManager  # noqa: E402


class TestCache(unittest.TestCase):
    def test_salvar_e_carregar(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "cache.json")
            momento = datetime(2026, 10, 16, 18, 30, 5)
            salvar_cache(caminho, {"AB123BR": {"eventos": [{"descricao": "Objeto postado"}]}}, momento)

            objetos, quando = carregar_cache(caminho)
            self.assertEqual(objetos["AB123BR"]["eventos"][0]["descricao"], "Objeto postado")
            self.assertEqual(quando, momento)
            self.assertFalse(os.path.exists(caminho + ".tmp"))

    def test_arquivo_inexistente_ou_invalido_devolve_none(self):
        with tempfile.TemporaryDirectory() as pasta:
            self.assertIsNone(carregar_cache(os.path.join(pasta, "nao_existe.json")))
            ruim = os.path.join(pasta, "ruim.json")
            Path(ruim).write_text("{ não é json", encoding="utf-8")
            self.assertIsNone(carregar_cache(ruim))
            sem_objetos = os.path.join(pasta, "sem_objetos.json")
            Path(sem_objetos).write_text('{"gerado_em": "2026-10-16T10:00:00"}', encoding="utf-8")
            self.assertIsNone(carregar_cache(sem_objetos))

    def test_data_invalida_usa_data_do_arquivo(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "cache.json")
            Path(caminho).write_text('{"gerado_em": "ontem", "objetos": {}}', encoding="utf-8")
            objetos, quando = carregar_cache(caminho)
            self.assertEqual(objetos, {})
            self.assertIsInstance(quando, datetime)


class TestRegerarSemRede(unittest.TestCase):
    """Executa o processar() real com cache, numa pasta temporária, sem nenhuma chamada de rede."""

    def _montar(self, pasta: str, com_cache: bool) -> str:
        arquivos = os.path.join(pasta, "Arquivos")
        os.makedirs(arquivos)
        Path(os.path.join(arquivos, "rastreios_tiny.csv")).write_text(
            "Número do Pedido no Tiny,Situação,Código de Rastreio\n42517,Enviado,AE023423841BR\n",
            encoding="utf-8",
        )
        if com_cache:
            salvar_cache(
                os.path.join(arquivos, "rastreios_cache.json"),
                {
                    "AE023423841BR": {
                        "eventos": [
                            {
                                "dtHrCriado": "2026-10-14T23:02:00",
                                "descricao": "Objeto entregue ao destinatário",
                                "unidade": {"endereco": {"cidade": "SAO PAULO", "uf": "SP"}},
                            },
                            {
                                "dtHrCriado": "2026-10-10T10:00:00",
                                "descricao": "Objeto postado",
                                "unidade": {"endereco": {"cidade": "SAO PAULO", "uf": "SP"}},
                            },
                        ]
                    }
                },
                datetime(2026, 10, 14, 23, 30, 0),
            )
        return os.path.join(arquivos, "consulta_correios.py")

    def test_regera_html_do_cache_sem_chamar_apis(self):
        with tempfile.TemporaryDirectory() as pasta:
            falso_modulo = self._montar(pasta, com_cache=True)
            with (
                patch.object(consulta_correios, "__file__", falso_modulo),
                patch.object(consulta_correios, "obter_token", side_effect=AssertionError("chamou a rede")),
                patch.object(consulta_correios, "consultar_objeto", side_effect=AssertionError("chamou a rede")),
                # O pedido do cache é uma entrega antiga: a regra de visibilidade o esconderia, e aqui o foco é o cache
                patch.object(TrackingService, "deve_ocultar_card", return_value=False),
                patch("sys.stdout", new_callable=io.StringIO),
            ):
                resultado = consulta_correios.processar(usar_cache=True)

            self.assertIsNot(resultado, False)
            html = Path(pasta, "relatorio_rastreio.html").read_text(encoding="utf-8")
            self.assertIn('<time id="dadosEm" datetime="2026-10-14T23:30:00">14/10 23:30</time>', html)
            self.assertIn('id="dadosIdade"', html)
            self.assertIn('data-status="entregue"', html)
            self.assertIn("Tiny desatualizado", html)
            self.assertTrue(Path(pasta, "pedidos_atrasados.html").exists())

            # Acessibilidade do HTML gerado: aba atual marcada e toda descrição aponta para um id que existe
            self.assertRegex(html, r'class="nav-tab active" aria-current="page"')
            ids = set(re.findall(r'\bid="([^"]+)"', html))
            referencias = set(re.findall(r'aria-describedby="([^"]+)"', html))
            self.assertTrue(referencias)
            for ref in referencias:
                for alvo in ref.split():
                    self.assertIn(alvo, ids, f"aria-describedby aponta para id inexistente: {alvo}")

    def test_resumo_soma_o_total_e_faixa_de_acao_conta_o_que_pede_acao(self):
        agora = datetime.now()

        def evento(dias, descricao):
            quando = (agora - timedelta(days=dias, hours=1)).replace(microsecond=0).isoformat()
            return {"dtHrCriado": quando, "descricao": descricao, "unidade": {"endereco": {"cidade": "SAO PAULO", "uf": "SP"}}}

        pedidos = {
            "SY1": ("Enviado", [evento(0, "Objeto aguardando retirada no endereço indicado"), evento(3, "Objeto postado")]),
            "SY2": ("Enviado", [evento(2, "Objeto em transferência"), evento(6, "Objeto postado")]),
            "SY3": ("Enviado", [evento(1, "Objeto em transferência"), evento(2, "Objeto postado")]),
            "SY4": ("Enviado", [evento(0, "Objeto entregue ao destinatário"), evento(3, "Objeto postado")]),
            "SY5": ("Não entregue", [evento(1, "Objeto devolvido ao remetente"), evento(9, "Objeto postado")]),
            "SY6": ("Pronto para envio", []),
        }
        with tempfile.TemporaryDirectory() as pasta:
            arquivos = os.path.join(pasta, "Arquivos")
            os.makedirs(arquivos)
            linhas = "".join(f"{100 + i},{situacao},{codigo}\n" for i, (codigo, (situacao, _)) in enumerate(pedidos.items()))
            Path(arquivos, "rastreios_tiny.csv").write_text(
                "Número do Pedido no Tiny,Situação,Código de Rastreio\n" + linhas, encoding="utf-8"
            )
            salvar_cache(
                os.path.join(arquivos, "rastreios_cache.json"),
                {codigo: ({"eventos": eventos} if eventos else None) for codigo, (_, eventos) in pedidos.items()},
                agora - timedelta(minutes=12),
            )
            with patch.object(consulta_correios, "__file__", os.path.join(arquivos, "consulta_correios.py")), patch(
                "sys.stdout", new_callable=io.StringIO
            ):
                resultado = consulta_correios.processar(usar_cache=True)

            self.assertIsNot(resultado, False)
            html = Path(pasta, "relatorio_rastreio.html").read_text(encoding="utf-8")

        total_cartoes = html.count('class="order-card')
        numeros_resumo = [int(n) for n in re.findall(r'class="dash-number[^"]*">(\d+)</span>', html)]
        # Pedidos que a regra de visibilidade esconde (devolvido há mais de 24h, entregue em semana passada)
        # não são desenhados nem contados; o resto aparece e soma o resumo
        ocultos = sum(
            1
            for _, eventos in pedidos.values()
            if TrackingService.deve_ocultar_card(TrackingService.processar_objeto("X", {"eventos": eventos}))
        )
        self.assertGreaterEqual(ocultos, 1)
        self.assertEqual(total_cartoes, len(pedidos) - ocultos)
        self.assertEqual(sum(numeros_resumo), total_cartoes)

        self.assertRegex(html, r'data-filter="atrasado"[^>]*>.*?<strong>1</strong> Atrasados')
        self.assertRegex(html, r'data-filter="aguardando_retirada"[^>]*>.*?<strong>1</strong> Aguardando retirada')
        # Pílulas com explicação (title + aria-describedby apontando para o bloco escondido) e a legenda de Opções
        self.assertRegex(html, r'data-filter="atrasado"[^>]*aria-describedby="desc-status-atrasado"')
        self.assertIn('<span id="desc-status-aguardando_retirada">Objeto na agência', html)
        self.assertIn("<strong>Atrasado:</strong> Mais de 3 dias em trânsito", html)
        self.assertNotIn("{texto_", html)
        self.assertNotIn("{descricoes_status}", html)
        self.assertNotIn("dash-card-urgent", html)
        self.assertIn("Recarregar dados salvos de", html)
        self.assertIn("Consultar Tiny e Correios", html)

    def test_nome_do_cliente_do_csv_aparece_no_titulo_e_na_busca(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivos = os.path.join(pasta, "Arquivos")
            os.makedirs(arquivos)
            Path(arquivos, "rastreios_tiny.csv").write_text(
                "Número do Pedido no Tiny,Situação,Código de Rastreio,Cliente\n"
                "7001,Enviado,AE000000001BR,Maria <b>Souza</b>\n"
                "7002,Enviado,AE000000002BR,\n",
                encoding="utf-8",
            )
            salvar_cache(
                os.path.join(arquivos, "rastreios_cache.json"),
                {
                    "AE000000001BR": {"eventos": [{"dtHrCriado": "2026-10-14T10:00:00", "descricao": "Objeto postado"}]},
                    "AE000000002BR": {"eventos": [{"dtHrCriado": "2026-10-14T10:00:00", "descricao": "Objeto postado"}]},
                },
                datetime(2026, 10, 14, 11, 0, 0),
            )
            with patch.object(consulta_correios, "__file__", os.path.join(arquivos, "consulta_correios.py")), patch(
                "sys.stdout", new_callable=io.StringIO
            ):
                resultado = consulta_correios.processar(usar_cache=True)

            self.assertIsNot(resultado, False)
            html = Path(pasta, "relatorio_rastreio.html").read_text(encoding="utf-8")

        # Sem pedido atrasado neste cenário, a tabela de atrasados não tem a coluna Cliente
        # Título em partes: número, cliente (com o HTML escapado) e código; sem cliente, só número e código
        self.assertIn('<span class="order-num">Pedido Tiny #7001</span>', html)
        self.assertIn('<span class="order-client">Maria &lt;b&gt;Souza&lt;/b&gt;</span>', html)
        self.assertIn('<span class="order-code">AE000000001BR</span>', html)
        self.assertIn('<span class="order-num">Pedido Tiny #7002</span>', html)
        self.assertIn('<span class="order-code">AE000000002BR</span>', html)
        self.assertEqual(html.count('<span class="order-client">'), 1)  # só o pedido 7001 tem cliente

    def test_tabela_de_atrasados_mostra_cliente_so_quando_o_csv_traz(self):
        agora = datetime.now()
        postado = (agora - timedelta(days=6)).replace(microsecond=0).isoformat()
        eventos = {"AE000000009BR": {"eventos": [{"dtHrCriado": postado, "descricao": "Objeto postado"}]}}

        def gerar(csv_texto):
            with tempfile.TemporaryDirectory() as pasta:
                arquivos = os.path.join(pasta, "Arquivos")
                os.makedirs(arquivos)
                Path(arquivos, "rastreios_tiny.csv").write_text(csv_texto, encoding="utf-8")
                salvar_cache(os.path.join(arquivos, "rastreios_cache.json"), eventos, agora)
                with patch.object(consulta_correios, "__file__", os.path.join(arquivos, "consulta_correios.py")), patch(
                    "sys.stdout", new_callable=io.StringIO
                ):
                    consulta_correios.processar(usar_cache=True)
                return Path(pasta, "pedidos_atrasados.html").read_text(encoding="utf-8")

        com = gerar("Número do Pedido no Tiny,Situação,Código de Rastreio,Cliente\n9001,Enviado,AE000000009BR,Ana <i>Lima</i>\n")
        self.assertIn('<th scope="col">Cliente</th>', com)
        self.assertIn('data-label="Cliente">Ana &lt;i&gt;Lima&lt;/i&gt;</td>', com)

        sem = gerar("Número do Pedido no Tiny,Situação,Código de Rastreio\n9001,Enviado,AE000000009BR\n")
        self.assertNotIn('<th scope="col">Cliente</th>', sem)
        self.assertIn('data-label="Pedido"', sem)

        # Cada linha tem "Copiar rastreio"; a navegação é a mesma do painel e há skip link e main
        self.assertIn('data-copy="AE000000009BR"', sem)
        self.assertIn('<th scope="col">Ações</th>', sem)
        self.assertIn('class="skip-link"', sem)
        self.assertIn('<main id="conteudo"', sem)
        self.assertIn('aria-current="page"', sem)
        self.assertNotIn("Voltar ao Painel", sem)

        # Sem a coluna Urgência (o selo de dias já traz o rótulo), legenda da tabela e status único escondido
        self.assertNotIn("Urgência</th>", sem)
        self.assertIn("6 dias · Alto", sem)
        self.assertIn("<caption class=\"sr-only\">Pedidos com mais de 3 dias em trânsito</caption>", sem)
        self.assertNotIn('data-label="Status"', sem)

    def test_atrasados_vazio_e_calmo_sem_quatro_zeros(self):
        with tempfile.TemporaryDirectory() as pasta:
            falso_modulo = self._montar(pasta, com_cache=True)
            with (
                patch.object(consulta_correios, "__file__", falso_modulo),
                patch.object(TrackingService, "deve_ocultar_card", return_value=False),
                patch("sys.stdout", new_callable=io.StringIO),
            ):
                consulta_correios.processar(usar_cache=True)
            vazio = Path(pasta, "pedidos_atrasados.html").read_text(encoding="utf-8")
            painel = Path(pasta, "relatorio_rastreio.html").read_text(encoding="utf-8")

        self.assertIn("Nada atrasado", vazio)
        self.assertNotIn("Nenhum pedido atrasado!", vazio)
        self.assertNotIn("summary-card", vazio)
        # Cartões de resumo do painel só informam: não são botões nem filtros
        self.assertNotIn('class="dash-card dash-clickable', painel)
        self.assertNotRegex(painel, r'class="dash-card[^"]*"[^>]*role="button"')
        self.assertEqual(painel.count('id="filterCount"'), 1)
        # Visão é um controle segmentado na linha da lista, fora do popover Opções
        self.assertIn('class="view-switch"', painel)
        self.assertNotIn('id="viewSelect"', painel)
        self.assertIn('data-view="tabela" aria-pressed="false"', painel)
        self.assertLess(painel.index('class="view-switch"'), painel.index('class="options-menu"'))

    def test_sem_cache_devolve_false(self):
        with tempfile.TemporaryDirectory() as pasta:
            falso_modulo = self._montar(pasta, com_cache=False)
            with (
                patch.object(consulta_correios, "__file__", falso_modulo),
                patch("sys.stdout", new_callable=io.StringIO) as saida,
            ):
                resultado = consulta_correios.processar(usar_cache=True)

            self.assertIs(resultado, False)
            self.assertIn("não há dados em cache", saida.getvalue())
            self.assertFalse(Path(pasta, "relatorio_rastreio.html").exists())


class TestUpdateManagerRegenerate(unittest.TestCase):
    def setUp(self):
        self.config = ServerConfig(cooldown_seconds=10, auto_update_interval=100)
        self.log_queue = ServerLogQueue()

    def test_sucesso_nao_inicia_cooldown(self):
        chamadas = []
        manager = UpdateManager(
            self.config, self.log_queue, runner_fn=lambda: None, regenerator_fn=lambda: chamadas.append(1)
        )
        sucesso, mensagem = manager.regenerate()
        self.assertTrue(sucesso)
        self.assertIn("regerado", mensagem)
        self.assertEqual(chamadas, [1])
        self.assertEqual(manager.remaining_cooldown(), 0)
        self.assertFalse(manager._is_updating)

    def test_falha_devolve_mensagem_e_libera_trava(self):
        def falha():
            raise RuntimeError("sem cache")

        manager = UpdateManager(self.config, self.log_queue, runner_fn=lambda: None, regenerator_fn=falha)
        sucesso, mensagem = manager.regenerate()
        self.assertFalse(sucesso)
        self.assertEqual(mensagem, "sem cache")
        self.assertFalse(manager._is_updating)

    def test_nao_roda_durante_atualizacao(self):
        manager = UpdateManager(
            self.config, self.log_queue, runner_fn=lambda: None, regenerator_fn=lambda: self.fail("não deveria rodar")
        )
        manager._is_updating = True
        sucesso, mensagem = manager.regenerate()
        self.assertFalse(sucesso)
        self.assertIn("atualização em andamento", mensagem)


class DummyHandler(RastreioRequestHandler):
    """Handler com I/O em memória, como nos testes do servidor."""

    def __init__(self, command: str, path: str, headers: dict | None = None):
        self.rfile = io.BytesIO(b"")
        self.wfile = io.BytesIO()
        self.client_address = ("127.0.0.1", 12345)
        self.command = command
        self.path = path
        self.requestline = f"{command} {path} HTTP/1.1"
        self.request_version = "HTTP/1.1"
        # Host do próprio servidor, como um navegador enviaria; None = sem cabeçalho Host
        self.headers = {"Host": "127.0.0.1:8000"} if headers is None else headers
        self.server_version = "TestServer/1.0"
        self.sys_version = "Python/3.12"
        self.close_connection = True

    def setup(self):
        pass

    def finish(self):
        pass


class TestRotaRegerar(unittest.TestCase):
    def setUp(self):
        self.config = ServerConfig(base_dir=Path(_raiz), cooldown_seconds=10)
        self.log_queue = ServerLogQueue()
        self._anteriores = (
            RastreioRequestHandler.server_config,
            RastreioRequestHandler.log_queue,
            RastreioRequestHandler.update_manager,
        )
        RastreioRequestHandler.server_config = self.config
        RastreioRequestHandler.log_queue = self.log_queue

    def tearDown(self):
        (
            RastreioRequestHandler.server_config,
            RastreioRequestHandler.log_queue,
            RastreioRequestHandler.update_manager,
        ) = self._anteriores

    def test_post_regerar_sucesso(self):
        RastreioRequestHandler.update_manager = UpdateManager(
            self.config, self.log_queue, runner_fn=lambda: None, regenerator_fn=lambda: None
        )
        handler = DummyHandler("POST", "/regerar")
        handler.do_POST()
        saida = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("HTTP/1.0 200", saida)
        self.assertIn('"sucesso": true', saida)

    def test_post_regerar_falha_devolve_409_com_erro(self):
        def falha():
            raise RuntimeError("não há dados em cache")

        RastreioRequestHandler.update_manager = UpdateManager(
            self.config, self.log_queue, runner_fn=lambda: None, regenerator_fn=falha
        )
        handler = DummyHandler("POST", "/regerar")
        handler.do_POST()
        saida = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("HTTP/1.0 409", saida)
        self.assertIn("não há dados em cache", saida)

    def test_post_regerar_sem_host_recusado_com_403(self):
        chamou = []

        def regenera():
            chamou.append(True)

        RastreioRequestHandler.update_manager = UpdateManager(
            self.config, self.log_queue, runner_fn=lambda: None, regenerator_fn=regenera
        )
        handler = DummyHandler("POST", "/regerar", headers={})
        handler.do_POST()
        saida = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("HTTP/1.0 403", saida)
        self.assertIn("Host não permitido", saida)
        self.assertEqual(chamou, [])


if __name__ == "__main__":
    unittest.main()
