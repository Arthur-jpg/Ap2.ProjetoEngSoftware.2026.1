import json
import subprocess

from config import REPOS_JSON, RAW_DIR, CLAUDE_COAUTHORED_RE, CLAUDE_AUTHOR_EMAIL_RE, CLAUDE_AUTHOR_NAME_RE
from utils import log, repo_dir_name


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


def _build(repo: dict) -> bool:
    dest = RAW_DIR / repo_dir_name(repo["owner"], repo["repo"])

    if (dest / "pom.xml").exists():
        log.info("  Maven detectado — compilando...")
        result = subprocess.run(
            ["mvn", "-q", "-DskipTests", "compile"],
            cwd=dest, capture_output=True, text=True, timeout=300,
        )
    elif (dest / "build.gradle").exists() or (dest / "build.gradle.kts").exists():
        # Prefere o wrapper incluído no repo (não exige Gradle instalado globalmente)
        gradlew = dest / "gradlew"
        if gradlew.exists():
            gradlew.chmod(gradlew.stat().st_mode | 0o111)  # garante permissão de execução
            gradle_cmd = "./gradlew"
        else:
            gradle_cmd = "gradle"
        log.info("  Gradle detectado — compilando com '%s'...", gradle_cmd)
        result = subprocess.run(
            [gradle_cmd, "-q", "compileJava"],
            cwd=dest, capture_output=True, text=True, timeout=300,
        )
    else:
        log.warning("  sem build file reconhecido (pom.xml / build.gradle)")
        return False

    if result.returncode != 0:
        log.warning("  build falhou:\n%s", result.stderr.strip()[-500:])
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
