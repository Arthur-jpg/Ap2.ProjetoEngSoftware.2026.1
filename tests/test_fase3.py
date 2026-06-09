"""Validação da Fase 3 — saídas do SourceMeter."""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
REPOS_JSON = ROOT / "data" / "repos.json"

COLUNAS_CLASS = {"LOC", "CLOC", "WMC", "CBO", "RFC", "DIT", "LCOM5", "NM", "NPM"}

erros = []


def falha(msg):
    erros.append(msg)
    print(f"[FALHA] {msg}")


def ok(msg):
    print(f"[OK]    {msg}")


print("=== Teste Fase 3: SourceMeter ===\n")

if not REPOS_JSON.exists():
    falha("repos.json não encontrado")
    sys.exit(1)

repos = json.loads(REPOS_JSON.read_text())
sm_ok = [r for r in repos if r.get("sourcemeter_ok")]

print(f"SourceMeter OK: {len(sm_ok)}/{len(repos)} repos\n")

for r in sm_ok:
    nome = r["full_name"]

    # Class.csv
    class_csv = r.get("class_csv")
    if not class_csv or not Path(class_csv).exists():
        falha(f"{nome} — Class.csv não encontrado")
        continue

    df = pd.read_csv(class_csv)
    faltando = COLUNAS_CLASS - set(df.columns)
    if faltando:
        falha(f"{nome} — colunas ausentes no Class.csv: {faltando}")
    else:
        ok(f"{nome} — Class.csv OK ({len(df)} classes, colunas-alvo presentes)")

    # Method.csv
    method_csv = r.get("method_csv")
    if not method_csv or not Path(method_csv).exists():
        falha(f"{nome} — Method.csv não encontrado")
    elif "McCC" not in pd.read_csv(method_csv).columns:
        falha(f"{nome} — coluna McCC ausente no Method.csv")
    else:
        ok(f"{nome} — Method.csv OK (McCC presente)")

print()
if not erros:
    print("Fase 3: PASSOU")
    sys.exit(0)
else:
    print(f"Fase 3: FALHOU ({len(erros)} erro(s))")
    sys.exit(1)
