"""Escala única de urgência do atraso: painel (selo) e página de Atrasados usam a mesma regra."""

import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
ARQUIVOS_DIR = PROJECT_ROOT / "Arquivos"
if str(ARQUIVOS_DIR) not in sys.path:
    sys.path.insert(0, str(ARQUIVOS_DIR))

from correios.cards import selo_status, urgencia_atraso  # noqa: E402


class TestUrgenciaAtraso(unittest.TestCase):
    def test_quatro_seis_e_oito_dias_geram_as_tres_classes(self):
        self.assertEqual(urgencia_atraso(4), ("urgencia-baixa", "Atenção"))
        self.assertEqual(urgencia_atraso(6), ("urgencia-media", "Alto"))
        self.assertEqual(urgencia_atraso(8), ("urgencia-alta", "Crítico"))

    def test_limites_de_cada_faixa(self):
        self.assertEqual(urgencia_atraso(5)[0], "urgencia-media")
        self.assertEqual(urgencia_atraso(7)[0], "urgencia-alta")
        self.assertEqual(urgencia_atraso(3)[0], "urgencia-baixa")

    def test_selo_do_painel_segue_a_mesma_escala(self):
        cores = {d: selo_status("em_transito", atrasado=True, dias_atraso=d)[1] for d in (4, 6, 8)}
        self.assertEqual(cores, {4: "badge-yellow", 6: "badge-orange", 8: "badge-red"})

    def test_selo_mantem_o_texto_com_os_dias(self):
        texto, _ = selo_status("em_transito", atrasado=True, dias_atraso=4)
        self.assertEqual(texto, "Atrasado · 4 dias · Atenção")


if __name__ == "__main__":
    unittest.main()
