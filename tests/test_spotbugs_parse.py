"""Testes unitários do parsing de bugs do SpotBugs (Fase 4, lógica pura).

Critério de aceite da Fase 4 (PLANO.md): a soma das contagens por classe deve
ser igual ao total de <BugInstance> no XML.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from spotbugs_parse import count_bugs_by_class


SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<BugCollection version="4.8.6">
  <BugInstance type="NP_NULL" priority="1" rank="9">
    <Class classname="com.example.Foo"/>
  </BugInstance>
  <BugInstance type="DM_DEFAULT" priority="2" rank="14">
    <Class classname="com.example.Foo"/>
  </BugInstance>
  <BugInstance type="EI_EXPOSE_REP" priority="2" rank="18">
    <Class classname="com.example.Bar"/>
  </BugInstance>
  <BugInstance type="SE_BAD_FIELD" priority="2" rank="18">
    <Class classname="com.example.Bar$Inner"/>
  </BugInstance>
</BugCollection>
"""


class TestCountBugsByClass(unittest.TestCase):
    def setUp(self):
        self.counts = count_bugs_by_class(SAMPLE_XML)

    def test_sum_equals_total_bug_instances(self):
        # Critério de aceite: soma == nº de <BugInstance> (4 no exemplo).
        self.assertEqual(sum(self.counts.values()), 4)

    def test_counts_per_class(self):
        self.assertEqual(self.counts["com.example.Foo"], 2)

    def test_inner_class_collapsed_to_outer(self):
        # Bar$Inner deve contar para com.example.Bar (normalização $).
        # Bar tem 1 bug direto + 1 do Inner = 2.
        self.assertEqual(self.counts["com.example.Bar"], 2)
        self.assertNotIn("com.example.Bar$Inner", self.counts)

    def test_empty_xml_returns_empty(self):
        empty = count_bugs_by_class(
            '<?xml version="1.0"?><BugCollection></BugCollection>'
        )
        self.assertEqual(empty, {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
