"""Fase 5 — geração do dataset.csv final (uma linha por classe).

Junta, por classe: métricas OO do CK (class.csv), complexidade ciclomática
agregada por método (method.csv → McCC_avg/McCC_max) e contagem de bugs do
SpotBugs. Classes de repos não analisados pelo SpotBugs ficam com
Number_of_bugs = NaN (ausente != zero — ver docs/decisions/05-dataset-join.md).
"""
import json
from pathlib import Path

import pandas as pd

from config import (
    REPOS_JSON, RAW_DIR, DATASET_CSV,
    CLASS_COLUMNS, METHOD_COLUMNS, METHOD_CLASS_COLUMN,
)
from spotbugs_parse import count_bugs_by_class
from utils import log, repo_dir_name


def mccc_per_class(method_df: pd.DataFrame) -> pd.DataFrame:
    """Agrega McCC (complexidade ciclomática por método) por classe.

    Recebe um DataFrame com colunas 'class' e 'McCC'. Retorna uma linha por
    classe com McCC_avg (média) e McCC_max (máximo) — distintos do WMC, que é
    a soma (McCabe 1976).
    """
    if method_df.empty:
        return pd.DataFrame(columns=[METHOD_CLASS_COLUMN, "McCC_avg", "McCC_max"])

    agg = (
        method_df.groupby(METHOD_CLASS_COLUMN)["McCC"]
        .agg(McCC_avg="mean", McCC_max="max")
        .reset_index()
    )
    agg["McCC_avg"] = agg["McCC_avg"].round(4)
    return agg


def join_bugs(class_df: pd.DataFrame, bugs: dict[str, int], analyzed: bool) -> pd.DataFrame:
    """Adiciona Number_of_bugs ao DataFrame de classes.

    `bugs` mapeia nome de classe → contagem (do SpotBugs).
    - `analyzed=True` (repo compilou e foi analisado): classe sem achado → **0**
      (foi analisada, nenhum bug encontrado).
    - `analyzed=False` (repo não compilou/não analisado): tudo **NaN**
      (ausência de análise != zero bugs).
    Preserva uma linha por classe.
    """
    out = class_df.copy()
    mapped = out["class"].map(bugs)
    out["Number_of_bugs"] = mapped.fillna(0.0) if analyzed else float("nan")
    return out


def _read_ck_class(class_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(class_csv)
    keep = {k: v for k, v in CLASS_COLUMNS.items() if k in df.columns}
    return df[list(keep)].rename(columns=keep)


def _read_ck_method(method_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(method_csv)
    keep = {k: v for k, v in METHOD_COLUMNS.items() if k in df.columns}
    return df[[METHOD_CLASS_COLUMN, *[c for c in keep if c != METHOD_CLASS_COLUMN]]].rename(columns=keep)


def _load_bugs(clone_dir: Path, repo: dict) -> dict[str, int] | None:
    """Lê bugs do spotbugs.xml. Retorna None se o repo não foi analisado
    (build_ok=false ou sem XML) — sinaliza 'ausente', não zero."""
    if not repo.get("build_ok"):
        return None
    xml_path = clone_dir / "spotbugs.xml"
    if not xml_path.exists():
        return None
    return count_bugs_by_class(xml_path.read_text())


def _build_repo_frame(repo: dict) -> pd.DataFrame | None:
    clone_dir = RAW_DIR / repo_dir_name(repo["owner"], repo["repo"])
    ck_dir = clone_dir / "ck"
    class_csv, method_csv = ck_dir / "class.csv", ck_dir / "method.csv"

    if not class_csv.exists():
        log.warning("  class.csv do CK ausente: %s", class_csv)
        return None

    df = _read_ck_class(class_csv)
    if df.empty:
        return None

    # McCC agregado por classe (join pelo nome de classe completo do CK).
    if method_csv.exists():
        mccc = mccc_per_class(_read_ck_method(method_csv))
        df = df.merge(mccc, left_on="class", right_on=METHOD_CLASS_COLUMN, how="left")
    else:
        df["McCC_avg"], df["McCC_max"] = pd.NA, pd.NA

    # Bugs: repo analisado pelo SpotBugs → classe sem achado = 0; repo não
    # analisado (build falhou) → tudo NaN (ausência != zero).
    bugs = _load_bugs(clone_dir, repo)
    df = join_bugs(df, bugs or {}, analyzed=bugs is not None)
    # Garante dtype float (evita FutureWarning de concat com colunas all-NA).
    df["Number_of_bugs"] = df["Number_of_bugs"].astype("float64")

    df["repo"] = repo["full_name"]
    return df


def run_fase5():
    if not REPOS_JSON.exists():
        raise FileNotFoundError(f"{REPOS_JSON} não encontrado — rode as fases anteriores.")

    repos = json.loads(REPOS_JSON.read_text())
    frames = []
    for repo in repos:
        log.info("[Fase 5] %s", repo["full_name"])
        frame = _build_repo_frame(repo)
        if frame is not None:
            frames.append(frame)
            log.info("  %d classes adicionadas", len(frame))
        else:
            log.warning("  pulado (sem class.csv do CK)")

    if not frames:
        raise RuntimeError("Nenhum dado disponível para gerar o dataset.")

    # Remove frames vazios antes de concatenar (evita FutureWarning do pandas
    # e mudança de dtype por colunas all-NA).
    frames = [f for f in frames if not f.empty]
    dataset = pd.concat(frames, ignore_index=True)
    DATASET_CSV.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(DATASET_CSV, index=False)
    log.info("Fase 5 concluída — %d classes em %d repos → %s",
             len(dataset), len(frames), DATASET_CSV)


if __name__ == "__main__":
    run_fase5()
