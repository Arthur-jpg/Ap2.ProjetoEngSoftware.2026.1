"""Fase 4 — contagem de bugs por classe via SpotBugs."""
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

from config import REPOS_JSON, RAW_DIR, SPOTBUGS_HOME
from utils import log, repo_dir_name


def _find_classes_dir(repo_dir: Path) -> Path | None:
    """Localiza o diretório com os .class compilados."""
    candidates = [
        repo_dir / "target" / "classes",                      # Maven
        repo_dir / "build" / "classes" / "java" / "main",    # Gradle (padrão)
        repo_dir / "build" / "classes" / "kotlin" / "main",
        repo_dir / "build" / "classes",
    ]
    for c in candidates:
        if c.exists() and any(c.rglob("*.class")):
            return c
    # Busca genérica por qualquer pasta com .class
    for p in repo_dir.rglob("*.class"):
        return p.parent
    return None


def _run_spotbugs(repo: dict) -> bool:
    clone_dir = RAW_DIR / repo_dir_name(repo["owner"], repo["repo"])
    out_xml   = clone_dir / "spotbugs.xml"
    out_csv   = clone_dir / "bugs_por_classe.csv"

    if out_xml.exists() and out_csv.exists():
        log.info("  SpotBugs já executado: %s", clone_dir.name)
        return True

    if not repo.get("build_ok"):
        log.info("  build_ok=false — SpotBugs pulado para %s", clone_dir.name)
        # Gera CSV vazio para que a fase 5 não quebre
        pd.DataFrame(columns=["class", "bug_count"]).to_csv(out_csv, index=False)
        return False

    classes_dir = _find_classes_dir(clone_dir)
    if not classes_dir:
        log.warning("  Nenhum .class encontrado em %s", clone_dir.name)
        pd.DataFrame(columns=["class", "bug_count"]).to_csv(out_csv, index=False)
        return False

    spotbugs_jar = SPOTBUGS_HOME / "lib" / "spotbugs.jar"
    if not spotbugs_jar.exists():
        raise FileNotFoundError(f"SpotBugs não encontrado em {spotbugs_jar}")

    log.info("  Rodando SpotBugs em %s...", clone_dir.name)
    cmd = [
        "java", "-jar", str(spotbugs_jar),
        "-textui",
        "-xml:withMessages",
        "-output", str(out_xml),
        str(classes_dir),
    ]
    log.info("  Comando: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode not in (0, 1):  # exit 1 = bugs encontrados (normal)
        log.error("  SpotBugs falhou (exit %d):\n%s",
                  result.returncode, (result.stderr or result.stdout)[-500:])
        pd.DataFrame(columns=["class", "bug_count"]).to_csv(out_csv, index=False)
        return False

    if not out_xml.exists():
        log.error("  SpotBugs não gerou XML")
        pd.DataFrame(columns=["class", "bug_count"]).to_csv(out_csv, index=False)
        return False

    _parse_xml(out_xml, out_csv)
    return True


def _parse_xml(xml_path: Path, csv_path: Path):
    """Conta BugInstance por classe e salva CSV."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as exc:
        log.error("  Erro ao parsear XML: %s", exc)
        pd.DataFrame(columns=["class", "bug_count"]).to_csv(csv_path, index=False)
        return

    counts: dict[str, int] = {}
    for bug in root.iter("BugInstance"):
        cls_el = bug.find("Class")
        if cls_el is None:
            cls_el = bug.find("SourceLine")
        if cls_el is not None:
            cls_name = cls_el.get("classname", "")
            # Remove sufixo de classe interna (ex: Foo$Bar → Foo)
            cls_name = cls_name.split("$")[0]
            if cls_name:
                counts[cls_name] = counts.get(cls_name, 0) + 1

    total_xml = len(list(root.iter("BugInstance")))
    total_csv = sum(counts.values())
    log.info("  SpotBugs: %d BugInstances no XML, %d distribuídos por %d classes",
             total_xml, total_csv, len(counts))

    df = pd.DataFrame(
        [{"class": k, "bug_count": v} for k, v in counts.items()]
    )
    df.to_csv(csv_path, index=False)


def run_fase4():
    if not REPOS_JSON.exists():
        raise FileNotFoundError(
            f"{REPOS_JSON} não encontrado — rode as fases anteriores primeiro."
        )

    repos    = json.loads(REPOS_JSON.read_text())
    ok_count = 0

    for repo in repos:
        log.info("[Fase 4] %s", repo["full_name"])
        success = _run_spotbugs(repo)
        repo["spotbugs_ok"] = success
        if success:
            ok_count += 1

    REPOS_JSON.write_text(json.dumps(repos, indent=2, ensure_ascii=False))
    log.info("Fase 4 concluída — %d/%d repos com SpotBugs OK", ok_count, len(repos))


if __name__ == "__main__":
    run_fase4()
