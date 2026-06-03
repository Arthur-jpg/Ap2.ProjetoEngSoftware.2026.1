import re
from pathlib import Path

# --- Paths ---
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
REPOS_JSON = DATA_DIR / "repos.json"
DATASET_CSV = DATA_DIR / "dataset.csv"
SOURCEMETER_HOME = Path("/app/tools/SourceMeter")
SPOTBUGS_HOME = Path("/opt/spotbugs-4.8.6")

# --- Detecção do Claude ---
CLAUDE_COAUTHORED_RE = re.compile(
    r"co-authored-by:\s*claude\b.*?noreply@anthropic\.com",
    re.IGNORECASE,
)
CLAUDE_AUTHOR_EMAIL_RE = re.compile(r"@anthropic\.com", re.IGNORECASE)
CLAUDE_AUTHOR_NAME_RE = re.compile(r"\bclaude\b", re.IGNORECASE)

# --- Colunas-alvo do SourceMeter (nome no CSV → nome final no dataset) ---
CLASS_COLUMNS = {
    "LongName": "class",
    "Path": "file",
    "LOC": "LOC",
    "CLOC": "CLOC",
    "WMC": "WMC",
    "CBO": "CBO",
    "RFC": "RFC",
    "DIT": "DIT",
    "LCOM5": "LCOM5",
    "NM": "NM",
    "NPM": "NPM",
    "WarningMajor": "WarningMajor",
    "RuleViolations_Design": "Design_Rules",
    "RuleViolations_Coupling": "Coupling_Metric_Rules",
    "RuleViolations_Documentation": "Documentation_Metric_Rules",
    "RuleViolations_Size": "Size_Metric_Rules",
}

METHOD_COLUMNS = {
    "LongName": "method",
    "McCC": "McCC",
}

# Coluna de nome de classe no Method CSV para o agrupamento
METHOD_CLASS_COLUMN = "Class"
