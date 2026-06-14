import os
import re
from pathlib import Path

# --- Paths ---
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
REPOS_JSON = DATA_DIR / "repos.json"
DATASET_CSV = DATA_DIR / "dataset.csv"

# Motor de métricas: CK (Aniche). Jar baixado no Docker; caminho via env CK_JAR.
# (Ver docs/decisions/03-metricas-ck.md — CK 0.7.0, Chidamber & Kemerer 1994.)
CK_JAR = Path(os.environ.get("CK_JAR", "/opt/ck/ck.jar"))
SPOTBUGS_HOME = Path(os.environ.get("SPOTBUGS_HOME", "/opt/spotbugs-4.10.2"))

# --- Curadoria da amostra (Fase 1) ---
# Repos excluídos da população. Ver docs/decisions/01-selecao-repos.md:
# - Android (exigem SDK, fora do escopo de código Java OO "padrão");
# - "Java" no rótulo do GitHub mas não são projetos Java OO de fato (livro
#   multi-linguagem, repo de 1 arquivo, Java só em fixtures de teste).
EXCLUDE_REPOS = {
    "JackZho/android-library-system",
    "JackZho/MusicPlayer",
    "adamzwasserman/honest-code-traces",   # livro multi-linguagem; ~10 .java
    "mechanicus01/programing",             # repo de estudo; 1 .java
    "akrishnanDG/schematizer-skill",       # "skill"; Java só em test-repo/ (fixtures)
}
# Repos fixados que sempre entram na amostra. Confirmados como Java + Claude,
# projetos Java reais (build file + >=20 .java). A Fase 1 busca os metadados.
PINNED_REPOS = [
    {"full_name": "pulumi/pulumi-java", "owner": "pulumi", "repo": "pulumi-java",
     "signals": ["co_authored_by"]},
    {"full_name": "yksi7417/cross_asset_ems", "owner": "yksi7417", "repo": "cross_asset_ems",
     "signals": ["co_authored_by"]},
    {"full_name": "adriandeleon/Editora", "owner": "adriandeleon", "repo": "Editora",
     "signals": ["co_authored_by"]},
    {"full_name": "jbiscella/H-tchen-Mail", "owner": "jbiscella", "repo": "H-tchen-Mail",
     "signals": ["co_authored_by"]},
]

# --- Detecção do Claude ---
CLAUDE_COAUTHORED_RE = re.compile(
    r"co-authored-by:\s*claude\b.*?noreply@anthropic\.com",
    re.IGNORECASE,
)
CLAUDE_AUTHOR_EMAIL_RE = re.compile(r"@anthropic\.com", re.IGNORECASE)
CLAUDE_AUTHOR_NAME_RE = re.compile(r"\bclaude\b", re.IGNORECASE)

# --- Colunas-alvo do CK 0.7.0 (cabeçalho real no CSV → nome final no dataset) ---
# Cabeçalhos verbatim do class.csv do CK (ResultWriter.java). O CK NÃO produz
# CLOC nem violações de regra (WarningMajor/RuleViolations_*) — essas eram do
# SourceMeter e foram removidas (não zerar colunas inexistentes).
# Referências: CK 1994 (cbo/dit/rfc/wmc/lcom/noc); Henderson-Sellers 1996 (lcom*);
# McCabe 1976 (wmc = soma da complexidade ciclomática dos métodos).
CLASS_COLUMNS = {
    "file": "file",
    "class": "class",
    "loc": "LOC",
    "wmc": "WMC",            # soma da complexidade ciclomática (McCabe 1976)
    "cbo": "CBO",            # Chidamber & Kemerer 1994
    "rfc": "RFC",
    "dit": "DIT",
    "noc": "NOC",
    "lcom": "LCOM",          # LCOM original (Chidamber & Kemerer 1994)
    "lcom*": "LCOM_norm",    # LCOM* normalizado 0–1 (Henderson-Sellers 1996)
    "totalMethodsQty": "NM",
    "publicMethodsQty": "NPM",
}

# method.csv do CK: 'wmc' é a complexidade ciclomática POR método (McCabe).
# Agregamos em McCC_avg/McCC_max por classe na Fase 5.
METHOD_COLUMNS = {
    "method": "method",
    "wmc": "McCC",
}

# Coluna de nome de classe no method.csv do CK, usada no agrupamento método→classe.
METHOD_CLASS_COLUMN = "class"
