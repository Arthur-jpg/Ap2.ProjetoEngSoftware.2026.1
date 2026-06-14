"""Fase 3 — extração de métricas OO com o CK (Aniche).

Nome do arquivo mantido como `run_sourcemeter.py` por compatibilidade com o
orquestrador (`main.py`), mas o motor de métricas é o **CK 0.7.0** — não o
SourceMeter. O CK roda sobre o FONTE Java (não precisa compilar) e gera
`class.csv` e `method.csv` por repo em `data/raw/<repo>/ck/`.

Referências: Chidamber & Kemerer 1994 (cbo/dit/rfc/wmc/lcom/noc);
Henderson-Sellers 1996 (lcom*); McCabe 1976 (wmc por método).
Ver docs/decisions/03-metricas-ck.md.
"""
import json
import subprocess
from pathlib import Path

from config import REPOS_JSON, RAW_DIR, CK_JAR
from utils import log, repo_dir_name


def ck_command(jar: str, project_dir: str, out_dir: str) -> list[str]:
    """Monta o comando do CK.

    CK 0.7.0: java -jar <jar> <dir> <useJars> <maxFiles> <varsAndFields> <out>
    useJars=false, maxFiles=0 (automático), varsAndFields=false.
    Todos os argumentos são strings (subprocess).
    """
    return [
        "java", "-jar", str(jar),
        str(project_dir),
        "false",   # use jars
        "0",       # max files per partition (0 = automático)
        "false",   # variables and fields metrics
        str(out_dir),
    ]


def _run_ck(repo: dict) -> bool:
    clone_dir = RAW_DIR / repo_dir_name(repo["owner"], repo["repo"])
    out_dir = clone_dir / "ck"

    if (out_dir / "class.csv").exists() and (out_dir / "method.csv").exists():
        log.info("  CK já executado: %s", clone_dir.name)
        return True

    if not CK_JAR.exists():
        raise FileNotFoundError(f"CK jar não encontrado em {CK_JAR} (defina CK_JAR).")

    out_dir.mkdir(parents=True, exist_ok=True)
    # O CK usa o argumento <out> como PREFIXO; passar 'ck/' garante ck/class.csv etc.
    prefix = str(out_dir) + "/"
    cmd = ck_command(jar=str(CK_JAR), project_dir=str(clone_dir), out_dir=prefix)
    log.info("  Comando: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    if result.returncode != 0:
        log.error("  CK falhou (exit %d):\n%s",
                  result.returncode, (result.stderr or result.stdout)[-500:])
        return False
    if not (out_dir / "class.csv").exists():
        log.error("  CK não gerou class.csv")
        return False

    log.info("  CK OK: %s", clone_dir.name)
    return True


def run_fase3():
    if not REPOS_JSON.exists():
        raise FileNotFoundError(f"{REPOS_JSON} não encontrado — rode as fases anteriores.")

    repos = json.loads(REPOS_JSON.read_text())
    ok_count = 0
    for repo in repos:
        log.info("[Fase 3] %s", repo["full_name"])
        success = _run_ck(repo)
        repo["ck_ok"] = success
        ok_count += int(success)

    REPOS_JSON.write_text(json.dumps(repos, indent=2, ensure_ascii=False))
    log.info("Fase 3 concluída — %d/%d repos com CK OK", ok_count, len(repos))


if __name__ == "__main__":
    run_fase3()
