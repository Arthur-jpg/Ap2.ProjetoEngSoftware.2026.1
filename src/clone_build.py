import json
import os
import re
import subprocess
from pathlib import Path

from config import REPOS_JSON, RAW_DIR, CLAUDE_COAUTHORED_RE, CLAUDE_AUTHOR_EMAIL_RE, CLAUDE_AUTHOR_NAME_RE
from utils import log, repo_dir_name

# Caminhos dos dois JDKs na imagem (ver Dockerfile). JDK 21 é o padrão
# (compatível com todos os wrappers Gradle e Tycho); JDK 25 só para repos que
# compilam release 25.
JAVA21_HOME = os.environ.get("JAVA21_HOME", "/opt/java/openjdk")
JAVA25_HOME = os.environ.get("JAVA25_HOME", "/opt/java/jdk25")

# Sinais, no log, de que o build falhou por exigir release/JDK 25.
_JDK25_SIGNALS = (
    re.compile(r"release version 25 not supported", re.I),
    re.compile(r"JavaSE-25", re.I),
)


def needs_jdk25_retry(log_text: str) -> bool:
    """True se o log indica falha por exigir release/JDK 25 (vale retry com 25).

    NÃO inclui 'major version 69' (isso é Gradle velho demais para o JDK 25 —
    retry com 25 só pioraria)."""
    return any(p.search(log_text) for p in _JDK25_SIGNALS)


def _java_env(java_home: str) -> dict:
    env = dict(os.environ)
    env["JAVA_HOME"] = java_home
    env["PATH"] = f"{java_home}/bin:" + env.get("PATH", "")
    return env


def _clone(repo: dict) -> bool:
    dest = RAW_DIR / repo_dir_name(repo["owner"], repo["repo"])
    if dest.exists():
        log.info("  já clonado: %s", dest)
        return True

    url = f"https://github.com/{repo['full_name']}.git"
    log.info("  clonando %s...", url)
    result = subprocess.run(
        ["git", "clone", "--depth=50", "--branch", repo["default_branch"], url, str(dest)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        log.error("  clone falhou: %s", result.stderr.strip())
        return False
    return True


def _confirm_claude(repo: dict) -> bool:
    dest = RAW_DIR / repo_dir_name(repo["owner"], repo["repo"])
    result = subprocess.run(
        ["git", "log", "--format=%an%n%ae%n%B"],
        cwd=dest, capture_output=True, text=True,
    )
    log_text = result.stdout

    if CLAUDE_COAUTHORED_RE.search(log_text):
        return True
    if CLAUDE_AUTHOR_EMAIL_RE.search(log_text):
        return True
    if CLAUDE_AUTHOR_NAME_RE.search(log_text):
        return True
    return False


def detect_build_system(dest: Path) -> str | None:
    """Detecta o sistema de build no RAIZ do diretório.

    Retorna 'maven', 'android', 'gradle' ou None. Maven tem precedência sobre
    Gradle. Projetos Gradle com AndroidManifest.xml são classificados como
    'android' (precisam do Android SDK, não de `gradle compileJava`).
    """
    if (dest / "pom.xml").exists():
        return "maven"
    if (dest / "build.gradle").exists() or (dest / "build.gradle.kts").exists():
        if any(dest.rglob("AndroidManifest.xml")):
            return "android"
        return "gradle"
    return None


# Diretórios que contêm build files de FIXTURE/teste, não do projeto em si.
_IGNORE_BUILD_DIRS = {"test-repo", "testdata", "test-data", "fixtures", "examples", "samples"}


def find_build(dest: Path, ignore_dirs: set | None = None):
    """Localiza o build do projeto, no raiz ou em subdiretório.

    Retorna (system, build_dir). Prefere o raiz; senão procura o build file
    mais raso em subdiretórios (ex.: pulumi `sdk/java/`, golf-api `api/`),
    ignorando diretórios de fixtures/teste. Retorna (None, None) se não achar.
    """
    ignore = ignore_dirs if ignore_dirs is not None else _IGNORE_BUILD_DIRS

    system = detect_build_system(dest)
    if system is not None:
        return system, dest

    # Procura subdiretórios pelo build file mais raso (ordena por profundidade).
    build_files = []
    for pattern in ("pom.xml", "build.gradle", "build.gradle.kts"):
        build_files.extend(dest.rglob(pattern))

    def _ignored(p: Path) -> bool:
        rel_parts = p.relative_to(dest).parts
        return any(part in ignore for part in rel_parts)

    candidates = sorted(
        (p for p in build_files if not _ignored(p)),
        key=lambda p: len(p.relative_to(dest).parts),
    )
    for bf in candidates:
        build_dir = bf.parent
        sub_system = detect_build_system(build_dir)
        if sub_system is not None:
            return sub_system, build_dir

    return None, None


def build_command(system: str, has_wrapper: bool) -> list[str]:
    """Monta o comando de build para o sistema detectado.

    - maven:   mvn -q -DskipTests compile
    - gradle:  ./gradlew (ou gradle) -q compileJava
    - android: ./gradlew (ou gradle) assembleDebug  (exige Android SDK)
    """
    if system == "maven":
        return ["mvn", "-q", "-DskipTests", "compile"]
    gradle = "./gradlew" if has_wrapper else "gradle"
    if system == "android":
        return [gradle, "assembleDebug"]
    return [gradle, "-q", "compileJava"]


def _build(repo: dict) -> bool:
    dest = RAW_DIR / repo_dir_name(repo["owner"], repo["repo"])

    system, build_dir = find_build(dest)
    if system is None:
        log.warning("  sem build file reconhecido (pom.xml / build.gradle)")
        (dest / "build.log").write_text("sem build file reconhecido\n")
        return False

    if build_dir != dest:
        log.info("  build em subdiretório: %s", build_dir.relative_to(dest))

    has_wrapper = (build_dir / "gradlew").exists()
    if has_wrapper:
        gradlew = build_dir / "gradlew"
        gradlew.chmod(gradlew.stat().st_mode | 0o111)  # garante permissão de execução

    cmd = build_command(system, has_wrapper)

    def _run(java_home: str):
        log.info("  %s detectado (JDK %s) — '%s'...",
                 system, "25" if java_home == JAVA25_HOME else "21", " ".join(cmd))
        return subprocess.run(
            cmd, cwd=build_dir, capture_output=True, text=True, timeout=600,
            env=_java_env(java_home),
        )

    # Tenta com JDK 21 (padrão, mais compatível).
    result = _run(JAVA21_HOME)
    combined = result.stdout + result.stderr

    # Se falhou por exigir release/JDK 25, refaz com o JDK 25.
    if result.returncode != 0 and needs_jdk25_retry(combined):
        log.info("  build exige release 25 — refazendo com JDK 25...")
        result = _run(JAVA25_HOME)

    # Captura o log completo do build para diagnóstico (P1).
    (dest / "build.log").write_text(
        f"$ (cwd={build_dir}) {' '.join(cmd)}\n[exit {result.returncode}]\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}\n"
    )

    if result.returncode != 0:
        log.warning("  build falhou (ver build.log):\n%s", result.stderr.strip()[-500:])
        return False

    log.info("  build OK")
    return True


def run_fase2():
    if not REPOS_JSON.exists():
        raise FileNotFoundError(f"{REPOS_JSON} não encontrado — rode a Fase 1 primeiro.")

    repos = json.loads(REPOS_JSON.read_text())
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    for repo in repos:
        name = repo["full_name"]
        log.info("[Fase 2] %s", name)

        cloned = _clone(repo)
        if not cloned:
            repo["claude_confirmed"] = False
            repo["build_ok"] = False
            continue

        confirmed = _confirm_claude(repo)
        repo["claude_confirmed"] = confirmed
        if not confirmed:
            log.warning("  sinal do Claude NÃO confirmado no git log")

        repo["build_ok"] = _build(repo)

    # Salva repos.json atualizado com claude_confirmed e build_ok
    REPOS_JSON.write_text(json.dumps(repos, indent=2, ensure_ascii=False))

    ok = sum(1 for r in repos if r.get("build_ok"))
    confirmed = sum(1 for r in repos if r.get("claude_confirmed"))
    log.info("Fase 2 concluída — %d/%d clonados confirmados com Claude, %d/%d builds OK",
             confirmed, len(repos), ok, len(repos))


if __name__ == "__main__":
    run_fase2()
