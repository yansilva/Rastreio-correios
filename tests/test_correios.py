"""
Suíte de testes automatizados para a camada dos Correios.

Todos os testes utilizam mocks (unittest.mock) sem chamadas de rede ou credenciais reais.
Compatível tanto com `pytest` quanto com `python -m unittest`.
"""
import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Garante que a raiz do projeto e o diretório Arquivos estejam no sys.path
_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_arquivos = os.path.join(_raiz, "Arquivos")
if _raiz not in sys.path:
    sys.path.insert(0, _raiz)
if _arquivos not in sys.path:
    sys.path.insert(0, _arquivos)

import consulta_correios
import requests
from correios import (
    CorreiosAuthError,
    CorreiosClient,
    CorreiosConfig,
    CorreiosConnectionError,
    CorreiosTimeoutError,
    ObjetoRastreio,
    TrackingService,
)


class TestCorreiosConfig(unittest.TestCase):
    """Testes de configuração da integração com os Correios."""

    def test_credenciais_ausentes(self):
        """Valida detecção de credenciais vazias."""
        with patch.dict(os.environ, {"ID_CORREIOS": "", "CONTRATO": "", "CODIGO_ACESSO": ""}, clear=True):
            config = CorreiosConfig(id_correios="", contrato="", codigo_acesso="")
            self.assertFalse(config.credenciais_preenchidas())

    def test_credenciais_preenchidas(self):
        """Valida detecção de credenciais fornecidas."""
        config = CorreiosConfig(id_correios="123456", contrato="9999", codigo_acesso="secret123")
        self.assertTrue(config.credenciais_preenchidas())

    def test_repr_mascara_credenciais(self):
        """Valida que __repr__ não expõe dados sensíveis."""
        config = CorreiosConfig(id_correios="123456789", contrato="99123456", codigo_acesso="ultra_secret_key")
        representacao = repr(config)
        self.assertNotIn("ultra_secret_key", representacao)
        self.assertIn("123...89", representacao)


class TestCorreiosClient(unittest.TestCase):
    """Testes da camada de comunicação HTTP (CorreiosClient)."""

    def test_gerar_token_sem_credenciais_lanca_excecao(self):
        """Valida que gerar_token() exige credenciais configuradas."""
        with patch.dict(os.environ, {"ID_CORREIOS": "", "CONTRATO": "", "CODIGO_ACESSO": ""}, clear=True):
            config = CorreiosConfig(id_correios="", contrato="", codigo_acesso="")
            client = CorreiosClient(config=config)
            with self.assertRaises(CorreiosAuthError) as ctx:
                client.gerar_token()
            self.assertIn("Credenciais dos Correios não configuradas", str(ctx.exception))

    @patch("requests.post")
    def test_gerar_token_sucesso(self, mock_post):
        """Valida obtenção de token com status HTTP 201."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"token": "mock_jwt_token_correios"}
        mock_post.return_value = mock_response

        config = CorreiosConfig(id_correios="123", contrato="456", codigo_acesso="xyz")
        client = CorreiosClient(config=config)
        token = client.gerar_token()

        self.assertEqual(token, "mock_jwt_token_correios")
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs.get("timeout"), 30.0)

    @patch("requests.post")
    def test_gerar_token_cache_reutilizacao(self, mock_post):
        """Valida que chamadas subsequentes reutilizam o token em memória sem nova requisição."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"token": "cached_token"}
        mock_post.return_value = mock_response

        config = CorreiosConfig(id_correios="123", contrato="456", codigo_acesso="xyz")
        client = CorreiosClient(config=config)
        token1 = client.gerar_token()
        token2 = client.gerar_token()

        self.assertEqual(token1, "cached_token")
        self.assertEqual(token2, "cached_token")
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_gerar_token_erro_autenticacao_401(self, mock_post):
        """Valida que status 401 dispara CorreiosAuthError."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        config = CorreiosConfig(id_correios="123", contrato="456", codigo_acesso="xyz")
        client = CorreiosClient(config=config)
        with self.assertRaises(CorreiosAuthError):
            client.gerar_token()

    @patch("requests.post")
    def test_gerar_token_timeout(self, mock_post):
        """Valida que timeout no POST dispara CorreiosTimeoutError."""
        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")

        config = CorreiosConfig(id_correios="123", contrato="456", codigo_acesso="xyz")
        client = CorreiosClient(config=config)
        with self.assertRaises(CorreiosTimeoutError):
            client.gerar_token()

    @patch("requests.get")
    def test_consultar_objeto_sucesso(self, mock_get):
        """Valida consulta com sucesso (HTTP 200) e retorno do objeto."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "objetos": [
                {
                    "codObjeto": "AA123456789BR",
                    "eventos": [{"descricao": "Objeto postado"}],
                }
            ]
        }
        mock_get.return_value = mock_response

        config = CorreiosConfig(id_correios="123", contrato="456", codigo_acesso="xyz")
        client = CorreiosClient(config=config)
        client._token = "fake_token"

        resultado = client.consultar_objeto("AA123456789BR")
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado["codObjeto"], "AA123456789BR")
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs.get("timeout"), 30.0)

    @patch("requests.get")
    def test_consultar_objeto_404_retorna_none(self, mock_get):
        """Valida que objeto não encontrado (HTTP 404) retorna None sem erro."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        config = CorreiosConfig(id_correios="123", contrato="456", codigo_acesso="xyz")
        client = CorreiosClient(config=config)
        client._token = "fake_token"

        resultado = client.consultar_objeto("XX999999999BR")
        self.assertIsNone(resultado)

    @patch("requests.get")
    def test_consultar_objeto_timeout(self, mock_get):
        """Valida que timeout na consulta dispara CorreiosTimeoutError."""
        mock_get.side_effect = requests.exceptions.Timeout("Read timeout")

        config = CorreiosConfig(id_correios="123", contrato="456", codigo_acesso="xyz")
        client = CorreiosClient(config=config)
        client._token = "fake_token"

        with self.assertRaises(CorreiosTimeoutError):
            client.consultar_objeto("AA123456789BR")

    @patch("requests.get")
    def test_consultar_objeto_erro_conexao(self, mock_get):
        """Valida que erro de rede dispara CorreiosConnectionError."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Network down")

        config = CorreiosConfig(id_correios="123", contrato="456", codigo_acesso="xyz")
        client = CorreiosClient(config=config)
        client._token = "fake_token"

        with self.assertRaises(CorreiosConnectionError):
            client.consultar_objeto("AA123456789BR")


class TestTrackingService(unittest.TestCase):
    """Testes das regras de negócio de rastreamento (TrackingService)."""

    def test_processar_objeto_entregue(self):
        """Valida classificação de objeto entregue."""
        dados = {
            "eventos": [
                {
                    "descricao": "Objeto entregue ao destinatário",
                    "dtHrCriado": "2026-09-08T14:30:00",
                    "unidade": {"endereco": {"cidade": "São Paulo", "uf": "SP"}},
                },
                {
                    "descricao": "Objeto postado",
                    "dtHrCriado": "2026-09-05T10:00:00",
                },
            ]
        }
        obj = TrackingService.processar_objeto("AA123456789BR", dados)
        self.assertTrue(obj.is_entregue)
        self.assertTrue(obj.is_postado)
        self.assertEqual(obj.status_categoria, "entregue")
        self.assertEqual(obj.ultimo_local, "São Paulo/SP")

    def test_processar_objeto_devolvido(self):
        """Valida classificação de objeto devolvido ao remetente."""
        dados = {
            "eventos": [
                {
                    "descricao": "Objeto devolvido ao remetente",
                    "dtHrCriado": "2026-09-09T16:00:00",
                    "unidade": {"endereco": {"cidade": "Curitiba", "uf": "PR"}},
                },
                {
                    "descricao": "Objeto postado",
                    "dtHrCriado": "2026-09-01T10:00:00",
                },
            ]
        }
        obj = TrackingService.processar_objeto("AA222222222BR", dados)
        self.assertTrue(obj.is_devolvido)
        self.assertEqual(obj.status_categoria, "devolvido")

    def test_processar_objeto_aguardando_retirada(self):
        """Valida detecção de encomenda aguardando retirada na agência."""
        dados = {
            "eventos": [
                {
                    "descricao": "Objeto aguardando retirada na agência dos Correios",
                    "detalhe": "Para retirada, compareça à agência indicada",
                    "dtHrCriado": "2026-09-09T11:00:00",
                    "unidade": {"endereco": {"cidade": "Belo Horizonte", "uf": "MG"}},
                },
                {
                    "descricao": "Objeto postado",
                    "dtHrCriado": "2026-09-06T09:00:00",
                },
            ]
        }
        obj = TrackingService.processar_objeto("AA333333333BR", dados)
        self.assertTrue(obj.is_retirada)
        self.assertTrue(obj.is_postado)
        self.assertEqual(obj.status_categoria, "em_transito")

    def test_processar_objeto_sem_eventos(self):
        """Valida que objeto sem eventos é classificado como 'nao_enviado'."""
        obj = TrackingService.processar_objeto("AA444444444BR", None)
        self.assertEqual(obj.status_categoria, "nao_enviado")
        self.assertFalse(obj.is_postado)
        self.assertEqual(len(obj.eventos), 0)

    def test_verificar_atraso_classificacao_urgencia(self):
        """Valida cálculo de dias em trânsito e níveis de urgência."""
        ref_now = datetime(2026, 9, 10, 12, 0, 0)

        # 8 dias de trânsito -> CRÍTICO
        obj_critico = ObjetoRastreio(
            codigo="AA888888888BR",
            status_categoria="em_transito",
            is_postado=True,
            data_postagem_dt=ref_now - timedelta(days=8),
            ultimo_evento_desc="Em trânsito",
            ultimo_local="SP/SP",
        )
        atraso_critico = TrackingService.verificar_atraso(obj_critico, "1001", "Aprovado", data_referencia=ref_now)
        self.assertIsNotNone(atraso_critico)
        self.assertEqual(atraso_critico.dias_transito, 8)
        self.assertEqual(atraso_critico.urgencia_label, "CRÍTICO")
        self.assertEqual(atraso_critico.urgencia_class, "urgencia-alta")

        # 6 dias de trânsito -> ALTO
        obj_alto = ObjetoRastreio(
            codigo="AA666666666BR",
            status_categoria="em_transito",
            is_postado=True,
            data_postagem_dt=ref_now - timedelta(days=6),
        )
        atraso_alto = TrackingService.verificar_atraso(obj_alto, "1002", "Aprovado", data_referencia=ref_now)
        self.assertIsNotNone(atraso_alto)
        self.assertEqual(atraso_alto.urgencia_label, "ALTO")

        # 4 dias de trânsito -> ATENÇÃO
        obj_atencao = ObjetoRastreio(
            codigo="AA444444444BR",
            status_categoria="em_transito",
            is_postado=True,
            data_postagem_dt=ref_now - timedelta(days=4),
        )
        atraso_atencao = TrackingService.verificar_atraso(obj_atencao, "1003", "Aprovado", data_referencia=ref_now)
        self.assertIsNotNone(atraso_atencao)
        self.assertEqual(atraso_atencao.urgencia_label, "ATENÇÃO")

        # 2 dias de trânsito -> Não atrasado (<= 3 dias)
        obj_ok = ObjetoRastreio(
            codigo="AA222222222BR",
            status_categoria="em_transito",
            is_postado=True,
            data_postagem_dt=ref_now - timedelta(days=2),
        )
        self.assertIsNone(TrackingService.verificar_atraso(obj_ok, "1004", "Aprovado", data_referencia=ref_now))

    def test_entregue_nao_consta_como_atrasado(self):
        """Valida que pedidos já entregues com sucesso não aparecem no relatório de atrasados."""
        ref_now = datetime(2026, 9, 10, 12, 0, 0)
        obj_entregue = ObjetoRastreio(
            codigo="AA111111111BR",
            status_categoria="entregue",
            is_entregue=True,
            is_postado=True,
            data_postagem_dt=ref_now - timedelta(days=10),
            data_entrega_dt=ref_now - timedelta(days=1),
        )
        atraso = TrackingService.verificar_atraso(obj_entregue, "1005", "Entregue", data_referencia=ref_now)
        self.assertIsNone(atraso)

    def test_deve_ocultar_card_devolvido_apos_24h(self):
        """Valida ocultamento de cards devolvidos após 24h."""
        ref_now = datetime(2026, 9, 10, 12, 0, 0)
        obj_devolvido_antigo = ObjetoRastreio(
            codigo="AA123BR",
            status_categoria="devolvido",
            data_devolucao_dt=ref_now - timedelta(hours=25),
        )
        self.assertTrue(TrackingService.deve_ocultar_card(obj_devolvido_antigo, data_referencia=ref_now))

        obj_devolvido_recente = ObjetoRastreio(
            codigo="AA124BR",
            status_categoria="devolvido",
            data_devolucao_dt=ref_now - timedelta(hours=5),
        )
        self.assertFalse(TrackingService.deve_ocultar_card(obj_devolvido_recente, data_referencia=ref_now))


class TestConsultaCorreiosRetrocompatibilidade(unittest.TestCase):
    """Testes de compatibilidade do script consulta_correios.py."""

    @patch("correios.client.CorreiosClient.gerar_token")
    def test_obter_token_fachada(self, mock_gerar):
        """Valida que obter_token() da fachada delega para CorreiosClient."""
        mock_gerar.return_value = "token_de_teste"
        token = consulta_correios.obter_token()
        self.assertEqual(token, "token_de_teste")
        mock_gerar.assert_called_once()

    @patch("correios.client.CorreiosClient.consultar_objeto")
    def test_consultar_objeto_fachada(self, mock_consultar):
        """Valida que consultar_objeto() da fachada delega para CorreiosClient."""
        mock_consultar.return_value = {"codObjeto": "AA123BR"}
        res = consulta_correios.consultar_objeto("AA123BR", "token123")
        self.assertEqual(res["codObjeto"], "AA123BR")
        mock_consultar.assert_called_once_with("AA123BR", token="token123")

    def test_processar_sem_credenciais_retorna_falso_com_mensagem(self):
        """Valida que processar() sem credenciais não quebra e exibe mensagem amigável."""
        with patch.dict(os.environ, {"ID_CORREIOS": "", "CONTRATO": "", "CODIGO_ACESSO": ""}, clear=True):
            resultado = consulta_correios.processar()
            self.assertFalse(resultado)


if __name__ == "__main__":
    unittest.main()
