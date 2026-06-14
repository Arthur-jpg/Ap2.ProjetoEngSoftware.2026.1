"""Testes unitários do comando do SpotBugs (Fase 4, lógica pura)."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from run_spotbugs import spotbugs_command, find_classes_dirs


def _mk(*rel_class_files):
    d = Path(tempfile.mkdtemp())
    for rel in rel_class_files:
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_bytes(b"\xca\xfe\xba\xbe")  # magic de .class
    return d


class TestFindClassesDirs(unittest.TestCase):
    def test_maven_root_classes_dir(self):
        d = _mk("target/classes/com/foo/A.class", "target/classes/com/foo/bar/B.class")
        dirs = find_classes_dirs(d)
        # Retorna o RAIZ target/classes (não com/foo), p/ cobrir todos os pacotes.
        self.assertIn(d / "target" / "classes", dirs)

    def test_gradle_root_classes_dir(self):
        d = _mk("build/classes/java/main/p/A.class")
        self.assertIn(d / "build" / "classes" / "java" / "main", find_classes_dirs(d))

    def test_multimodule_returns_all_modules(self):
        d = _mk(
            "modA/target/classes/a/A.class",
            "modB/target/classes/b/B.class",
        )
        dirs = find_classes_dirs(d)
        self.assertIn(d / "modA" / "target" / "classes", dirs)
        self.assertIn(d / "modB" / "target" / "classes", dirs)
        self.assertEqual(len(dirs), 2)

    def test_does_not_descend_into_packages(self):
        d = _mk("target/classes/com/x/Deep.class")
        dirs = find_classes_dirs(d)
        # Nenhum diretório retornado deve ser um subpacote (com/x).
        for dd in dirs:
            self.assertFalse(dd.name in ("com", "x"))

    def test_empty_when_no_classes(self):
        d = _mk("src/Foo.java")
        self.assertEqual(find_classes_dirs(d), [])


class TestSpotbugsCommand(unittest.TestCase):
    def test_command_shape(self):
        cmd = spotbugs_command(jar="/sb/spotbugs.jar", classes_dir="/c", out_xml="/o.xml")
        self.assertEqual(cmd[:3], ["java", "-jar", "/sb/spotbugs.jar"])
        self.assertIn("-textui", cmd)
        self.assertIn("-xml:withMessages", cmd)
        # saída e diretório de classes presentes
        self.assertIn("/o.xml", cmd)
        self.assertEqual(cmd[-1], "/c")  # classes dir é o alvo final

    def test_output_flag_precedes_path(self):
        cmd = spotbugs_command(jar="j", classes_dir="c", out_xml="o.xml")
        i = cmd.index("-output")
        self.assertEqual(cmd[i + 1], "o.xml")


if __name__ == "__main__":
    unittest.main(verbosity=2)
