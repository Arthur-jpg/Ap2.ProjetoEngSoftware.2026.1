"""Testes da curadoria da Fase 1: exclusão de Android + includes fixos.

Garante seleção reprodutível: re-rodar a Fase 1 sempre exclui repos Android e
sempre inclui os repos fixados (ex.: pulumi/pulumi-java).
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import config
from github_discovery import is_android_repo, apply_curation, select_final


class TestIsAndroidRepo(unittest.TestCase):
    def test_android_manifest_marks_android(self):
        self.assertTrue(is_android_repo(["app/src/main/AndroidManifest.xml", "build.gradle"]))

    def test_android_gradle_plugin_marks_android(self):
        self.assertTrue(is_android_repo(["build.gradle"], gradle_text="apply plugin: 'com.android.application'"))

    def test_plain_java_not_android(self):
        self.assertFalse(is_android_repo(["pom.xml", "src/main/java/Foo.java"]))


class TestApplyCuration(unittest.TestCase):
    def test_excludes_listed_repos(self):
        repos = {
            "JackZho/MusicPlayer": {"full_name": "JackZho/MusicPlayer"},
            "x/keep": {"full_name": "x/keep"},
        }
        out = apply_curation(repos, exclude={"JackZho/MusicPlayer"}, include=[])
        self.assertNotIn("JackZho/MusicPlayer", out)
        self.assertIn("x/keep", out)

    def test_pinned_includes_added_if_missing(self):
        repos = {"x/keep": {"full_name": "x/keep"}}
        out = apply_curation(repos, exclude=set(),
                             include=[{"full_name": "pulumi/pulumi-java", "owner": "pulumi",
                                       "repo": "pulumi-java", "signals": ["co_authored_by"]}])
        self.assertIn("pulumi/pulumi-java", out)

    def test_pinned_include_not_duplicated(self):
        repos = {"pulumi/pulumi-java": {"full_name": "pulumi/pulumi-java", "signals": ["x"]}}
        out = apply_curation(repos, exclude=set(),
                             include=[{"full_name": "pulumi/pulumi-java", "owner": "pulumi",
                                       "repo": "pulumi-java", "signals": ["co_authored_by"]}])
        self.assertEqual(len([k for k in out if k == "pulumi/pulumi-java"]), 1)

    def test_config_has_curation_constants(self):
        self.assertIn("JackZho/android-library-system", config.EXCLUDE_REPOS)
        self.assertIn("JackZho/MusicPlayer", config.EXCLUDE_REPOS)
        # repos "Java" fracos também excluídos
        self.assertIn("adamzwasserman/honest-code-traces", config.EXCLUDE_REPOS)
        names = [r["full_name"] for r in config.PINNED_REPOS]
        self.assertIn("pulumi/pulumi-java", names)
        self.assertIn("yksi7417/cross_asset_ems", names)


class TestSelectFinal(unittest.TestCase):
    def _r(self, name, stars, pinned=False):
        return {"full_name": name, "stars": stars, "pinned": pinned}

    def test_pinned_always_kept_even_if_low_stars(self):
        repos = [self._r(f"hi/{i}", 100 + i) for i in range(10)]
        repos.append(self._r("pin/low", 0, pinned=True))
        out = select_final(repos, target=10)
        names = [r["full_name"] for r in out]
        self.assertIn("pin/low", names)
        self.assertEqual(len(out), 10)

    def test_fills_rest_by_stars(self):
        repos = [self._r("a", 5), self._r("b", 50), self._r("c", 1)]
        out = select_final(repos, target=2)
        names = [r["full_name"] for r in out]
        self.assertEqual(names, ["b", "a"])  # top-2 por estrelas

    def test_sorted_by_stars_desc(self):
        repos = [self._r("a", 5), self._r("p", 0, pinned=True), self._r("b", 50)]
        out = select_final(repos, target=3)
        stars = [r["stars"] for r in out]
        self.assertEqual(stars, sorted(stars, reverse=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
