"""Testes do histórico de entregas (aba Entregues): registro, poda, semanas, resumo e arquivo."""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_arquivos = os.path.join(_raiz, "Arquivos")
for _caminho in (_raiz, _arquivos):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from correios import historico_entregas as hist  # noqa: E402
from correios.models import EventoRastreio, ObjetoRastreio  # noqa: E402


def _entregue(codigo, entregue_em, postado_em=None, cidade="RIO DE JANEIRO", uf="RJ"):
    evento = EventoRastreio(dt_hr_criado=entregue_em.isoformat(), descricao="Objeto entregue ao destinatário",
                            cidade=cidade, uf=uf)
    return ObjetoRastreio(
        codigo=codigo,
        eventos=[evento],
        status_categoria="entregue",
        is_entregue=True,
        data_entrega_dt=entregue_em,
        data_postagem_dt=postado_em,
        ultimo_local=f"{cidade}/{uf}",
    )


def _item(rastreio, entregue_em, postado_em=None):
    return {
        "pedido": rastreio,
        "cliente": "",
        "rastreio": rastreio,
        "cidade": "SP/SP",
        "postado_em": postado_em.isoformat(timespec="seconds") if postado_em else None,
        "entregue_em": entregue_em.isoformat(timespec="seconds"),
        "registrado_em": entregue_em.isoformat(timespec="seconds"),
    }


AGORA = datetime(2026, 11, 12, 15, 0, 0)


class TestCidadeDaEntrega(unittest.TestCase):
    """A cidade vem do evento de entrega (BDE/01), não de um "não entregue" mais recente."""

    def test_nao_entregue_mais_recente_nao_troca_a_cidade(self):
        from correios.tracking import TrackingService

        dados = {
            "eventos": [
                {
                    "codigo": "BDE",
                    "tipo": "20",
                    "descricao": "Objeto não entregue - destinatário ausente",
                    "dtHrCriado": "2026-11-12T09:00:00",
                    "unidade": {"endereco": {"cidade": "CAMPINAS", "uf": "SP"}},
                },
                {
                    "codigo": "BDE",
                    "tipo": "01",
                    "descricao": "Objeto entregue ao destinatário",
                    "dtHrCriado": "2026-11-11T14:00:00",
                    "unidade": {"endereco": {"cidade": "RIO DE JANEIRO", "uf": "RJ"}},
                },
                {
                    "codigo": "PO",
                    "tipo": "01",
                    "descricao": "Objeto postado",
                    "dtHrCriado": "2026-11-09T10:00:00",
                    "unidade": {"endereco": {"cidade": "SAO PAULO", "uf": "SP"}},
                },
            ]
        }
        objeto = TrackingService.processar_objeto("AE000000001BR", dados)
        self.assertEqual(objeto.status_categoria, "entregue")

        dicionario = hist._estrutura_vazia()
        self.assertTrue(hist.registrar_entrega(dicionario, objeto, "43000", "Cliente", AGORA))
        self.assertEqual(dicionario["entregas"]["AE000000001BR"]["cidade"], "RIO DE JANEIRO/RJ")


class TestRegistro(unittest.TestCase):
    def test_registra_entregue_uma_vez(self):
        dados = hist.carregar("inexistente.json")
        objeto = _entregue("AE111BR", datetime(2026, 11, 11, 10, 15), datetime(2026, 11, 7, 14, 2))
        primeiro = datetime(2026, 11, 11, 10, 47, 12)
        self.assertTrue(hist.registrar_entrega(dados, objeto, "42934", "Fulano", primeiro))
        self.assertFalse(hist.registrar_entrega(dados, objeto, "42934", "Fulano", datetime(2026, 11, 12, 9, 0)))
        item = dados["entregas"]["AE111BR"]
        self.assertEqual(item["registrado_em"], primeiro.isoformat(timespec="seconds"))
        self.assertEqual(item["cidade"], "RIO DE JANEIRO/RJ")
        self.assertEqual(item["postado_em"], "2026-11-07T14:02:00")
        self.assertEqual(set(item), {"pedido", "cliente", "rastreio", "cidade", "postado_em", "entregue_em", "registrado_em"})

    def test_ignora_nao_entregue(self):
        dados = hist.carregar("inexistente.json")
        objeto = ObjetoRastreio(codigo="AE222BR", status_categoria="em_transito", is_postado=True)
        self.assertFalse(hist.registrar_entrega(dados, objeto, "1", "X", AGORA))
        self.assertEqual(dados["entregas"], {})

    def test_cidade_cai_para_ultimo_local_sem_evento_de_entrega(self):
        dados = hist.carregar("inexistente.json")
        objeto = _entregue("AE333BR", datetime(2026, 11, 11, 10, 15))
        objeto.eventos = [EventoRastreio(dt_hr_criado="2026-11-11T10:15:00", descricao="Saiu para entrega")]
        objeto.ultimo_local = "CURITIBA/PR"
        hist.registrar_entrega(dados, objeto, "2", "Y", AGORA)
        self.assertEqual(dados["entregas"]["AE333BR"]["cidade"], "CURITIBA/PR")


class TestArquivo(unittest.TestCase):
    def test_carregar_arquivo_ausente_ou_corrompido(self):
        with tempfile.TemporaryDirectory() as pasta:
            vazio = {"versao": 1, "acompanhados": {}, "entregas": {}}
            self.assertEqual(hist.carregar(os.path.join(pasta, "nao_existe.json")), vazio)
            ruim = os.path.join(pasta, "ruim.json")
            Path(ruim).write_text("{x", encoding="utf-8")
            self.assertEqual(hist.carregar(ruim), vazio)
            Path(ruim).write_text("[1, 2]", encoding="utf-8")
            self.assertEqual(hist.carregar(ruim), vazio)

    def test_salvar_e_carregar_ida_e_volta(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "entregas_historico.json")
            dados = {"versao": 1, "acompanhados": {"AE1": {"pedido": "9"}}, "entregas": {"AE2": _item("AE2", AGORA)}}
            hist.salvar(caminho, dados)
            self.assertEqual(hist.carregar(caminho), dados)
            self.assertFalse(os.path.exists(caminho + ".tmp"))
            self.assertEqual(json.loads(Path(caminho).read_text(encoding="utf-8")), dados)


class TestEntradasIncompletas(unittest.TestCase):
    def test_carregar_descarta_entrada_sem_data_de_entrega_valida(self):
        bruto = {
            "versao": 1,
            "acompanhados": {},
            "entregas": {
                "BOA": _item("BOA", datetime(2026, 11, 10, 9)),
                "SEM_DATA": {"pedido": "1", "rastreio": "SEM_DATA"},
                "DATA_RUIM": {"pedido": "2", "rastreio": "DATA_RUIM", "entregue_em": "ontem"},
                "NAO_DICT": "x",
            },
        }
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "entregas_historico.json")
            Path(caminho).write_text(json.dumps(bruto), encoding="utf-8")
            with self.assertLogs("correios.historico", level="WARNING") as aviso:
                dados = hist.carregar(caminho)
        self.assertEqual(set(dados["entregas"]), {"BOA"})
        self.assertTrue(any("descartada" in linha for linha in aviso.output))

    def test_podar_e_semana_ignoram_entrada_incompleta(self):
        dados = {
            "versao": 1,
            "acompanhados": {},
            "entregas": {
                "BOA": _item("BOA", datetime(2026, 11, 10, 9)),
                "SEM_DATA": {"rastreio": "SEM_DATA"},
                "DATA_RUIM": {"rastreio": "DATA_RUIM", "entregue_em": "ontem"},
            },
        }
        self.assertEqual([i["rastreio"] for i in hist.entregas_da_semana(dados, AGORA)], ["BOA"])
        hist.podar(dados, AGORA)
        self.assertEqual(set(dados["entregas"]), {"BOA"})

    def test_dias_com_postagem_invalida_fica_none(self):
        item = _item("X", datetime(2026, 11, 10, 9))
        item["postado_em"] = "semana passada"
        self.assertIsNone(hist.dias_ate_entrega(item))
        self.assertEqual(hist.resumo([item])["media_dias"], None)


class TestSemanas(unittest.TestCase):
    def test_podar_mantem_semana_atual_e_anterior(self):
        dados = {
            "versao": 1,
            "acompanhados": {},
            "entregas": {
                "NOVA": _item("NOVA", datetime(2026, 11, 10, 9)),
                "ANTERIOR": _item("ANTERIOR", datetime(2026, 11, 4, 9)),
                "VELHA": _item("VELHA", datetime(2026, 10, 28, 9)),
            },
        }
        hist.podar(dados, AGORA)
        self.assertEqual(set(dados["entregas"]), {"NOVA", "ANTERIOR"})

    def test_semana_anterior_na_virada_de_ano(self):
        agora = datetime(2027, 1, 4, 10, 0, 0)
        dados = {"versao": 1, "acompanhados": {}, "entregas": {"FIM": _item("FIM", datetime(2026, 12, 29, 10))}}
        self.assertEqual(hist.entregas_da_semana(dados, agora, deslocamento=0), [])
        anterior = hist.entregas_da_semana(dados, agora, deslocamento=-1)
        self.assertEqual([i["rastreio"] for i in anterior], ["FIM"])
        hist.podar(dados, agora)
        self.assertIn("FIM", dados["entregas"])

    def test_entregas_da_semana_ordem_mais_recente_primeiro(self):
        dados = {
            "versao": 1,
            "acompanhados": {},
            "entregas": {
                "A": _item("A", datetime(2026, 11, 9, 8)),
                "B": _item("B", datetime(2026, 11, 11, 8)),
                "C": _item("C", datetime(2026, 11, 10, 8)),
            },
        }
        self.assertEqual([i["rastreio"] for i in hist.entregas_da_semana(dados, AGORA)], ["B", "C", "A"])


class TestResumo(unittest.TestCase):
    def test_resumo_media_e_mais_demorado(self):
        lista = [
            _item("R1", datetime(2026, 11, 10, 12), datetime(2026, 11, 8, 12)),  # 2,0 dias
            _item("R2", datetime(2026, 11, 11, 12), datetime(2026, 11, 6, 0)),  # 5,5 dias
        ]
        self.assertEqual(hist.dias_ate_entrega(lista[0]), 2.0)
        resultado = hist.resumo(lista)
        self.assertEqual(resultado["total"], 2)
        self.assertEqual(resultado["media_dias"], 3.8)
        self.assertEqual(resultado["mais_demorado"]["rastreio"], "R2")
        self.assertEqual(hist.dias_ate_entrega(lista[1]), 5.5)

    def test_resumo_sem_postagem_fica_fora_da_media(self):
        lista = [
            _item("S1", datetime(2026, 11, 10, 12), datetime(2026, 11, 8, 12)),  # 2,0 dias
            _item("S2", datetime(2026, 11, 11, 12)),  # sem postagem
        ]
        self.assertIsNone(hist.dias_ate_entrega(lista[1]))
        resultado = hist.resumo(lista)
        self.assertEqual(resultado["total"], 2)
        self.assertEqual(resultado["media_dias"], 2.0)
        self.assertEqual(resultado["mais_demorado"]["rastreio"], "S1")

    def test_resumo_lista_vazia(self):
        self.assertEqual(hist.resumo([]), {"total": 0, "media_dias": None, "mais_demorado": None})


if __name__ == "__main__":
    unittest.main()
