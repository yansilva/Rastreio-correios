"""
Suíte de testes automatizados para a camada de frete.

Todos os testes utilizam mocks (unittest.mock) sem chamadas de rede ou credenciais reais.
Compatível tanto com `pytest` quanto com `python -m unittest`.
"""
import os
import sys
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

import requests

# Garante que a raiz do projeto e o diretório Arquivos estejam no sys.path
_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_arquivos = os.path.join(_raiz, "Arquivos")
if _raiz not in sys.path:
    sys.path.insert(0, _raiz)
if _arquivos not in sys.path:
    sys.path.insert(0, _arquivos)

from frete import (
    FreteConfig,
    FreteClient,
    FreteService,
    FreteReportGenerator,
    FreteError,
    FreteAPIError,
    FreteConnectionError,
    FreteTimeoutError,
    FreteServicoIndisponivelError,
    OpcaoFrete,
    validar_cep,
    normalizar_cep,
    validar_dimensoes,
)
from correios import CorreiosClient, CorreiosConfig


# ============== TESTES DE CEP ==============


class TestValidarCep(unittest.TestCase):
    """Testes da validação e normalização de CEP."""

    def test_cep_valido_sem_hifen(self):
        self.assertTrue(validar_cep("05617010"))

    def test_cep_valido_com_hifen(self):
        self.assertTrue(validar_cep("05617-010"))

    def test_cep_invalido_curto(self):
        self.assertFalse(validar_cep("0561"))

    def test_cep_invalido_letras(self):
        self.assertFalse(validar_cep("abcdefgh"))

    def test_cep_vazio(self):
        self.assertFalse(validar_cep(""))

    def test_cep_none(self):
        self.assertFalse(validar_cep(None))

    def test_cep_todos_zeros(self):
        self.assertFalse(validar_cep("00000000"))

    def test_cep_com_espacos(self):
        self.assertTrue(validar_cep(" 05617010 "))

    def test_normalizar_cep_com_hifen(self):
        self.assertEqual(normalizar_cep("05617-010"), "05617010")

    def test_normalizar_cep_sem_hifen(self):
        self.assertEqual(normalizar_cep("05617010"), "05617010")

    def test_normalizar_cep_invalido_levanta_erro(self):
        with self.assertRaises(ValueError):
            normalizar_cep("abc")

    def test_normalizar_cep_vazio_levanta_erro(self):
        with self.assertRaises(ValueError):
            normalizar_cep("")


# ============== TESTES DE PARÂMETROS ==============


class TestValidarDimensoes(unittest.TestCase):
    """Testes da validação de peso e dimensões."""

    def test_dimensoes_validas(self):
        self.assertTrue(validar_dimensoes(1000, 30, 20, 10))

    def test_peso_zero(self):
        self.assertFalse(validar_dimensoes(0, 30, 20, 10))

    def test_dimensao_negativa(self):
        self.assertFalse(validar_dimensoes(1000, -1, 20, 10))

    def test_largura_zero(self):
        self.assertFalse(validar_dimensoes(1000, 30, 0, 10))

    def test_altura_zero(self):
        self.assertFalse(validar_dimensoes(1000, 30, 20, 0))

    def test_todos_positivos_minimos(self):
        self.assertTrue(validar_dimensoes(1, 1, 1, 1))


# ============== TESTES DE OPCAOFRETE ==============


class TestOpcaoFrete(unittest.TestCase):
    """Testes do modelo OpcaoFrete."""

    def test_preco_formatado(self):
        opcao = OpcaoFrete(codigo="03220", nome="SEDEX", disponivel=True, preco=Decimal("29.90"))
        self.assertEqual(opcao.preco_formatado, "R$ 29,90")

    def test_preco_formatado_milhar(self):
        opcao = OpcaoFrete(codigo="03220", nome="SEDEX", disponivel=True, preco=Decimal("1234.56"))
        self.assertEqual(opcao.preco_formatado, "R$ 1.234,56")

    def test_preco_formatado_none(self):
        opcao = OpcaoFrete(codigo="03220", nome="SEDEX", disponivel=True, preco=None)
        self.assertIsNone(opcao.preco_formatado)

    def test_to_dict_disponivel(self):
        opcao = OpcaoFrete(
            codigo="03220", nome="SEDEX", disponivel=True,
            preco=Decimal("29.90"), prazo_dias=3, msg_prazo="Entrega normal"
        )
        d = opcao.to_dict()
        self.assertTrue(d["disponivel"])
        self.assertAlmostEqual(d["preco"], 29.90)
        self.assertEqual(d["prazo"], 3)
        self.assertEqual(d["preco_fmt"], "R$ 29,90")
        self.assertIsNone(d["erro"])

    def test_to_dict_indisponivel(self):
        opcao = OpcaoFrete(codigo="03220", nome="SEDEX", disponivel=False, erro="Indisponível")
        d = opcao.to_dict()
        self.assertFalse(d["disponivel"])
        self.assertIsNone(d["preco"])
        self.assertIsNone(d["prazo"])
        self.assertEqual(d["erro"], "Indisponível")

    def test_parse_preco_valido(self):
        self.assertEqual(OpcaoFrete.parse_preco("29,90"), Decimal("29.90"))

    def test_parse_preco_com_milhar(self):
        self.assertEqual(OpcaoFrete.parse_preco("1.234,56"), Decimal("1234.56"))

    def test_parse_preco_zero(self):
        self.assertIsNone(OpcaoFrete.parse_preco("0"))

    def test_parse_preco_vazio(self):
        self.assertIsNone(OpcaoFrete.parse_preco(""))

    def test_parse_preco_invalido(self):
        self.assertIsNone(OpcaoFrete.parse_preco("abc"))

    def test_parse_prazo_inteiro(self):
        self.assertEqual(OpcaoFrete.parse_prazo(3), 3)

    def test_parse_prazo_float(self):
        self.assertEqual(OpcaoFrete.parse_prazo(3.0), 3)

    def test_parse_prazo_string(self):
        self.assertEqual(OpcaoFrete.parse_prazo("5"), 5)

    def test_parse_prazo_none(self):
        self.assertIsNone(OpcaoFrete.parse_prazo(None))

    def test_parse_prazo_invalido(self):
        self.assertIsNone(OpcaoFrete.parse_prazo("abc"))

    def test_parse_prazo_zero(self):
        self.assertIsNone(OpcaoFrete.parse_prazo(0))

    def test_parse_prazo_negativo(self):
        self.assertIsNone(OpcaoFrete.parse_prazo(-1))


# ============== TESTES DE CONFIG ==============


class TestFreteConfig(unittest.TestCase):
    """Testes da configuração de frete."""

    def test_valores_padrao(self):
        config = FreteConfig()
        self.assertEqual(config.peso_gramas, 1000)
        self.assertEqual(config.comprimento, 30)
        self.assertEqual(config.largura, 20)
        self.assertEqual(config.altura, 10)
        self.assertEqual(config.tipo_objeto, 2)
        self.assertEqual(config.timeout_segundos, 15.0)
        self.assertIn("03220", config.servicos)

    def test_cep_origem_do_env(self):
        with patch.dict(os.environ, {"CEP_ORIGEM": "01001000"}):
            config = FreteConfig(cep_origem="")
            self.assertEqual(config.cep_origem, "01001000")

    def test_cep_origem_fallback(self):
        with patch.dict(os.environ, {}, clear=True):
            config = FreteConfig(cep_origem="")
            self.assertEqual(config.cep_origem, "05617010")

    def test_repr_nao_expoe_dados_sensiveis(self):
        config = FreteConfig()
        representacao = repr(config)
        self.assertIn("FreteConfig", representacao)
        self.assertIn("peso=1000g", representacao)


# ============== TESTES DO CLIENTE HTTP ==============


class TestFreteClient(unittest.TestCase):
    """Testes da camada de comunicação HTTP (FreteClient)."""

    def _criar_client(self):
        """Helper para criar FreteClient com mocks."""
        correios_config = CorreiosConfig(id_correios="123", contrato="456", codigo_acesso="xyz")
        correios_client = CorreiosClient(config=correios_config)
        correios_client._token = "fake_token_frete"
        frete_config = FreteConfig(cep_origem="05617010")
        return FreteClient(correios_client=correios_client, config=frete_config)

    @patch("requests.get")
    def test_obter_preco_sucesso(self, mock_get):
        """Valida consulta de preço com resposta válida."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"pcFinal": "29,90", "coProduto": "03220"}
        mock_get.return_value = mock_response

        client = self._criar_client()
        resultado = client.obter_preco("01001000", "03220")

        self.assertEqual(resultado["pcFinal"], "29,90")
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["cepOrigem"], "05617010")
        self.assertEqual(kwargs["params"]["cepDestino"], "01001000")
        self.assertEqual(kwargs["timeout"], 15.0)

    @patch("requests.get")
    def test_obter_prazo_sucesso(self, mock_get):
        """Valida consulta de prazo com resposta válida."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"prazoEntrega": 3, "msgPrazo": "Entrega normal"}
        mock_get.return_value = mock_response

        client = self._criar_client()
        resultado = client.obter_prazo("01001000", "03220")

        self.assertEqual(resultado["prazoEntrega"], 3)
        self.assertEqual(resultado["msgPrazo"], "Entrega normal")

    @patch("requests.get")
    def test_servico_indisponivel_422(self, mock_get):
        """Valida que HTTP 422 levanta FreteServicoIndisponivelError."""
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_get.return_value = mock_response

        client = self._criar_client()
        with self.assertRaises(FreteServicoIndisponivelError):
            client.obter_preco("01001000", "03220")

    @patch("requests.get")
    def test_servico_indisponivel_400(self, mock_get):
        """Valida que HTTP 400 levanta FreteServicoIndisponivelError."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_get.return_value = mock_response

        client = self._criar_client()
        with self.assertRaises(FreteServicoIndisponivelError):
            client.obter_preco("01001000", "03158")

    @patch("requests.get")
    def test_timeout(self, mock_get):
        """Valida que timeout levanta FreteTimeoutError."""
        mock_get.side_effect = requests.exceptions.Timeout("Read timed out")

        client = self._criar_client()
        with self.assertRaises(FreteTimeoutError):
            client.obter_preco("01001000", "03220")

    @patch("requests.get")
    def test_connection_error(self, mock_get):
        """Valida que erro de conexão levanta FreteConnectionError."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Network unreachable")

        client = self._criar_client()
        with self.assertRaises(FreteConnectionError):
            client.obter_preco("01001000", "03220")

    @patch("requests.get")
    def test_http_401_renova_token(self, mock_get):
        """Valida renovação de token após 401."""
        mock_401 = MagicMock()
        mock_401.status_code = 401

        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.json.return_value = {"pcFinal": "15,00"}

        mock_get.side_effect = [mock_401, mock_200]

        client = self._criar_client()
        with patch.object(client.correios_client, "gerar_token", return_value="novo_token"):
            resultado = client.obter_preco("01001000", "03220")
            self.assertEqual(resultado["pcFinal"], "15,00")

    @patch("requests.get")
    def test_http_403(self, mock_get):
        """Valida que HTTP 403 levanta FreteAPIError."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        client = self._criar_client()
        with self.assertRaises(FreteAPIError):
            client.obter_preco("01001000", "03220")

    @patch("requests.get")
    def test_http_429(self, mock_get):
        """Valida que HTTP 429 levanta FreteAPIError."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        client = self._criar_client()
        with self.assertRaises(FreteAPIError):
            client.obter_preco("01001000", "03220")

    @patch("requests.get")
    def test_http_500(self, mock_get):
        """Valida que HTTP 500 levanta FreteAPIError com detalhes."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        client = self._criar_client()
        with self.assertRaises(FreteAPIError) as ctx:
            client.obter_preco("01001000", "03220")
        self.assertEqual(ctx.exception.status_code, 500)

    @patch("requests.get")
    def test_json_invalido(self, mock_get):
        """Valida que JSON inválido levanta FreteAPIError."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        client = self._criar_client()
        with self.assertRaises(FreteAPIError):
            client.obter_preco("01001000", "03220")


# ============== TESTES DO SERVIÇO ==============


class TestFreteService(unittest.TestCase):
    """Testes das regras de negócio de frete (FreteService)."""

    def _criar_service_com_mock(self):
        """Helper que cria FreteService com FreteClient mockado."""
        mock_client = MagicMock(spec=FreteClient)
        config = FreteConfig(cep_origem="05617010")
        service = FreteService(client=mock_client, config=config)
        return service, mock_client

    def test_consultar_opcoes_todas_disponiveis(self):
        """Valida consulta com todos os serviços disponíveis."""
        service, mock_client = self._criar_service_com_mock()

        mock_client.obter_preco.return_value = {"pcFinal": "29,90"}
        mock_client.obter_prazo.return_value = {"prazoEntrega": 3, "msgPrazo": None}

        opcoes = service.consultar_opcoes("01001000", intervalo_segundos=0)

        self.assertEqual(len(opcoes), 3)  # SEDEX, SEDEX 10, SEDEX 12
        for opcao in opcoes:
            self.assertTrue(opcao.disponivel)
            self.assertEqual(opcao.preco, Decimal("29.90"))
            self.assertEqual(opcao.prazo_dias, 3)

    def test_consultar_opcoes_servico_indisponivel(self):
        """Valida que serviço indisponível é retornado como não disponível."""
        service, mock_client = self._criar_service_com_mock()

        mock_client.obter_preco.side_effect = FreteServicoIndisponivelError("Indisponível")

        opcoes = service.consultar_opcoes("01001000", intervalo_segundos=0)

        self.assertEqual(len(opcoes), 3)
        for opcao in opcoes:
            self.assertFalse(opcao.disponivel)
            self.assertIsNotNone(opcao.erro)

    def test_consultar_opcoes_prazo_indisponivel(self):
        """Valida que preço disponível mas prazo indisponível ainda retorna opção."""
        service, mock_client = self._criar_service_com_mock()

        mock_client.obter_preco.return_value = {"pcFinal": "50,00"}
        mock_client.obter_prazo.side_effect = FreteServicoIndisponivelError("Prazo indisponível")

        opcoes = service.consultar_opcoes("01001000", intervalo_segundos=0)

        for opcao in opcoes:
            self.assertTrue(opcao.disponivel)
            self.assertEqual(opcao.preco, Decimal("50.00"))
            self.assertIsNone(opcao.prazo_dias)

    def test_consultar_opcoes_resposta_vazia(self):
        """Valida que resposta vazia de preço retorna preço None mas disponível."""
        service, mock_client = self._criar_service_com_mock()

        mock_client.obter_preco.return_value = {"pcFinal": "0"}
        mock_client.obter_prazo.return_value = {"prazoEntrega": 2}

        opcoes = service.consultar_opcoes("01001000", intervalo_segundos=0)

        for opcao in opcoes:
            self.assertTrue(opcao.disponivel)
            self.assertIsNone(opcao.preco)

    def test_filtrar_disponiveis(self):
        """Valida filtro de opções disponíveis."""
        opcoes = [
            OpcaoFrete(codigo="03220", nome="SEDEX", disponivel=True, preco=Decimal("29.90")),
            OpcaoFrete(codigo="03158", nome="SEDEX 10", disponivel=False, erro="Indisponível"),
            OpcaoFrete(codigo="03140", nome="SEDEX 12", disponivel=True, preco=Decimal("45.00")),
        ]
        resultado = FreteService.filtrar_disponiveis(opcoes)
        self.assertEqual(len(resultado), 2)

    def test_mais_barato(self):
        """Valida seleção da opção mais barata."""
        opcoes = [
            OpcaoFrete(codigo="03220", nome="SEDEX", disponivel=True, preco=Decimal("29.90")),
            OpcaoFrete(codigo="03158", nome="SEDEX 10", disponivel=True, preco=Decimal("45.00")),
            OpcaoFrete(codigo="03140", nome="SEDEX 12", disponivel=True, preco=Decimal("39.00")),
        ]
        resultado = FreteService.mais_barato(opcoes)
        self.assertEqual(resultado.codigo, "03220")
        self.assertEqual(resultado.preco, Decimal("29.90"))

    def test_mais_rapido(self):
        """Valida seleção da opção mais rápida."""
        opcoes = [
            OpcaoFrete(codigo="03220", nome="SEDEX", disponivel=True, prazo_dias=5),
            OpcaoFrete(codigo="03158", nome="SEDEX 10", disponivel=True, prazo_dias=2),
            OpcaoFrete(codigo="03140", nome="SEDEX 12", disponivel=True, prazo_dias=3),
        ]
        resultado = FreteService.mais_rapido(opcoes)
        self.assertEqual(resultado.codigo, "03158")
        self.assertEqual(resultado.prazo_dias, 2)

    def test_mais_barato_lista_vazia(self):
        """Valida que lista vazia retorna None."""
        self.assertIsNone(FreteService.mais_barato([]))

    def test_mais_rapido_lista_vazia(self):
        """Valida que lista vazia retorna None."""
        self.assertIsNone(FreteService.mais_rapido([]))

    def test_mais_barato_sem_disponiveis(self):
        """Valida que lista sem opções disponíveis retorna None."""
        opcoes = [
            OpcaoFrete(codigo="03220", nome="SEDEX", disponivel=False),
        ]
        self.assertIsNone(FreteService.mais_barato(opcoes))

    def test_mais_rapido_sem_prazo(self):
        """Valida que opções sem prazo definido não são consideradas."""
        opcoes = [
            OpcaoFrete(codigo="03220", nome="SEDEX", disponivel=True, prazo_dias=None),
        ]
        self.assertIsNone(FreteService.mais_rapido(opcoes))


# ============== TESTES DO REPORT ==============


class TestFreteReportGenerator(unittest.TestCase):
    """Testes da geração de relatório HTML."""

    def test_gerar_html_sem_pedidos(self):
        """Valida geração de HTML com lista vazia (estado vazio)."""
        config = FreteConfig(cep_origem="05617010")
        generator = FreteReportGenerator(config=config)

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            caminho = generator.gerar_html([])
            self.assertIn("opcoes_frete.html", caminho)
            # Verifica que o arquivo foi escrito
            mock_file.assert_called()

    def test_gerar_html_com_pedidos(self):
        """Valida geração de HTML com pedidos e serviços."""
        config = FreteConfig(cep_origem="05617010")
        generator = FreteReportGenerator(config=config)

        pedidos = [{
            "numero": "1001",
            "situacao": "Aberto",
            "nome_cliente": "Teste",
            "valor": 150.0,
            "cep_destino": "01001000",
            "destino_label": "São Paulo/SP",
            "servicos": {
                "03220": {"disponivel": True, "preco": 29.9, "preco_fmt": "R$ 29,90", "prazo": 3, "msg_prazo": None, "erro": None},
                "03158": {"disponivel": False, "preco": None, "preco_fmt": None, "prazo": None, "msg_prazo": None, "erro": "Indisponível"},
                "03140": {"disponivel": False, "preco": None, "preco_fmt": None, "prazo": None, "msg_prazo": None, "erro": "Indisponível"},
            }
        }]

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            caminho = generator.gerar_html(pedidos)
            self.assertIn("opcoes_frete.html", caminho)

            # Verifica que o conteúdo HTML foi escrito (pelo menos uma vez)
            handle = mock_file()
            conteudo_escrito = "".join(
                call.args[0] for call in handle.write.call_args_list if call.args
            )
            self.assertIn("Pedido #1001", conteudo_escrito)
            self.assertIn("SEDEX", conteudo_escrito)


# ============== TESTES DE COMPATIBILIDADE ==============


class TestConsultaFreteRetrocompatibilidade(unittest.TestCase):
    """Testes de compatibilidade do script consulta_frete.py."""

    def test_importacao_modulo(self):
        """Valida que consulta_frete.py pode ser importado sem erro."""
        import consulta_frete
        self.assertTrue(hasattr(consulta_frete, "processar"))
        self.assertTrue(hasattr(consulta_frete, "buscar_pedidos_abertos"))
        self.assertTrue(hasattr(consulta_frete, "obter_cep_destino"))

    def test_funcao_processar_existe(self):
        """Valida que processar() é chamável."""
        import consulta_frete
        self.assertTrue(callable(consulta_frete.processar))


# ============== TESTES DE EXCEÇÕES ==============


class TestFreteExceptions(unittest.TestCase):
    """Testes da hierarquia de exceções."""

    def test_hierarquia_frete_error(self):
        self.assertTrue(issubclass(FreteAPIError, FreteError))
        self.assertTrue(issubclass(FreteConnectionError, FreteError))
        self.assertTrue(issubclass(FreteTimeoutError, FreteError))
        self.assertTrue(issubclass(FreteServicoIndisponivelError, FreteError))

    def test_frete_api_error_atributos(self):
        err = FreteAPIError("teste", status_code=500, detalhes="Internal")
        self.assertEqual(err.status_code, 500)
        self.assertEqual(err.detalhes, "Internal")
        self.assertEqual(str(err), "teste")


if __name__ == "__main__":
    unittest.main()
