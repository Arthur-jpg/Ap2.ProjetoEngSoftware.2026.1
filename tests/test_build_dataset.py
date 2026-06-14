"""Testes unitários da lógica de montagem do dataset (Fase 5).

Requer pandas — pula automaticamente onde o pandas não está instalado
(ex.: máquina local sem deps); roda no Docker/CI. Verifica:
  - agregação McCC por classe (avg/máx) a partir do method.csv do CK;
  - McCC_avg/McCC_max distintos de WMC (PLANO.md);
  - join de bugs deixa classes SEM bug como NaN (ausente != 0);
  - uma linha por classe.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import pandas as pd
    _HAS_PANDAS = True
except ImportError:
    _HAS_PANDAS = False


@unittest.skipUnless(_HAS_PANDAS, "pandas indisponível (roda no Docker)")
class TestMcccAggregation(unittest.TestCase):
    def test_avg_and_max_per_class(self):
        from build_dataset import mccc_per_class
        method_df = pd.DataFrame({
            "class": ["com.x.A", "com.x.A", "com.x.A", "com.x.B"],
            "McCC": [1, 3, 5, 4],
        })
        agg = mccc_per_class(method_df).set_index("class")
        self.assertEqual(agg.loc["com.x.A", "McCC_max"], 5)
        self.assertAlmostEqual(agg.loc["com.x.A", "McCC_avg"], 3.0)
        self.assertEqual(agg.loc["com.x.B", "McCC_avg"], 4.0)
        self.assertEqual(agg.loc["com.x.B", "McCC_max"], 4.0)

    def test_mccc_differs_from_wmc(self):
        # WMC (classe) = soma = 9; McCC_avg = 3, McCC_max = 5 → distintos.
        from build_dataset import mccc_per_class
        method_df = pd.DataFrame({
            "class": ["com.x.A"] * 3, "McCC": [1, 3, 5],
        })
        agg = mccc_per_class(method_df).iloc[0]
        wmc = method_df["McCC"].sum()
        self.assertNotEqual(agg["McCC_avg"], wmc)
        self.assertNotEqual(agg["McCC_max"], wmc)


@unittest.skipUnless(_HAS_PANDAS, "pandas indisponível (roda no Docker)")
class TestBugJoin(unittest.TestCase):
    def test_analyzed_repo_missing_bug_is_zero(self):
        # Repo analisado pelo SpotBugs: classe sem achado → 0 (foi analisada).
        from build_dataset import join_bugs
        classes = pd.DataFrame({"class": ["com.x.A", "com.x.B"], "CBO": [3, 7]})
        out = join_bugs(classes, {"com.x.A": 2}, analyzed=True).set_index("class")
        self.assertEqual(out.loc["com.x.A", "Number_of_bugs"], 2)
        self.assertEqual(out.loc["com.x.B", "Number_of_bugs"], 0)  # analisada, 0 bugs

    def test_not_analyzed_repo_is_nan(self):
        # Repo NÃO analisado (build falhou): tudo NaN (ausência != zero).
        from build_dataset import join_bugs
        classes = pd.DataFrame({"class": ["com.x.A", "com.x.B"], "CBO": [3, 7]})
        out = join_bugs(classes, {}, analyzed=False).set_index("class")
        self.assertTrue(pd.isna(out.loc["com.x.A", "Number_of_bugs"]))
        self.assertTrue(pd.isna(out.loc["com.x.B", "Number_of_bugs"]))

    def test_one_row_per_class_preserved(self):
        from build_dataset import join_bugs
        classes = pd.DataFrame({"class": ["A", "B", "C"], "CBO": [1, 2, 3]})
        out = join_bugs(classes, {"A": 1}, analyzed=True)
        self.assertEqual(len(out), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
