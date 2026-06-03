"""Validação da Fase 1 — data/repos.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPOS_JSON = ROOT / "data" / "repos.json"

REQUIRED_FIELDS = {"full_name", "owner", "repo", "language", "stars", "default_branch", "signals"}

erros = []


def falha(msg: str):
    erros.append(msg)
    print(f"[FALHA] {msg}")


def ok(msg: str):
    print(f"[OK]    {msg}")


print("=== Teste Fase 1: repos.json ===\n")

# 1. Arquivo existe
if not REPOS_JSON.exists():
    falha(f"Arquivo não encontrado: {REPOS_JSON}")
    print("\nFase 1: FALHOU (arquivo ausente — rode a Fase 1 antes)")
    sys.exit(1)

repos = json.loads(REPOS_JSON.read_text())

# 2. Exatamente 10 entradas
if len(repos) == 10:
    ok(f"10 repos encontrados")
else:
    falha(f"Esperado 10 repos, encontrado {len(repos)}")

# 3. Todos Java
non_java = [r["full_name"] for r in repos if r.get("language") != "Java"]
if not non_java:
    ok("Todos os repos são Java")
else:
    falha(f"Repos não-Java encontrados: {non_java}")

# 4. Todos com sinal do Claude
no_signal = [r["full_name"] for r in repos if not r.get("signals")]
if not no_signal:
    ok("Todos têm sinal de contribuição do Claude")
else:
    falha(f"Repos sem sinal do Claude: {no_signal}")

# 5. Ordenados por estrelas (desc)
stars = [r["stars"] for r in repos]
if stars == sorted(stars, reverse=True):
    ok(f"Ordenados por estrelas (desc): {stars}")
else:
    falha(f"Repos não estão ordenados por estrelas. Ordem atual: {stars}")

# 6. Campos obrigatórios presentes
for r in repos:
    missing = REQUIRED_FIELDS - r.keys()
    if missing:
        falha(f"{r.get('full_name', '?')} — campos ausentes: {missing}")

if not erros:
    ok("Todos os campos obrigatórios presentes")

print()
if not erros:
    print("Fase 1: PASSOU")
    sys.exit(0)
else:
    print(f"Fase 1: FALHOU ({len(erros)} erro(s))")
    sys.exit(1)
