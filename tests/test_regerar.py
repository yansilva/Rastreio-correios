"""Testes do cache dos Correios e da regeração do relatório sem chamar as APIs."""
import io
import json
import os
import re
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

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
        # Aguardando retirada não entra nos cartões de resumo: aparece na faixa "Precisam de ação"
        retiradas = int(re.search(r"<strong>(\d+)</strong> Aguardando retirada", html).group(1))
        self.assertEqual(retiradas, 1)
        self.assertEqual(sum(numeros_resumo) + retiradas, total_cartoes)

        self.assertRegex(html, r'data-filter="atrasado"[^>]*>.*?<strong>1</strong> Atrasados')
        self.assertRegex(html, r'data-filter="aguardando_retirada"[^>]*>.*?<strong>1</strong> Aguardando retirada')

        # Uma categoria por pedido: quem aguarda retirada sai de "Em trânsito" e aparece só em "Aguardando retirada"
        categorias = {"em_transito", "aguardando_retirada", "nao_enviado", "entregue", "devolvido"}
        por_cartao = [set(valor.split()) & categorias for valor in re.findall(r'data-status="([^"]*)"', html)]
        self.assertEqual(len(por_cartao), total_cartoes)
        self.assertTrue(all(len(c) == 1 for c in por_cartao), por_cartao)
        self.assertEqual(sum(1 for c in por_cartao if "em_transito" in c), 2)  # SY2 e SY3
        self.assertEqual(sum(1 for c in por_cartao if "aguardando_retirada" in c), 1)  # SY1
        numero_em_transito = re.search(r'class="dash-number dash-number-blue">(\d+)</span>', html)
        self.assertEqual(int(numero_em_transito.group(1)), 2)
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


def _evento_iso(dias: float, descricao: str) -> dict:
    quando = (datetime.now() - timedelta(days=dias)).replace(microsecond=0).isoformat()
    return {"dtHrCriado": quando, "descricao": descricao, "unidade": {"endereco": {"cidade": "RIO DE JANEIRO", "uf": "RJ"}}}


def _raw_entregue() -> dict:
    return {"eventos": [_evento_iso(1, "Objeto entregue ao destinatário"), _evento_iso(4, "Objeto postado")]}


def _raw_em_transito() -> dict:
    return {"eventos": [_evento_iso(1, "Objeto em transferência"), _evento_iso(4, "Objeto postado")]}


class TestHistoricoEntregasEmProcessar(unittest.TestCase):
    """processar() alimenta o histórico de entregas; a última consulta só acontece em consulta real."""

    CSV = "Número do Pedido no Tiny,Situação,Código de Rastreio,Cliente\n"

    def _ambiente(self, pasta, csv_linhas, cache=None, historico=None):
        arquivos = os.path.join(pasta, "Arquivos")
        os.makedirs(arquivos)
        Path(arquivos, "rastreios_tiny.csv").write_text(self.CSV + csv_linhas, encoding="utf-8")
        if cache is not None:
            salvar_cache(os.path.join(arquivos, "rastreios_cache.json"), cache, datetime.now())
        if historico is not None:
            Path(arquivos, "entregas_historico.json").write_text(json.dumps(historico), encoding="utf-8")
        return os.path.join(arquivos, "consulta_correios.py")

    def _rodar(self, falso_modulo, usar_cache, consultar):
        with (
            patch.object(consulta_correios, "__file__", falso_modulo),
            patch.object(consulta_correios, "obter_token", return_value="tok"),
            patch.object(consulta_correios, "consultar_objeto", consultar),
            patch.object(consulta_correios.CorreiosConfig, "credenciais_preenchidas", return_value=True),
            patch.object(consulta_correios.time, "sleep"),
            patch("sys.stdout", new_callable=io.StringIO),
        ):
            return consulta_correios.processar(usar_cache=usar_cache)

    @staticmethod
    def _respostas(respostas):
        def fake(codigo, _token):
            valor = respostas.get(codigo)
            if isinstance(valor, Exception):
                raise valor
            return valor

        return fake

    @staticmethod
    def _historico(pasta):
        return json.loads(Path(pasta, "Arquivos", "entregas_historico.json").read_text(encoding="utf-8"))

    def test_processar_registra_entregue_no_historico(self):
        with tempfile.TemporaryDirectory() as pasta:
            falso = self._ambiente(
                pasta,
                "42517,Enviado,AE023423841BR,Fulano de Tal\n",
                cache={"AE023423841BR": _raw_entregue()},
            )
            consultar = MagicMock(side_effect=AssertionError("chamou a rede"))
            resultado = self._rodar(falso, usar_cache=True, consultar=consultar)

            self.assertIsNot(resultado, False)
            consultar.assert_not_called()
            item = self._historico(pasta)["entregas"]["AE023423841BR"]
            self.assertEqual(item["pedido"], "42517")
            self.assertEqual(item["cliente"], "Fulano de Tal")
            self.assertEqual(item["cidade"], "RIO DE JANEIRO/RJ")
            self.assertIsNotNone(item["postado_em"])

    def test_rastreio_que_saiu_do_tiny_recebe_uma_consulta(self):
        historico = {
            "versao": 1,
            "acompanhados": {"AE111BR": {"pedido": "42934", "cliente": "Fulano", "situacao_tiny": "Enviado", "visto_em": "2026-11-12T10:30:00"}},
            "entregas": {},
        }
        with tempfile.TemporaryDirectory() as pasta:
            falso = self._ambiente(pasta, "42935,Enviado,AE222BR,Beltrana\n", historico=historico)
            consultar = MagicMock(
                side_effect=self._respostas({"AE111BR": _raw_entregue(), "AE222BR": _raw_em_transito()})
            )
            resultado = self._rodar(falso, usar_cache=False, consultar=consultar)

            self.assertIsNot(resultado, False)
            chamadas = [c.args[0] for c in consultar.call_args_list]
            self.assertEqual(chamadas.count("AE111BR"), 1)
            dados = self._historico(pasta)
            self.assertEqual(dados["entregas"]["AE111BR"]["pedido"], "42934")
            self.assertEqual(dados["entregas"]["AE111BR"]["cliente"], "Fulano")
            self.assertEqual(set(dados["acompanhados"]), {"AE222BR"})

    def test_regerar_pelo_cache_nao_faz_ultima_consulta(self):
        historico = {
            "versao": 1,
            "acompanhados": {"AE111BR": {"pedido": "42934", "cliente": "Fulano", "situacao_tiny": "Enviado", "visto_em": "x"}},
            "entregas": {},
        }
        with tempfile.TemporaryDirectory() as pasta:
            falso = self._ambiente(
                pasta,
                "42935,Enviado,AE222BR,Beltrana\n",
                cache={"AE222BR": _raw_em_transito()},
                historico=historico,
            )
            consultar = MagicMock()
            resultado = self._rodar(falso, usar_cache=True, consultar=consultar)

            self.assertIsNot(resultado, False)
            consultar.assert_not_called()
            dados = self._historico(pasta)
            self.assertEqual(set(dados["acompanhados"]), {"AE111BR"})
            self.assertEqual(dados["entregas"], {})

    def test_entrada_sem_entregue_em_nao_derruba_o_painel(self):
        historico = {
            "versao": 1,
            "acompanhados": {},
            "entregas": {"RUIM": {"pedido": "9", "rastreio": "RUIM"}},
        }
        with tempfile.TemporaryDirectory() as pasta:
            falso = self._ambiente(
                pasta,
                "42935,Enviado,AE222BR,Beltrana\n",
                cache={"AE222BR": _raw_em_transito()},
                historico=historico,
            )
            resultado = self._rodar(falso, usar_cache=True, consultar=MagicMock())

            self.assertIsNot(resultado, False)
            self.assertTrue(Path(pasta, "relatorio_rastreio.html").exists())
            self.assertTrue(Path(pasta, "entregues_semana.html").exists())
            self.assertEqual(self._historico(pasta)["entregas"], {})

    def test_falha_ao_gerar_pagina_entregues_nao_devolve_false(self):
        with tempfile.TemporaryDirectory() as pasta:
            falso = self._ambiente(pasta, "42935,Enviado,AE222BR,Beltrana\n", cache={"AE222BR": _raw_em_transito()})
            with patch.object(consulta_correios, "gerar_pagina_entregues", side_effect=ValueError("quebrou")):
                resultado = self._rodar(falso, usar_cache=True, consultar=MagicMock())

            self.assertIsNot(resultado, False)
            self.assertTrue(Path(pasta, "relatorio_rastreio.html").exists())

    def test_falha_na_ultima_consulta_nao_derruba_relatorio(self):
        historico = {
            "versao": 1,
            "acompanhados": {"AE111BR": {"pedido": "42934", "cliente": "Fulano", "situacao_tiny": "Enviado", "visto_em": "x"}},
            "entregas": {},
        }
        with tempfile.TemporaryDirectory() as pasta:
            falso = self._ambiente(pasta, "42935,Enviado,AE222BR,Beltrana\n", historico=historico)
            consultar = MagicMock(
                side_effect=self._respostas(
                    {"AE111BR": requests.RequestException("sem rede"), "AE222BR": _raw_em_transito()}
                )
            )
            resultado = self._rodar(falso, usar_cache=False, consultar=consultar)

            self.assertIsNot(resultado, False)
            self.assertTrue(Path(pasta, "relatorio_rastreio.html").exists())
            dados = self._historico(pasta)
            self.assertEqual(dados["entregas"], {})
            self.assertEqual(set(dados["acompanhados"]), {"AE222BR"})


class TestFalhaDeUmRastreioNaConsultaReal(unittest.TestCase):
    """Uma falha da API dos Correios num rastreio não derruba a consulta inteira."""

    def test_falha_de_um_rastreio_mantem_dado_anterior_e_segue(self):
        from correios.exceptions import CorreiosTimeoutError

        agora = datetime.now()
        antigo = {"eventos": [{"dtHrCriado": (agora - timedelta(days=2)).replace(microsecond=0).isoformat(),
                               "descricao": "Objeto postado ANTIGO"}]}
        novo = {"eventos": [{"dtHrCriado": (agora - timedelta(days=1)).replace(microsecond=0).isoformat(),
                             "descricao": "Objeto postado NOVO"}]}
        with tempfile.TemporaryDirectory() as pasta:
            arquivos = os.path.join(pasta, "Arquivos")
            os.makedirs(arquivos)
            Path(arquivos, "rastreios_tiny.csv").write_text(
                "Número do Pedido no Tiny,Situação,Código de Rastreio\n"
                "5001,Enviado,AE000000001BR\n"
                "5002,Enviado,AE000000002BR\n",
                encoding="utf-8",
            )
            salvar_cache(
                os.path.join(arquivos, "rastreios_cache.json"),
                {"AE000000001BR": antigo},
                agora - timedelta(hours=1),
            )
            respostas = {"AE000000001BR": CorreiosTimeoutError("demorou"), "AE000000002BR": novo}

            def consulta(codigo, _token):
                valor = respostas[codigo]
                if isinstance(valor, Exception):
                    raise valor
                return valor

            with (
                patch.object(consulta_correios, "__file__", os.path.join(arquivos, "consulta_correios.py")),
                patch.object(consulta_correios, "obter_token", return_value="tok"),
                patch.object(consulta_correios, "consultar_objeto", side_effect=consulta),
                patch.object(consulta_correios.CorreiosConfig, "credenciais_preenchidas", return_value=True),
                patch.object(consulta_correios.time, "sleep"),
                patch("sys.stdout", new_callable=io.StringIO),
            ):
                resultado = consulta_correios.processar(usar_cache=False)

            self.assertIs(resultado, True)
            html = Path(pasta, "relatorio_rastreio.html").read_text(encoding="utf-8")
            self.assertIn('<span class="order-num">Pedido Tiny #5001</span>', html)
            self.assertIn('<span class="order-num">Pedido Tiny #5002</span>', html)
            self.assertIn("Objeto postado ANTIGO", html)
            self.assertIn("Objeto postado NOVO", html)
            cache_salvo, _ = carregar_cache(os.path.join(arquivos, "rastreios_cache.json"))
            self.assertEqual(cache_salvo["AE000000001BR"], antigo)
            self.assertEqual(cache_salvo["AE000000002BR"], novo)


class TestEscapeDeDadosExternos(unittest.TestCase):
    """Texto vindo dos Correios e do Tiny sai escapado no HTML: "<" e "&" não quebram a página."""

    def test_evento_com_html_sai_escapado_no_cartao(self):
        evento = {
            "dtHrCriado": "2026-11-12T10:00:00",
            "descricao": "Objeto <b>& teste</b>",
            "detalhe": "<script>alert(1)</script>",
            "unidade": {"endereco": {"cidade": "Rio <X>", "uf": "RJ"}},
        }
        html = consulta_correios.formatar_evento_html(evento)
        self.assertNotIn("<script>", html)
        self.assertNotIn("<b>& teste", html)
        self.assertIn("Objeto &lt;b&gt;&amp; teste&lt;/b&gt;", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertIn("Rio &lt;X&gt;/RJ", html)

    def test_data_invalida_sai_escapada(self):
        html = consulta_correios.formatar_evento_html({"dtHrCriado": "<img src=x>", "descricao": "Postado"})
        self.assertNotIn("<img", html)
        self.assertIn("&lt;img src=x&gt;", html)

    def test_atrasado_e_painel_com_texto_de_html_saem_escapados(self):
        agora = datetime.now()
        postado = (agora - timedelta(days=6)).replace(microsecond=0).isoformat()
        cache = {
            "AE000000077BR": {
                "eventos": [
                    {
                        "dtHrCriado": postado,
                        "descricao": "Objeto <i>postado</i> & cia",
                        "unidade": {"endereco": {"cidade": "Cidade <A> & Co", "uf": "SP"}},
                    }
                ]
            }
        }
        with tempfile.TemporaryDirectory() as pasta:
            arquivos = os.path.join(pasta, "Arquivos")
            os.makedirs(arquivos)
            Path(arquivos, "rastreios_tiny.csv").write_text(
                "Número do Pedido no Tiny,Situação,Código de Rastreio,Cliente\n"
                "<b>7701</b>,Enviado,AE000000077BR,Ana <i>Lima</i> & Filhos\n",
                encoding="utf-8",
            )
            salvar_cache(os.path.join(arquivos, "rastreios_cache.json"), cache, agora)
            with (
                patch.object(consulta_correios, "__file__", os.path.join(arquivos, "consulta_correios.py")),
                patch.object(consulta_correios.CorreiosConfig, "credenciais_preenchidas", return_value=True),
                patch("sys.stdout", new_callable=io.StringIO),
            ):
                self.assertIsNot(consulta_correios.processar(usar_cache=True), False)
            painel = Path(pasta, "relatorio_rastreio.html").read_text(encoding="utf-8")
            atrasados = Path(pasta, "pedidos_atrasados.html").read_text(encoding="utf-8")

        for html in (painel, atrasados):
            self.assertNotIn("<i>postado</i>", html)
            self.assertNotIn("<A>", html)
            self.assertNotIn("<b>7701</b>", html)
        self.assertIn("Objeto &lt;i&gt;postado&lt;/i&gt; &amp; cia", atrasados)
        self.assertIn("Cidade &lt;A&gt; &amp; Co/SP", atrasados)
        self.assertIn("&lt;b&gt;7701&lt;/b&gt;", atrasados)
        self.assertIn("Ana &lt;i&gt;Lima&lt;/i&gt; &amp; Filhos", atrasados)


class TestErrosNaConsultaRealDeRastreio(unittest.TestCase):
    """Só erro da API dos Correios usa o dado anterior; erro de autenticação e de programação sobem."""

    def _rodar_com(self, excecao):
        from correios.exceptions import CorreiosAuthError  # noqa: F401

        agora = datetime.now()
        with tempfile.TemporaryDirectory() as pasta:
            arquivos = os.path.join(pasta, "Arquivos")
            os.makedirs(arquivos)
            Path(arquivos, "rastreios_tiny.csv").write_text(
                "Número do Pedido no Tiny,Situação,Código de Rastreio\n5101,Enviado,AE000000011BR\n",
                encoding="utf-8",
            )
            salvar_cache(
                os.path.join(arquivos, "rastreios_cache.json"),
                {"AE000000011BR": {"eventos": [{"dtHrCriado": agora.replace(microsecond=0).isoformat(), "descricao": "Objeto postado"}]}},
                agora - timedelta(hours=1),
            )
            with (
                patch.object(consulta_correios, "__file__", os.path.join(arquivos, "consulta_correios.py")),
                patch.object(consulta_correios, "obter_token", return_value="tok"),
                patch.object(consulta_correios, "consultar_objeto", side_effect=excecao),
                patch.object(consulta_correios.CorreiosConfig, "credenciais_preenchidas", return_value=True),
                patch.object(consulta_correios.time, "sleep"),
                patch("sys.stdout", new_callable=io.StringIO),
            ):
                return consulta_correios.processar(usar_cache=False)

    def test_erro_de_autenticacao_faz_processar_falhar(self):
        from correios.exceptions import CorreiosAuthError

        self.assertIs(self._rodar_com(CorreiosAuthError("token recusado")), False)

    def test_erro_de_programacao_nao_e_engolido(self):
        self.assertIs(self._rodar_com(TypeError("bug de programação")), False)


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
