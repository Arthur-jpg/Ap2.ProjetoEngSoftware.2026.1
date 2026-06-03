"""Validação da Fase 2 — clones e builds."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPOS_JSON = ROOT / "data" / "repos.json"
RAW_DIR = ROOT / "data" / "raw"

erros = []


def falha(msg):
    erros.append(msg)
    print(f"[FALHA] {msg}")


def ok(msg):
    print(f"[OK]    {msg}")


print("=== Teste Fase 2: clone & build ===\n")

if not REPOS_JSON.exists():
    falha("repos.json não encontrado")
    sys.exit(1)

repos = json.loads(REPOS_JSON.read_text())

# 1. Campos novos presentes
for r in repos:
    for campo in ("claude_confirmed", "build_ok"):
        if campo not in r:
            falha(f"{r['full_name']} — campo '{campo}' ausente no repos.json")

ok("Campos claude_confirmed e build_ok presentes em todos os repos")

# 2. Diretórios clonados existem
for r in repos:
    dir_name = f"{r['owner']}__{r['repo']}"
    clone_dir = RAW_DIR / dir_name
    if not clone_dir.exists():
        falha(f"Diretório de clone não encontrado: {clone_dir}")
    else:
        ok(f"Clone OK: {dir_name}")

# 3. Resumo de confirmação e builds
confirmed = [r for r in repos if r.get("claude_confirmed")]
built = [r for r in repos if r.get("build_ok")]

print(f"\nResumo:")
print(f"  Claude confirmado: {len(confirmed)}/{len(repos)}")
print(f"  Build OK:          {len(built)}/{len(repos)}")

for r in repos:
    status = []
    status.append("claude=OK" if r.get("claude_confirmed") else "claude=FALHOU")
    status.append("build=OK" if r.get("build_ok") else "build=FALHOU")
    print(f"  {r['full_name']:<45} {' | '.join(status)}")

print()
if not erros:
    print("Fase 2: PASSOU")
    sys.exit(0)
else:
    print(f"Fase 2: FALHOU ({len(erros)} erro(s))")
    sys.exit(1)
