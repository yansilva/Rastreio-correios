"""
Suíte de testes automatizados para a camada Tiny ERP.

Todos os testes utilizam mocks (unittest.mock) sem chamadas de rede ou credenciais reais.
Compatível tanto com `pytest` quanto com `python -m unittest`.
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Garante que a raiz do projeto e o diretório Arquivos estejam no sys.path
_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_arquivos = os.path.join(_raiz, "Arquivos")
if _raiz not in sys.path:
    sys.path.insert(0, _raiz)
if _arquivos not in sys.path:
    sys.path.insert(0, _arquivos)

import requests
import tiny_rastreio
from tiny import (
    PedidoTiny,
    TinyAPIError,
    TinyAuthError,
    TinyClient,
    TinyConfig,
    TinyConnectionError,
    TinyOrderService,
    TinyTimeoutError,
)


class TestTinyClient(unittest.TestCase):
    """Testes da camada de comunicação HTTP (TinyClient)."""

    def test_token_ausente_lanca_excecao(self):
        """Valida que o cliente exige um token e lança TinyAuthError quando ausente."""
        with patch.dict(os.environ, {"TOKEN_TINY": ""}):
            config_sem_token = TinyConfig(token="")
            with self.assertRaises(TinyAuthError) as ctx:
                TinyClient(config=config_sem_token)
            self.assertIn("Token do Tiny ERP não configurado", str(ctx.exception))

    @patch("requests.get")
    def test_pesquisa_resposta_valida(self, mock_get):
        """Valida que o cliente processa uma resposta 200 JSON de sucesso."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "retorno": {
                "status": "OK",
                "numero_paginas": 1,
                "pedidos": [
                    {
                        "pedido": {
                            "id": "123",
                            "numero": "1001",
                            "situacao": "Aprovado",
                            "codigo_rastreamento": "AA123456789BR",
                        }
                    }
                ],
            }
        }
        mock_get.return_value = mock_response

        client = TinyClient(config=TinyConfig(token="fake_token_123"))
        resultado = client.pesquisar_pedidos("01/01/2026", "31/01/2026", pagina=1)

        self.assertEqual(resultado["retorno"]["status"], "OK")
        self.assertEqual(len(resultado["retorno"]["pedidos"]), 1)
        self.assertEqual(
            resultado["retorno"]["pedidos"][0]["pedido"]["codigo_rastreamento"],
            "AA123456789BR",
        )
        mock_get.assert_called_once()
        # Verifica timeout explícito
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs.get("timeout"), 30.0)

    @patch("requests.get")
    def test_pesquisa_resposta_invalida_json(self, mock_get):
        """Valida tratamento quando a API retorna conteúdo que não é JSON."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON format")
        mock_get.return_value = mock_response

        client = TinyClient(config=TinyConfig(token="fake_token_123"))
        with self.assertRaises(TinyAPIError) as ctx:
            client.pesquisar_pedidos("01/01/2026", "31/01/2026")
        self.assertIn("JSON válido", str(ctx.exception))

    @patch("requests.get")
    def test_pesquisa_erro_http(self, mock_get):
        """Valida tratamento quando a API retorna código HTTP de erro (ex: 500 ou 400)."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        client = TinyClient(config=TinyConfig(token="fake_token_123"))
        with self.assertRaises(TinyAPIError) as ctx:
            client.pesquisar_pedidos("01/01/2026", "31/01/2026")
        self.assertEqual(ctx.exception.status_code, 500)

    @patch("requests.get")
    def test_pesquisa_timeout(self, mock_get):
        """Valida que timeout de rede dispara TinyTimeoutError."""
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        client = TinyClient(config=TinyConfig(token="fake_token_123"))
        with self.assertRaises(TinyTimeoutError) as ctx:
            client.pesquisar_pedidos("01/01/2026", "31/01/2026")
        self.assertIn("Tempo limite", str(ctx.exception))

    @patch("requests.get")
    def test_pesquisa_erro_conexao(self, mock_get):
        """Valida que falha de rede dispara TinyConnectionError."""
        mock_get.side_effect = requests.exceptions.ConnectionError("DNS failure")

        client = TinyClient(config=TinyConfig(token="fake_token_123"))
        with self.assertRaises(TinyConnectionError) as ctx:
            client.pesquisar_pedidos("01/01/2026", "31/01/2026")
        self.assertIn("Falha de conexão", str(ctx.exception))

    @patch("requests.get")
    def test_pesquisar_todos_pedidos_fim_paginacao_erro_6(self, mock_get):
        """Valida parada elegante da paginação ao receber o erro 'A consulta não retornou registros'."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "retorno": {
                "status": "Erro",
                "erros": [{"erro": "A consulta não retornou registros"}],
            }
        }
        mock_get.return_value = mock_resp

        client = TinyClient(config=TinyConfig(token="fake_token_123"))
        pedidos = client.pesquisar_todos_pedidos("01/01/2026", "31/01/2026")
        self.assertEqual(pedidos, [])


class TestTinyOrderService(unittest.TestCase):
    """Testes da camada de regras de negócio (TinyOrderService)."""

    def test_filtro_pedidos_para_rastreio(self):
        """
        Valida as regras de negócio:
        - Mantém pedidos com código começando com 'A' e status ativo.
        - Descarta pedidos 'ENTREGUE' e 'CANCELADO'.
        - Descarta pedidos sem rastreio ou com prefixos não-A.
        """
        pedidos = [
            PedidoTiny(id="1", numero="101", situacao="Aprovado", codigo_rastreamento="AA111111111BR"),
            PedidoTiny(id="2", numero="102", situacao="ENTREGUE", codigo_rastreamento="AA222222222BR"),
            PedidoTiny(id="3", numero="103", situacao="Cancelado", codigo_rastreamento="AA333333333BR"),
            PedidoTiny(id="4", numero="104", situacao="Em Aberto", codigo_rastreamento=None),
            PedidoTiny(id="5", numero="105", situacao="Em Aberto", codigo_rastreamento=""),
            PedidoTiny(id="6", numero="106", situacao="Preparando Envio", codigo_rastreamento="BR999999999"),
            PedidoTiny(id="7", numero="107", situacao="Enviado", codigo_rastreamento="AB777777777BR"),
        ]

        filtrados = TinyOrderService.filtrar_pedidos_para_rastreio(pedidos)
        self.assertEqual(len(filtrados), 2)
        numeros = [p.numero for p in filtrados]
        self.assertIn("101", numeros)
        self.assertIn("107", numeros)

    def test_exportacao_csv(self):
        """Valida a estrutura e conteúdo do arquivo CSV gerado."""
        pedidos = [
            PedidoTiny(id="1", numero="2001", situacao="Aprovado", codigo_rastreamento="AA123456789BR"),
            PedidoTiny(id="2", numero="2002", situacao="Cancelado", codigo_rastreamento="AA987654321BR"),
        ]

        service = TinyOrderService(config=TinyConfig(token="fake_token"))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "rastreios_teste.csv")
            caminho_gerado, total = service.exportar_csv(pedidos, caminho_saida=csv_path)

            self.assertEqual(caminho_gerado, csv_path)
            self.assertEqual(total, 1)  # apenas o pedido 2001 é válido

            with open(csv_path, encoding="utf-8") as f:
                linhas = f.read().splitlines()

            self.assertEqual(linhas[0], "Número do Pedido no Tiny,Situação,Código de Rastreio")
            self.assertEqual(linhas[1], "2001,Aprovado,AA123456789BR")


class TestTinyRetrocompatibilidade(unittest.TestCase):
    """Testes de compatibilidade da fachada Arquivos/tiny_rastreio.py."""

    @patch("tiny.client.TinyClient.pesquisar_todos_pedidos")
    def test_buscar_pedidos_fachada(self, mock_pesquisa):
        """Valida que tiny_rastreio.buscar_pedidos() retorna lista de dicionários original."""
        mock_pesquisa.return_value = [
            {
                "pedido": {
                    "id": "99",
                    "numero": "3001",
                    "situacao": "Pronto",
                    "codigo_rastreamento": "AA555555555BR",
                }
            }
        ]

        with patch.object(tiny_rastreio, "TOKEN", "fake_token_123"):
            with patch.dict(os.environ, {"TOKEN_TINY": "fake_token_123"}):
                pedidos = tiny_rastreio.buscar_pedidos()
                self.assertEqual(len(pedidos), 1)
                self.assertEqual(pedidos[0]["pedido"]["numero"], "3001")

    def test_gerar_csv_fachada(self):
        """Valida que tiny_rastreio.gerar_csv() recebe lista de dicionários e retorna tupla esperada."""
        dados = [
            {
                "pedido": {
                    "id": "1",
                    "numero": "4001",
                    "situacao": "Aguardando",
                    "codigo_rastreamento": "AA666666666BR",
                }
            }
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_csv = os.path.join(tmpdir, "rastreios_tiny.csv")
            with patch("tiny_rastreio._dir_atual", tmpdir):
                caminho, total = tiny_rastreio.gerar_csv(dados)
                self.assertEqual(caminho, fake_csv)
                self.assertEqual(total, 1)
                self.assertTrue(os.path.exists(fake_csv))

    def test_processar_sem_token_retorna_falso_com_mensagem_amigavel(self):
        """Valida que processar() sem token não gera exceção não tratada e retorna False."""
        with patch.dict(os.environ, {"TOKEN_TINY": ""}, clear=True):
            with patch("tiny.config.TinyConfig.token", ""):
                sucesso = tiny_rastreio.processar()
                self.assertFalse(sucesso)


if __name__ == "__main__":
    unittest.main()
