"""Fase 5 — geração do dataset.csv final (uma linha por classe)."""
import json
from pathlib import Path

import pandas as pd

from config import (
    REPOS_JSON, RAW_DIR, DATASET_CSV,
    CLASS_COLUMNS, METHOD_COLUMNS, METHOD_CLASS_COLUMN,
)
from utils import log, repo_dir_name


def _mccc_per_class(method_csv: Path) -> pd.DataFrame:
    """Agrega McCC por classe: média e máximo."""
    if not method_csv.exists():
        return pd.DataFrame(columns=["class_name", "McCC_avg", "McCC_max"])

    dm = pd.read_csv(method_csv)
    if dm.empty or METHOD_CLASS_COLUMN not in dm.columns or "McCC" not in dm.columns:
        return pd.DataFrame(columns=["class_name", "McCC_avg", "McCC_max"])

    agg = (
        dm.groupby(METHOD_CLASS_COLUMN)["McCC"]
        .agg(McCC_avg="mean", McCC_max="max")
        .reset_index()
        .rename(columns={METHOD_CLASS_COLUMN: "class_name"})
    )
    agg["McCC_avg"] = agg["McCC_avg"].round(4)
    return agg


def _bugs_per_class(clone_dir: Path) -> pd.DataFrame:
    """Lê bugs_por_classe.csv; retorna DataFrame com class_name e bug_count."""
    csv_path = clone_dir / "bugs_por_classe.csv"
    if not csv_path.exists():
        return pd.DataFrame(columns=["class_name", "bug_count"])

    df = pd.read_csv(csv_path)
    if df.empty or "class" not in df.columns:
        return pd.DataFrame(columns=["class_name", "bug_count"])

    df = df.rename(columns={"class": "class_name"})
    return df[["class_name", "bug_count"]]


def _normalize_class_name(long_name: str) -> str:
    """Extrai o nome simples da classe de um LongName qualificado."""
    # ex: "com.example.Foo" → "Foo"; "Foo" → "Foo"
    return str(long_name).split(".")[-1].split("$")[0]


def _build_repo_frame(repo: dict) -> pd.DataFrame | None:
    if not repo.get("sourcemeter_ok"):
        return None

    class_csv  = Path(repo["class_csv"])
    method_csv = Path(repo["method_csv"])
    clone_dir  = RAW_DIR / repo_dir_name(repo["owner"], repo["repo"])

    if not class_csv.exists():
        log.warning("  Class.csv não encontrado: %s", class_csv)
        return None

    df = pd.read_csv(class_csv)
    if df.empty:
        return None

    # Renomeia colunas para nomes finais
    df = df.rename(columns=CLASS_COLUMNS)

    # Garante coluna "class" normalizada para o join
    if "class" not in df.columns:
        log.warning("  Coluna 'class' ausente em %s", class_csv)
        return None

    df["class_name"] = df["class"].apply(_normalize_class_name)

    # Join com McCC agregado por classe
    mccc = _mccc_per_class(method_csv)
    if not mccc.empty:
        mccc["class_name"] = mccc["class_name"].apply(_normalize_class_name)
        df = df.merge(mccc, on="class_name", how="left")
    else:
        df["McCC_avg"] = pd.NA
        df["McCC_max"] = pd.NA

    # Join com SpotBugs (zeros para classes sem bug)
    bugs = _bugs_per_class(clone_dir)
    if not bugs.empty:
        bugs["class_name"] = bugs["class_name"].apply(_normalize_class_name)
        df = df.merge(bugs, on="class_name", how="left")
        df["bug_count"] = df["bug_count"].fillna(0).astype(int)
    else:
        df["bug_count"] = 0

    df = df.rename(columns={"bug_count": "Number_of_bugs"})
    df["repo"] = repo["full_name"]

    df = df.drop(columns=["class_name"], errors="ignore")
    return df


def run_fase5():
    if not REPOS_JSON.exists():
        raise FileNotFoundError(
            f"{REPOS_JSON} não encontrado — rode as fases anteriores primeiro."
        )

    repos  = json.loads(REPOS_JSON.read_text())
    frames = []

    for repo in repos:
        log.info("[Fase 5] %s", repo["full_name"])
        frame = _build_repo_frame(repo)
        if frame is not None:
            frames.append(frame)
            log.info("  %d classes adicionadas", len(frame))
        else:
            log.warning("  pulado (sem dados)")

    if not frames:
        raise RuntimeError("Nenhum dado disponível para gerar o dataset.")

    dataset = pd.concat(frames, ignore_index=True)

    # Garante colunas numéricas
    numeric_cols = ["LOC", "CLOC", "WMC", "CBO", "RFC", "DIT", "LCOM5",
                    "NM", "NPM", "McCC_avg", "McCC_max", "Number_of_bugs"]
    for col in numeric_cols:
        if col in dataset.columns:
            dataset[col] = pd.to_numeric(dataset[col], errors="coerce")

    DATASET_CSV.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(DATASET_CSV, index=False)

    log.info("Fase 5 concluída — %d classes em %d repos → %s",
             len(dataset), len(frames), DATASET_CSV)


if __name__ == "__main__":
    run_fase5()
