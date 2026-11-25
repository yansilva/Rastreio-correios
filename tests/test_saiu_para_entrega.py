"""Classificação dos eventos dos Correios pelo código (codigo/tipo), com o texto como reserva.

Cobre o status "saiu para entrega" (OEC/01) e o bug de "não entregue" virar entregue (BDE/02, BDE/20, BDI/26...).
"""
import os
import sys
import unittest
from datetime import datetime

_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_arquivos = os.path.join(_raiz, "Arquivos")
for _caminho in (_raiz, _arquivos):
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)

from correios import ObjetoRastreio, TrackingService  # noqa: E402

AVISO_PRAZO = "Sua entrega ou retirada nos Correios pode levar mais tempo do que o previsto"


def _ev(codigo, tipo, descricao, data="2026-11-24T10:00:00"):
    return {"codigo": codigo, "tipo": tipo, "descricao": descricao, "dtHrCriado": data}


def _sem_codigo(descricao, data="2026-11-24T10:00:00"):
    return {"descricao": descricao, "dtHrCriado": data}


def _objeto(*eventos):
    """Eventos na ordem da API: o primeiro é o mais recente."""
    return TrackingService.processar_objeto("AE000000001BR", {"eventos": list(eventos)})


SAIU = _ev("OEC", "01", "Objeto saiu para entrega ao destinatário", "2026-11-24T08:00:00")
POSTADO = _ev("PO", "01", "Objeto postado", "2026-11-20T10:00:00")


class TestCampoSaiuParaEntrega(unittest.TestCase):
    def test_campo_existe_e_comeca_falso(self):
        self.assertFalse(ObjetoRastreio(codigo="AE000000001BR").saiu_para_entrega)


class TestSaiuComoStatusMaisRecente(unittest.TestCase):
    def test_oec01_mais_recente_marca_saiu_para_entrega(self):
        obj = _objeto(SAIU, POSTADO)
        self.assertTrue(obj.saiu_para_entrega)
        self.assertFalse(obj.is_entregue)
        self.assertFalse(obj.is_devolvido)

    def test_saiu_continua_em_transito(self):
        # O selo "Saiu para entrega" é do cartão; a categoria segue em trânsito (conta em Atrasados)
        self.assertEqual(_objeto(SAIU, POSTADO).status_categoria, "em_transito")


class TestAvisoPorCimaNaoDesfaz(unittest.TestCase):
    def test_aviso_de_prazo_por_cima_nao_desfaz(self):
        obj = _objeto(_ev("FC", "08", AVISO_PRAZO, "2026-11-24T12:09:00"), SAIU, POSTADO)
        self.assertTrue(obj.saiu_para_entrega)
        self.assertEqual(obj.aviso_texto, AVISO_PRAZO)

    def test_inconsistencia_por_cima_nao_desfaz(self):
        obj = _objeto(_ev("BDE", "19", "Inconsistências no endereçamento do objeto.", "2026-11-24T12:09:00"), SAIU)
        self.assertTrue(obj.saiu_para_entrega)


class TestStatusDepoisDesfaz(unittest.TestCase):
    def test_nao_entregue_depois_desfaz(self):
        obj = _objeto(_ev("BDE", "02", "Objeto não entregue - carteiro não atendido"), SAIU, POSTADO)
        self.assertFalse(obj.saiu_para_entrega)

    def test_transferencia_e_outros_status_depois_desfazem(self):
        for codigo, tipo, descricao in (
            ("DO", "01", "Objeto em transferência - por favor aguarde"),
            ("RO", "01", "Objeto em transferência - por favor aguarde"),
            ("EST", "11", "Favor desconsiderar a informação anterior"),
            ("FC", "03", "Objeto em correção de rota"),
        ):
            with self.subTest(evento=f"{codigo}/{tipo}"):
                obj = _objeto(_ev(codigo, tipo, descricao, "2026-11-24T12:00:00"), SAIU, POSTADO)
                self.assertFalse(obj.saiu_para_entrega)


class TestOec09NaoConta(unittest.TestCase):
    def test_saiu_para_entrega_ao_remetente_nao_marca(self):
        obj = _objeto(_ev("OEC", "09", "Objeto saiu para entrega ao remetente"), SAIU, POSTADO)
        self.assertFalse(obj.saiu_para_entrega)
        self.assertTrue(obj.is_devolvido)  # comportamento de devolução continua o mesmo
        self.assertEqual(obj.status_categoria, "devolvido")


class TestNaoEntregueNaoViraEntregue(unittest.TestCase):
    def test_bde02_nao_e_entregue(self):
        obj = _objeto(_ev("BDE", "02", "Objeto não entregue - carteiro não atendido"), POSTADO)
        self.assertFalse(obj.is_entregue)
        self.assertEqual(obj.status_categoria, "em_transito")

    def test_bde20_nao_e_entregue(self):
        obj = _objeto(_ev("BDE", "20", "Objeto não entregue - carteiro não atendido"), POSTADO)
        self.assertFalse(obj.is_entregue)

    def test_bdi26_prazo_de_retirada_encerrado_nao_e_entregue(self):
        obj = _objeto(_ev("BDI", "26", "Objeto não entregue - prazo de retirada encerrado"), POSTADO)
        self.assertFalse(obj.is_entregue)
        self.assertIsNone(obj.data_entrega_dt)

    def test_nao_entregue_sem_codigo_nao_vira_entregue(self):
        obj = _objeto(_sem_codigo("Objeto não entregue - carteiro não atendido"), POSTADO)
        self.assertFalse(obj.is_entregue)

    def test_entregue_ao_destinatario_continua_entregue(self):
        obj = _objeto(_ev("BDE", "01", "Objeto entregue ao destinatário", "2026-11-24T14:00:00"), POSTADO)
        self.assertTrue(obj.is_entregue)
        self.assertEqual(obj.status_categoria, "entregue")
        self.assertEqual(obj.data_entrega_dt, datetime(2026, 11, 24, 14, 0, 0))

    def test_caso_ae16_aguardando_retirada_nao_e_entregue(self):
        # Último evento LDI/01 ("aguardando retirada"); o BDE/98 "não entregue" estava marcado como entrega
        obj = _objeto(
            _ev("LDI", "01", "Objeto aguardando retirada no endereço indicado", "2026-11-19T13:00:00"),
            _ev("RO", "01", "Objeto em transferência - por favor aguarde", "2026-11-18T09:00:00"),
            _ev("BDE", "98", "Objeto não entregue - Endereço insuficiente", "2026-11-18T08:00:00"),
            _ev("OEC", "01", "Objeto saiu para entrega ao destinatário", "2026-11-18T07:00:00"),
            _ev("PO", "01", "Objeto postado", "2026-11-17T16:22:04"),
        )
        self.assertFalse(obj.is_entregue)
        self.assertEqual(obj.status_categoria, "em_transito")
        self.assertTrue(obj.is_retirada)
        self.assertFalse(obj.saiu_para_entrega)


class TestEntregueOuDevolvidoNuncaSaiu(unittest.TestCase):
    def test_entregue_nunca_marca_saiu(self):
        # OEC/01 mais recente, mas o objeto já consta como entregue: saiu não vale
        obj = _objeto(SAIU, _ev("BDE", "01", "Objeto entregue ao destinatário", "2026-11-23T14:00:00"), POSTADO)
        self.assertTrue(obj.is_entregue)
        self.assertFalse(obj.saiu_para_entrega)

    def test_devolvido_nunca_marca_saiu(self):
        obj = _objeto(SAIU, _ev("BDE", "23", "Objeto entregue ao remetente", "2026-11-23T14:00:00"), POSTADO)
        self.assertTrue(obj.is_devolvido)
        self.assertFalse(obj.saiu_para_entrega)


class TestEventoSemCodigoCaiNoTexto(unittest.TestCase):
    def test_saiu_sem_codigo_pelo_texto(self):
        obj = _objeto(_sem_codigo("Objeto saiu para entrega ao destinatário", "2026-11-24T08:00:00"), POSTADO)
        self.assertTrue(obj.saiu_para_entrega)

    def test_entregue_sem_codigo_pelo_texto(self):
        obj = _objeto(_sem_codigo("Objeto entregue ao destinatário"), POSTADO)
        self.assertTrue(obj.is_entregue)

    def test_aviso_sem_codigo_pelo_texto(self):
        obj = _objeto(_sem_codigo(AVISO_PRAZO), SAIU, POSTADO)
        self.assertEqual(obj.aviso_texto, AVISO_PRAZO)
        self.assertTrue(obj.saiu_para_entrega)

    def test_codigo_desconhecido_cai_no_texto(self):
        obj = _objeto(_ev("XX", "99", "Objeto saiu para entrega ao destinatário"), POSTADO)
        self.assertTrue(obj.saiu_para_entrega)

    def test_codigo_conhecido_vence_o_texto(self):
        # Código DO/01 (transferência) manda, mesmo com texto de saída para entrega
        obj = _objeto(_ev("DO", "01", "Objeto saiu para entrega ao destinatário"), POSTADO)
        self.assertFalse(obj.saiu_para_entrega)


class TestSaiuContaEmAtrasados(unittest.TestCase):
    def test_saiu_para_entrega_atrasado_continua_em_atrasados(self):
        obj = _objeto(
            _ev("OEC", "01", "Objeto saiu para entrega ao destinatário", "2026-11-24T08:00:00"),
            _ev("PO", "01", "Objeto postado", "2026-11-10T09:00:00"),
        )
        atraso = TrackingService.verificar_atraso(
            obj, "1001", "Enviado", data_referencia=datetime(2026, 11, 25, 12, 0, 0)
        )
        self.assertIsNotNone(atraso)
        self.assertEqual(atraso.status, "em_transito")
        self.assertTrue(obj.saiu_para_entrega)


class TestFavorDesconsiderar(unittest.TestCase):
    """EST/11 desfaz o evento imediatamente anterior no tempo (o seguinte na lista), em todas as decisões."""

    EST = _ev("EST", "11", "Favor desconsiderar a informação anterior", "2026-11-24T12:00:00")
    BDE01 = _ev("BDE", "01", "Objeto entregue ao destinatário", "2026-11-23T14:00:00")
    RO = _ev("RO", "01", "Objeto em transferência - por favor aguarde", "2026-11-23T09:00:00")

    def test_bde01_seguido_de_est11_nao_e_entregue(self):
        obj = _objeto(self.EST, self.BDE01, POSTADO)
        self.assertFalse(obj.is_entregue)
        self.assertEqual(obj.status_categoria, "em_transito")

    def test_controle_sem_est11_o_mesmo_bde01_e_entregue(self):
        self.assertTrue(_objeto(self.BDE01, POSTADO).is_entregue)

    def test_oec01_seguido_de_est11_nao_e_saiu_para_entrega(self):
        obj = _objeto(self.EST, SAIU, POSTADO)
        self.assertFalse(obj.saiu_para_entrega)
        self.assertFalse(obj.is_entregue)

    def test_est11_com_transferencia_anterior_nao_muda_nada(self):
        # A transferência é a que fica desfeita (não tem marca); a postagem, mais antiga, continua valendo
        obj = _objeto(self.EST, self.RO, POSTADO)
        self.assertEqual(
            (obj.status_categoria, obj.is_postado, obj.is_retirada, obj.saiu_para_entrega, obj.is_entregue),
            ("em_transito", True, False, False, False),
        )
        self.assertTrue(obj.eventos[1].desconsiderado)

    def test_retirada_logo_antes_do_est11_e_desfeita(self):
        ldi = _ev("LDI", "01", "Objeto aguardando retirada no endereço indicado", "2026-11-23T11:00:00")
        self.assertFalse(_objeto(self.EST, ldi, POSTADO).is_retirada)

    def test_devolucao_desfeita_nao_esconde_o_cartao(self):
        bde23 = _ev("BDE", "23", "Objeto entregue ao remetente", "2026-11-23T14:00:00")
        oec09 = _ev("OEC", "09", "Objeto saiu para entrega ao remetente", "2026-11-24T10:00:00")
        obj = _objeto(self.EST, bde23, oec09, POSTADO)
        self.assertEqual(obj.status_categoria, "devolvido")
        self.assertTrue(obj.eventos[1].desconsiderado)
        self.assertFalse(TrackingService.deve_ocultar_card(obj, data_referencia=datetime(2026, 11, 24, 12, 0, 0)))


if __name__ == "__main__":
    unittest.main()
