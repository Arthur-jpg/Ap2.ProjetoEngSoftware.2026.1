"""Testes unitários do schema de colunas do CK (config.py).

Garante que o mapa de colunas reflete a saída REAL do CK 0.7.0 e não inventa
colunas que o CK não produz (CLOC, WarningMajor, RuleViolations_*).

Cabeçalhos verbatim do CK 0.7.0 (ResultWriter.java):
  class.csv:  file, class, type, cbo, cboModified, fanin, fanout, wmc, dit,
              noc, rfc, lcom, lcom*, tcc, lcc, totalMethodsQty, ...,
              publicMethodsQty, ..., loc, ...
  method.csv: file, class, method, constructor, line, ..., wmc, ..., loc, ...
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import config


# Colunas que o CK realmente emite (chaves do CLASS_COLUMNS devem ser um
# subconjunto destas).
CK_CLASS_HEADERS = {
    "file", "class", "type", "cbo", "cboModified", "fanin", "fanout", "wmc",
    "dit", "noc", "rfc", "lcom", "lcom*", "tcc", "lcc", "totalMethodsQty",
    "publicMethodsQty", "loc",
}

# Colunas que o SourceMeter produzia mas o CK NÃO — não podem aparecer no mapa.
FORBIDDEN = {
    "CLOC", "WarningMajor", "RuleViolations_Design", "RuleViolations_Coupling",
    "RuleViolations_Documentation", "RuleViolations_Size", "LongName", "Path",
}


class TestClassColumns(unittest.TestCase):
    def test_keys_are_real_ck_headers(self):
        for ck_col in config.CLASS_COLUMNS:
            self.assertIn(
                ck_col, CK_CLASS_HEADERS,
                f"'{ck_col}' não é um cabeçalho real do CK 0.7.0",
            )

    def test_no_sourcemeter_only_columns(self):
        for dest in config.CLASS_COLUMNS.values():
            self.assertNotIn(
                dest, FORBIDDEN,
                f"coluna '{dest}' é do SourceMeter e o CK não a produz — remover",
            )
        for src in config.CLASS_COLUMNS:
            self.assertNotIn(src, FORBIDDEN)

    def test_core_ck_metrics_present(self):
        dest = set(config.CLASS_COLUMNS.values())
        for required in ("CBO", "DIT", "RFC", "WMC", "LCOM", "NOC"):
            self.assertIn(required, dest, f"métrica CK essencial ausente: {required}")

    def test_lcom_star_mapped_honestly(self):
        # lcom* (Henderson-Sellers) deve existir e ser rotulado como LCOM_norm,
        # nunca como 'LCOM5'.
        self.assertEqual(config.CLASS_COLUMNS.get("lcom*"), "LCOM_norm")
        self.assertNotIn("LCOM5", config.CLASS_COLUMNS.values())


class TestMethodColumns(unittest.TestCase):
    def test_method_has_wmc_for_mccc(self):
        # McCC por método vem do 'wmc' do method.csv.
        self.assertIn("wmc", config.METHOD_COLUMNS)

    def test_method_class_join_key_is_class(self):
        # O join método→classe usa a coluna 'class' do CK.
        self.assertEqual(config.METHOD_CLASS_COLUMN, "class")


if __name__ == "__main__":
    unittest.main(verbosity=2)
