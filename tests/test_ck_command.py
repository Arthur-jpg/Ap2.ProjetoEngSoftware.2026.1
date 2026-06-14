"""Testes unitários da construção do comando do CK (Fase 3, lógica pura).

Invocação do CK 0.7.0 (ResultWriter/README):
  java -jar <ck.jar> <project_dir> <useJars> <maxFiles> <varsAndFields> <out_dir>
Usamos: useJars=false, maxFiles=0 (automático), varsAndFields=false.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from run_sourcemeter import ck_command


class TestCkCommand(unittest.TestCase):
    def test_command_shape(self):
        cmd = ck_command(jar="/opt/ck/ck.jar", project_dir="/p", out_dir="/o")
        self.assertEqual(cmd[:3], ["java", "-jar", "/opt/ck/ck.jar"])
        # project_dir vem logo após o jar
        self.assertEqual(cmd[3], "/p")
        # out_dir é o último argumento
        self.assertEqual(cmd[-1], "/o")

    def test_flags_useJars_false_and_vars_false(self):
        cmd = ck_command(jar="j", project_dir="p", out_dir="o")
        # argumentos posicionais: jar dir useJars maxFiles varsAndFields out
        self.assertEqual(cmd[4], "false")  # useJars
        self.assertEqual(cmd[5], "0")      # maxFiles automático
        self.assertEqual(cmd[6], "false")  # variables and fields

    def test_all_args_are_strings(self):
        cmd = ck_command(jar="j", project_dir="p", out_dir="o")
        self.assertTrue(all(isinstance(a, str) for a in cmd))


if __name__ == "__main__":
    unittest.main(verbosity=2)
