import json
import os
import time

import requests
from dotenv import load_dotenv

from config import REPOS_JSON, EXCLUDE_REPOS, PINNED_REPOS
from utils import log

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
SEARCH_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.cloak-preview+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
REPO_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

TARGET = 10
CANDIDATE_POOL = 100  # coleta 50 candidatos, pega os 10 com mais estrelas
REQ_INTERVAL = 2.5

SIGNAL_QUERIES = [
    ('"Co-authored-by: Claude" "noreply@anthropic.com" language:java', "co_authored_by"),
    ("author-email:noreply@anthropic.com language:java", "author_email"),
]


def _wait_rate_limit(resp: requests.Response):
    reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
    wait = max(reset - time.time(), 1)
    log.warning("Rate limit. Aguardando %.0fs...", wait)
    time.sleep(wait)


def _collect_repos(repos: dict):
    """Coleta CANDIDATE_POOL repos únicos de Java+Claude, para selecionar os 10 com mais estrelas."""
    for query, signal in SIGNAL_QUERIES:
        if len(repos) >= CANDIDATE_POOL:
            break
        log.info("Buscando — sinal '%s'...", signal)
        page = 1
        while len(repos) < TARGET:
            resp = requests.get(
                "https://api.github.com/search/commits",
                headers=SEARCH_HEADERS,
                params={"q": query, "per_page": 100, "page": page},
            )
            if resp.status_code == 422:
                break
            if resp.status_code in (403, 429):
                _wait_rate_limit(resp)
                continue
            resp.raise_for_status()

            for item in resp.json().get("items", []):
                r = item.get("repository", {})
                full_name = r.get("full_name")
                if not full_name or full_name in repos:
                    continue
                repos[full_name] = {
                    "full_name": full_name,
                    "owner": r.get("owner", {}).get("login"),
                    "repo": r.get("name"),
                    "signals": [signal],
                }
                if len(repos) >= CANDIDATE_POOL:
                    break

            items = resp.json().get("items", [])
            log.info("  pág %d — %d/%d candidatos coletados", page, len(repos), CANDIDATE_POOL)
            if len(items) < 100:
                break
            page += 1
            time.sleep(REQ_INTERVAL)


def is_android_repo(file_paths, gradle_text: str = "") -> bool:
    """Heurística: o repo é um app Android?

    True se houver AndroidManifest.xml na árvore OU o build.gradle aplicar o
    plugin Android. Android exige SDK e está fora da população (ver
    docs/decisions/01-selecao-repos.md).
    """
    for p in file_paths:
        if p.endswith("AndroidManifest.xml"):
            return True
    if "com.android" in gradle_text:
        return True
    return False


def apply_curation(repos: dict, exclude: set, include: list) -> dict:
    """Aplica a curadoria à amostra: remove `exclude` e garante `include` fixos.

    Retorna um novo dict {full_name: info}. Includes ausentes são adicionados;
    includes já presentes não são duplicados.
    """
    out = {fn: info for fn, info in repos.items() if fn not in exclude}
    pinned_names = {p["full_name"] for p in include}
    for pinned in include:
        fn = pinned["full_name"]
        if fn not in out:
            out[fn] = dict(pinned)
    # Marca os fixados para a seleção final garanti-los.
    for fn, info in out.items():
        info["pinned"] = fn in pinned_names
    return out


def select_final(java_repos: list, target: int) -> list:
    """Seleciona os `target` repos finais, ordenados por estrelas (desc).

    Repos fixados (`pinned=True`) são SEMPRE incluídos; as vagas restantes são
    preenchidas pelos não-fixados com mais estrelas. O resultado fica ordenado
    por estrelas desc.
    """
    pinned = [r for r in java_repos if r.get("pinned")]
    rest = [r for r in java_repos if not r.get("pinned")]
    rest_sorted = sorted(rest, key=lambda r: r["stars"], reverse=True)
    chosen = pinned + rest_sorted[: max(target - len(pinned), 0)]
    return sorted(chosen, key=lambda r: r["stars"], reverse=True)


def _is_android_via_api(full_name: str, default_branch: str) -> bool:
    """Consulta a árvore do repo e detecta marcadores Android."""
    url = f"https://api.github.com/repos/{full_name}/git/trees/{default_branch}?recursive=1"
    resp = requests.get(url, headers=REPO_HEADERS)
    if resp.status_code != 200:
        return False
    paths = [t.get("path", "") for t in resp.json().get("tree", [])]
    return is_android_repo(paths)


def _fetch_stars(full_name: str) -> dict:
    resp = requests.get(f"https://api.github.com/repos/{full_name}", headers=REPO_HEADERS)
    if resp.status_code in (403, 429):
        _wait_rate_limit(resp)
        resp = requests.get(f"https://api.github.com/repos/{full_name}", headers=REPO_HEADERS)
    resp.raise_for_status()
    d = resp.json()
    return {
        "stars": d.get("stargazers_count", 0),
        "default_branch": d.get("default_branch", "main"),
        "pushed_at": d.get("pushed_at"),
        "language": d.get("language"),
    }


def run_fase1():
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN não definido. Copie .env.example para .env e preencha.")

    REPOS_JSON.parent.mkdir(parents=True, exist_ok=True)

    # Passo 1: coletar candidatos (language:java na query filtra commits, não o repo principal)
    repos: dict[str, dict] = {}
    _collect_repos(repos)

    # Passo 1.5: curadoria reprodutível — remove Android conhecidos, fixa includes.
    repos = apply_curation(repos, exclude=EXCLUDE_REPOS, include=PINNED_REPOS)
    log.info("%d candidatos (pós-curadoria). Verificando linguagem e estrelas...", len(repos))

    # Passo 2: buscar metadados e filtrar SOMENTE repos Java, não-Android
    java_repos = []
    for full_name, info in repos.items():
        meta = _fetch_stars(full_name)
        if meta["language"] != "Java":
            log.info("  ignorado %-40s (linguagem: %s)", full_name, meta["language"])
            continue
        if _is_android_via_api(full_name, meta["default_branch"]):
            log.info("  ignorado %-40s (Android — fora do escopo)", full_name)
            continue
        info.update(meta)
        log.info("  Java OK  %-40s %6d estrelas", full_name, info["stars"])
        java_repos.append(info)
        time.sleep(1)

    if len(java_repos) < TARGET:
        log.warning("Apenas %d repos Java encontrados (esperado %d). Aumente CANDIDATE_POOL.", len(java_repos), TARGET)

    # Passo 3: seleção final — fixados garantidos + top por estrelas
    top10 = select_final(java_repos, TARGET)

    log.info("Top %d Java+Claude por estrelas:", len(top10))
    for r in top10:
        log.info("  %-45s %6d estrelas  %s", r["full_name"], r["stars"], r["signals"])

    # Remove o marcador interno 'pinned' antes de salvar (mantém o schema limpo).
    for r in top10:
        r.pop("pinned", None)

    REPOS_JSON.write_text(json.dumps(top10, indent=2, ensure_ascii=False))
    log.info("Salvo em %s", REPOS_JSON)


if __name__ == "__main__":
    run_fase1()
