"""Teste de fumaça: todo módulo de src/ importa sem erro.

Pega faltas de import (ex.: usar `Path` num type hint sem
`from pathlib import Path`), que só aparecem ao avaliar o módulo — exatamente
o NameError que quebrou a Fase 2 no Docker. pandas é opcional aqui: módulos
que dependem dele são pulados se não estiver instalado.
"""
import importlib
import sys
import unittest
from pathlib import Path

SRC = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC))

# Módulos sem dependências externas pesadas — devem importar em qualquer ambiente.
CORE_MODULES = ["config", "utils", "clone_build", "spotbugs_parse"]
# Dependem de libs externas (requests/pandas) — pulam se ausentes.
OPTIONAL_MODULES = {
    "github_discovery": "requests",
    "run_sourcemeter": None,
    "run_spotbugs": None,
    "build_dataset": "pandas",
    "main": None,
}


class TestModulesImport(unittest.TestCase):
    def test_core_modules_import(self):
        for name in CORE_MODULES:
            with self.subTest(module=name):
                importlib.import_module(name)

    def test_optional_modules_import_when_deps_present(self):
        for name, dep in OPTIONAL_MODULES.items():
            if dep is not None:
                try:
                    importlib.import_module(dep)
                except ImportError:
                    continue  # dependência ausente neste ambiente
            with self.subTest(module=name):
                importlib.import_module(name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
