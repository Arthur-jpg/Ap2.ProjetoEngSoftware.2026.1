"""Fase 4 — contagem de bugs por classe via SpotBugs.

Roda o SpotBugs sobre o bytecode compilado (precisa de build_ok=true) e grava
`spotbugs.xml` por repo. A contagem por classe é feita na Fase 5 a partir do
XML (spotbugs_parse.count_bugs_by_class). Repos sem build NÃO geram XML e, na
Fase 5, ficam com Number_of_bugs = NaN (ausente != zero).
"""
import json
import subprocess
from pathlib import Path

from config import REPOS_JSON, RAW_DIR, SPOTBUGS_HOME
from utils import log, repo_dir_name


def spotbugs_command(jar: str, classes_dir, out_xml: str) -> list[str]:
    """Monta o comando do SpotBugs em modo textui com saída XML.

    `classes_dir` pode ser um caminho único (str/Path) ou uma lista de
    diretórios (multi-módulo) — todos são passados como alvos.
    """
    if isinstance(classes_dir, (str, Path)):
        targets = [str(classes_dir)]
    else:
        targets = [str(c) for c in classes_dir]
    return [
        "java", "-jar", str(jar),
        "-textui",
        "-xml:withMessages",
        "-output", str(out_xml),
        *targets,
    ]


def find_classes_dirs(repo_dir: Path) -> list[Path]:
    """Localiza TODOS os diretórios-raiz de bytecode (.class) do repo.

    Retorna os raízes de saída de compilação (Maven `target/classes`, Gradle
    `build/classes/java/main`) de TODOS os módulos — não desce para subpacotes.
    Multi-módulo retorna vários. Isso garante que o SpotBugs analise todas as
    classes, não só um subpacote (bug da versão anterior que subcontava bugs).
    """
    roots: list[Path] = []
    # Maven: qualquer .../target/classes com .class dentro.
    for p in repo_dir.rglob("target/classes"):
        if p.is_dir() and any(p.rglob("*.class")):
            roots.append(p)
    # Gradle: qualquer .../build/classes/java/main com .class dentro.
    for p in repo_dir.rglob("build/classes/java/main"):
        if p.is_dir() and any(p.rglob("*.class")):
            roots.append(p)
    return roots


def _run_spotbugs(repo: dict) -> bool:
    clone_dir = RAW_DIR / repo_dir_name(repo["owner"], repo["repo"])
    out_xml = clone_dir / "spotbugs.xml"

    if out_xml.exists():
        log.info("  SpotBugs já executado: %s", clone_dir.name)
        return True
    if not repo.get("build_ok"):
        log.info("  build_ok=false — SpotBugs pulado (bugs ficarão NaN): %s", clone_dir.name)
        return False

    classes_dirs = find_classes_dirs(clone_dir)
    if not classes_dirs:
        log.warning("  nenhum .class encontrado em %s", clone_dir.name)
        return False
    log.info("  %d diretório(s) de classes encontrados", len(classes_dirs))

    spotbugs_jar = SPOTBUGS_HOME / "lib" / "spotbugs.jar"
    if not spotbugs_jar.exists():
        raise FileNotFoundError(f"SpotBugs não encontrado em {spotbugs_jar}")

    cmd = spotbugs_command(str(spotbugs_jar), classes_dirs, str(out_xml))
    log.info("  Comando: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    if result.returncode not in (0, 1):  # exit 1 = bugs encontrados (normal)
        log.error("  SpotBugs falhou (exit %d):\n%s",
                  result.returncode, (result.stderr or result.stdout)[-500:])
        return False
    if not out_xml.exists():
        log.error("  SpotBugs não gerou XML")
        return False

    log.info("  SpotBugs OK: %s", clone_dir.name)
    return True


def run_fase4():
    if not REPOS_JSON.exists():
        raise FileNotFoundError(f"{REPOS_JSON} não encontrado — rode as fases anteriores.")

    repos = json.loads(REPOS_JSON.read_text())
    ok_count = 0
    for repo in repos:
        log.info("[Fase 4] %s", repo["full_name"])
        success = _run_spotbugs(repo)
        repo["spotbugs_ok"] = success
        ok_count += int(success)

    REPOS_JSON.write_text(json.dumps(repos, indent=2, ensure_ascii=False))
    log.info("Fase 4 concluída — %d/%d repos com SpotBugs OK", ok_count, len(repos))


if __name__ == "__main__":
    run_fase4()
