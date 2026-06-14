"""Testes unitários da detecção de build e comando (Fase 2, lógica pura)."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from clone_build import detect_build_system, build_command, find_build


def _dir_with(*files):
    d = Path(tempfile.mkdtemp())
    for f in files:
        (d / f).parent.mkdir(parents=True, exist_ok=True)
        (d / f).write_text("")
    return d


class TestFindBuild(unittest.TestCase):
    """find_build localiza build em subdiretórios (ex.: pulumi sdk/java, golf api/)."""

    def test_root_maven(self):
        d = _dir_with("pom.xml")
        system, build_dir = find_build(d)
        self.assertEqual(system, "maven")
        self.assertEqual(build_dir, d)

    def test_subdir_maven(self):
        # golf-api: pom.xml em api/
        d = _dir_with("api/pom.xml", "README.md")
        system, build_dir = find_build(d)
        self.assertEqual(system, "maven")
        self.assertEqual(build_dir, d / "api")

    def test_subdir_gradle(self):
        # pulumi: build.gradle em sdk/java/
        d = _dir_with("sdk/java/build.gradle", "sdk/java/settings.gradle", "go.mod")
        system, build_dir = find_build(d)
        self.assertEqual(system, "gradle")
        self.assertEqual(build_dir, d / "sdk" / "java")

    def test_root_wins_over_subdir(self):
        d = _dir_with("pom.xml", "sub/build.gradle")
        system, build_dir = find_build(d)
        self.assertEqual(build_dir, d)

    def test_none_when_no_build_anywhere(self):
        d = _dir_with("README.md", "src/Foo.java")
        self.assertEqual(find_build(d), (None, None))

    def test_ignores_testdata_fixtures(self):
        # schematizer-skill: poms só em test-repo/ — não conta como build do projeto.
        d = _dir_with("test-repo/order-api/pom.xml", "README.md")
        system, build_dir = find_build(d, ignore_dirs={"test-repo", "testdata"})
        self.assertEqual((system, build_dir), (None, None))


class TestDetectBuildSystem(unittest.TestCase):
    def _dir_with(self, *files):
        return _dir_with(*files)

    def test_maven_detected(self):
        self.assertEqual(detect_build_system(self._dir_with("pom.xml")), "maven")

    def test_gradle_detected(self):
        self.assertEqual(detect_build_system(self._dir_with("build.gradle")), "gradle")
        self.assertEqual(detect_build_system(self._dir_with("build.gradle.kts")), "gradle")

    def test_android_detected(self):
        # build.gradle + AndroidManifest.xml ou plugin android → 'android'
        d = self._dir_with("build.gradle", "app/src/main/AndroidManifest.xml")
        self.assertEqual(detect_build_system(d), "android")

    def test_maven_wins_over_gradle_when_both(self):
        self.assertEqual(detect_build_system(self._dir_with("pom.xml", "build.gradle")), "maven")

    def test_none_when_no_build_file(self):
        self.assertIsNone(detect_build_system(self._dir_with("README.md")))


class TestBuildCommand(unittest.TestCase):
    def test_maven_compile(self):
        cmd = build_command("maven", has_wrapper=False)
        self.assertEqual(cmd[0], "mvn")
        self.assertIn("compile", cmd)

    def test_gradle_uses_wrapper_when_present(self):
        self.assertEqual(build_command("gradle", has_wrapper=True)[0], "./gradlew")
        self.assertEqual(build_command("gradle", has_wrapper=False)[0], "gradle")

    def test_gradle_compileJava(self):
        self.assertIn("compileJava", build_command("gradle", has_wrapper=False))

    def test_android_assembles_not_compileJava(self):
        # Android: 'assembleDebug' (precisa do SDK), não 'compileJava'.
        cmd = build_command("android", has_wrapper=True)
        self.assertIn("assembleDebug", cmd)
        self.assertNotIn("compileJava", cmd)


class TestNeedsJdk25Retry(unittest.TestCase):
    """Detecta no log quando o build falhou por exigir release/JDK 25."""

    def test_maven_release_25_triggers_retry(self):
        from clone_build import needs_jdk25_retry
        self.assertTrue(needs_jdk25_retry("error: release version 25 not supported"))

    def test_tycho_javase25_triggers_retry(self):
        from clone_build import needs_jdk25_retry
        self.assertTrue(needs_jdk25_retry("Unknown OSGi execution environment: 'JavaSE-25'"))

    def test_unrelated_failure_no_retry(self):
        from clone_build import needs_jdk25_retry
        self.assertFalse(needs_jdk25_retry("Could not find artifact org.apache.flink:...:jar:tests"))

    def test_gradle_major69_does_not_retry_with_25(self):
        # 'major version 69' = JDK 25 cedo demais p/ o Gradle → NÃO retry com 25.
        from clone_build import needs_jdk25_retry
        self.assertFalse(needs_jdk25_retry("Unsupported class file major version 69"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
