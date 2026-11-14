"""Frete: serviços por preço (do mais barato ao mais caro) e aviso único de prazo indisponível no lote."""

import re
import sys
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
ARQUIVOS_DIR = PROJECT_ROOT / "Arquivos"
for caminho in (PROJECT_ROOT, ARQUIVOS_DIR):
    if str(caminho) not in sys.path:
        sys.path.insert(0, str(caminho))

from frete.config import FreteConfig  # noqa: E402
from frete.report import FreteReportGenerator  # noqa: E402

CODIGOS = list(FreteConfig().servicos.keys())


def _servico(preco, prazo):
    return {
        "disponivel": True,
        "preco": preco,
        "preco_fmt": f"R$ {preco:.2f}".replace(".", ","),
        "prazo": prazo,
        "msg_prazo": "",
    }


def _pedido(servicos, numero="1001"):
    return {
        "numero": numero, "situacao": "Aberto", "nome_cliente": "Teste", "valor": 100.0,
        "cep_destino": "01001000", "destino_label": "São Paulo/SP", "servicos": servicos,
    }


def _renderizar(pedidos):
    generator = FreteReportGenerator(config=FreteConfig(cep_origem="05617010"))
    with patch("builtins.open", mock_open()) as arquivo:
        generator.gerar_html(pedidos)
        return "".join(c.args[0] for c in arquivo().write.call_args_list[:1] if c.args)


def _precos_na_ordem(html):
    return [float(p.replace("R$", "").replace(".", "").replace(",", ".").strip())
            for p in re.findall(r'class="servico-preco">([^<]+)<', html)]


class TestOrdemPorPreco(unittest.TestCase):
    def test_servicos_do_mais_barato_ao_mais_caro(self):
        html = _renderizar([_pedido({
            CODIGOS[0]: _servico(54.0, 2),
            CODIGOS[1]: _servico(12.5, 1),
            CODIGOS[2]: _servico(31.0, 3),
        })])
        self.assertEqual(_precos_na_ordem(html), [12.5, 31.0, 54.0])

    def test_indisponiveis_vao_para_o_fim(self):
        html = _renderizar([_pedido({
            CODIGOS[0]: {"disponivel": False},
            CODIGOS[1]: _servico(40.0, 2),
            CODIGOS[2]: _servico(10.0, 1),
        })])
        # Só os disponíveis viram cartões, na ordem de preço; o indisponível fica na nota do pedido
        self.assertEqual(_precos_na_ordem(html), [10.0, 40.0])
        self.assertEqual(html.count('class="servico-card disponivel'), 2)


class TestAvisoDePrazoNoLote(unittest.TestCase):
    def test_sem_nenhum_prazo_no_lote_avisa_uma_vez_no_resumo(self):
        html = _renderizar([
            _pedido({CODIGOS[0]: _servico(20.0, None), CODIGOS[1]: _servico(30.0, None)}, "1001"),
            _pedido({CODIGOS[0]: _servico(22.0, None)}, "1002"),
        ])
        self.assertEqual(html.count("Prazos indisponíveis nesta consulta"), 1)
        self.assertNotIn("Prazo indisponível", html)
        self.assertNotIn('class="servico-prazo"', html)

    def test_alguns_sem_prazo_mantem_o_aviso_por_cartao(self):
        html = _renderizar([_pedido({CODIGOS[0]: _servico(20.0, None), CODIGOS[1]: _servico(30.0, 2)})])
        self.assertNotIn("Prazos indisponíveis nesta consulta", html)
        self.assertIn("Prazo indisponível", html)
        self.assertIn("2 dias úteis", html)

    def test_lote_sem_servico_disponivel_nao_mostra_o_aviso_do_lote(self):
        html = _renderizar([_pedido({CODIGOS[0]: {"disponivel": False}})])
        self.assertNotIn("Prazos indisponíveis nesta consulta", html)


if __name__ == "__main__":
    unittest.main()
