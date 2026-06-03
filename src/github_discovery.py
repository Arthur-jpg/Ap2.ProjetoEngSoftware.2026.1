import json
import os
import time

import requests
from dotenv import load_dotenv

from config import REPOS_JSON
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
CANDIDATE_POOL = 50  # coleta 50 candidatos, pega os 10 com mais estrelas
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

    # Passo 1: coletar exatamente TARGET repos Java+Claude
    repos: dict[str, dict] = {}
    _collect_repos(repos)
    log.info("%d candidatos Java+Claude encontrados. Buscando estrelas...", len(repos))

    # Passo 2: buscar estrelas (uma chamada por repo, só TARGET calls)
    for full_name, info in repos.items():
        meta = _fetch_stars(full_name)
        info.update(meta)
        log.info("  %-45s %6d estrelas", full_name, info["stars"])
        time.sleep(1)

    # Passo 3: ordenar por estrelas e salvar
    top10 = sorted(repos.values(), key=lambda r: r["stars"], reverse=True)[:TARGET]

    log.info("Top %d por estrelas:", TARGET)
    for r in top10:
        log.info("  %-45s %6d estrelas  %s", r["full_name"], r["stars"], r["signals"])

    REPOS_JSON.write_text(json.dumps(top10, indent=2, ensure_ascii=False))
    log.info("Salvo em %s", REPOS_JSON)


if __name__ == "__main__":
    run_fase1()
