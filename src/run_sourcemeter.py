"""Fase 3 — extração de métricas OO via análise Python (javalang)."""
import json
import re
from pathlib import Path

import pandas as pd

try:
    import javalang
    _HAS_JAVALANG = True
except ImportError:
    _HAS_JAVALANG = False

from config import REPOS_JSON, RAW_DIR
from utils import log, repo_dir_name

# ---------------------------------------------------------------------------
# Helpers de contagem de texto (fallback e CLOC)
# ---------------------------------------------------------------------------

_RE_BLOCK_COMMENT  = re.compile(r"/\*.*?\*/", re.DOTALL)
_RE_LINE_COMMENT   = re.compile(r"//.*")
_RE_STRING_LITERAL = re.compile(r'"(?:\\.|[^"\\])*"')


def _strip_strings(src: str) -> str:
    return _RE_STRING_LITERAL.sub('""', src)


def _count_cloc(src: str) -> int:
    count = 0
    in_block = False
    for line in src.splitlines():
        s = line.strip()
        if in_block:
            count += 1
            if "*/" in s:
                in_block = False
        elif s.startswith("//"):
            count += 1
        elif "/*" in s:
            count += 1
            tail = s[s.index("/*") + 2:]
            if "*/" not in tail:
                in_block = True
    return count


def _cyclomatic(src: str) -> int:
    """Complexidade ciclomática aproximada: 1 + ramificações."""
    branches = re.findall(
        r"\b(if|else\s+if|for|while|case|catch|\?\s*[^:]+:)\b", src
    )
    return 1 + len(branches)


# ---------------------------------------------------------------------------
# Extração com javalang
# ---------------------------------------------------------------------------

def _modifiers(node) -> set:
    return set(node.modifiers or [])


def _method_body_src(method_node, full_src: str) -> str:
    """Extrai o trecho de código do método (heurística por posição)."""
    if method_node.position is None:
        return ""
    start = method_node.position.line - 1
    lines = full_src.splitlines()
    body_lines = []
    depth = 0
    for line in lines[start:]:
        body_lines.append(line)
        depth += line.count("{") - line.count("}")
        if depth <= 0 and body_lines:
            break
    return "\n".join(body_lines)


def _count_method_calls(src: str) -> int:
    return len(re.findall(r"\.\s*\w+\s*\(", src))


def _analyze_file_javalang(java_file: Path):
    """Retorna (class_rows, method_rows) para um arquivo .java."""
    src = java_file.read_text(errors="ignore")
    loc  = src.count("\n") + 1
    cloc = _count_cloc(src)

    try:
        tree = javalang.parse.parse(src)
    except Exception:
        return [], []

    imports = tree.imports or []
    import_pkgs = {".".join(i.path.split(".")[:-1]) for i in imports}
    cbo_base = len(import_pkgs)

    class_rows  = []
    method_rows = []

    for _, cls in tree.filter(javalang.tree.ClassDeclaration):
        methods = list(cls.methods or [])
        fields  = list(cls.fields  or [])

        nm  = len(methods)
        npm = sum(1 for m in methods if "public" in _modifiers(m))
        dit = 1 if cls.extends else 0

        # WMC = soma da complexidade ciclomática de cada método
        wmc = 0
        for m in methods:
            body = _method_body_src(m, src)
            wmc += _cyclomatic(body)

        # RFC = NM + chamadas de método no corpo da classe
        rfc = nm + _count_method_calls(src)

        # LCOM5: proporção de pares de métodos sem campo em comum (aprox.)
        field_names = {
            v.name
            for f in fields
            for v in (f.declarators or [])
        }
        if nm > 1 and field_names:
            shared = 0
            for m in methods:
                body = _method_body_src(m, src)
                uses = {f for f in field_names if re.search(rf"\b{re.escape(f)}\b", body)}
                shared += len(uses)
            lcom5 = max(0.0, 1 - shared / (nm * max(len(field_names), 1)))
        else:
            lcom5 = 0.0

        class_rows.append({
            "LongName":  f"{tree.package.name}.{cls.name}" if tree.package else cls.name,
            "Path":      str(java_file),
            "LOC":       loc,
            "CLOC":      cloc,
            "WMC":       wmc,
            "CBO":       cbo_base,
            "RFC":       rfc,
            "DIT":       dit,
            "LCOM5":     round(lcom5, 4),
            "NM":        nm,
            "NPM":       npm,
            "WarningMajor":               0,
            "RuleViolations_Design":      0,
            "RuleViolations_Coupling":    0,
            "RuleViolations_Documentation": 0,
            "RuleViolations_Size":        0,
        })

        for m in methods:
            body = _method_body_src(m, src)
            method_rows.append({
                "LongName": f"{cls.name}.{m.name}",
                "Class":    cls.name,
                "McCC":     _cyclomatic(body),
            })

    return class_rows, method_rows


# ---------------------------------------------------------------------------
# Fallback regex (quando javalang não está disponível ou falha no parse)
# ---------------------------------------------------------------------------

_RE_CLASS   = re.compile(r"\bclass\s+(\w+)(?:\s+extends\s+(\w+))?")
_RE_METHOD  = re.compile(r"\b(public|private|protected)\b[^;{]*\w+\s*\([^)]*\)\s*(?:throws\s+\w+\s*)?\{")
_RE_IMPORT  = re.compile(r"^\s*import\s+([\w.]+);", re.MULTILINE)


def _analyze_file_regex(java_file: Path):
    src = java_file.read_text(errors="ignore")
    loc  = src.count("\n") + 1
    cloc = _count_cloc(src)

    class_match = _RE_CLASS.search(src)
    if not class_match:
        return [], []

    class_name  = class_match.group(1)
    has_extends = bool(class_match.group(2))

    method_matches = _RE_METHOD.findall(src)
    nm  = len(method_matches)
    npm = sum(1 for v in method_matches if v == "public")

    import_pkgs = {".".join(m.split(".")[:-1]) for m in _RE_IMPORT.findall(src)}
    cbo  = len(import_pkgs)
    wmc  = _cyclomatic(src)
    rfc  = nm + _count_method_calls(src)

    class_rows = [{
        "LongName":  class_name,
        "Path":      str(java_file),
        "LOC":       loc,
        "CLOC":      cloc,
        "WMC":       wmc,
        "CBO":       cbo,
        "RFC":       rfc,
        "DIT":       1 if has_extends else 0,
        "LCOM5":     0.0,
        "NM":        nm,
        "NPM":       npm,
        "WarningMajor":               0,
        "RuleViolations_Design":      0,
        "RuleViolations_Coupling":    0,
        "RuleViolations_Documentation": 0,
        "RuleViolations_Size":        0,
    }]

    method_rows = [{"LongName": f"{class_name}.method_{i}", "Class": class_name, "McCC": 1}
                   for i in range(nm)]

    return class_rows, method_rows


# ---------------------------------------------------------------------------
# Orquestração por repo
# ---------------------------------------------------------------------------

def _analyze_repo(repo: dict) -> bool:
    clone_dir = RAW_DIR / repo_dir_name(repo["owner"], repo["repo"])
    out_dir   = clone_dir / "sourcemeter"
    out_dir.mkdir(parents=True, exist_ok=True)

    class_csv  = out_dir / "Class.csv"
    method_csv = out_dir / "Method.csv"

    if class_csv.exists() and method_csv.exists():
        log.info("  Métricas já extraídas: %s", clone_dir.name)
        return True

    java_files = list(clone_dir.rglob("*.java"))
    if not java_files:
        log.warning("  Nenhum arquivo .java encontrado em %s", clone_dir.name)
        return False

    log.info("  Analisando %d arquivos .java em %s...", len(java_files), clone_dir.name)

    all_classes = []
    all_methods = []
    errors = 0

    for jf in java_files:
        try:
            if _HAS_JAVALANG:
                cr, mr = _analyze_file_javalang(jf)
            else:
                cr, mr = _analyze_file_regex(jf)
            all_classes.extend(cr)
            all_methods.extend(mr)
        except Exception as exc:
            errors += 1
            log.debug("  Erro ao analisar %s: %s", jf.name, exc)

    if not all_classes:
        log.error("  Nenhuma classe extraída de %s (%d erros)", clone_dir.name, errors)
        return False

    pd.DataFrame(all_classes).to_csv(class_csv, index=False)
    pd.DataFrame(all_methods).to_csv(method_csv, index=False)

    log.info("  OK — %d classes, %d métodos (%d arquivos com erro)",
             len(all_classes), len(all_methods), errors)
    return True


# ---------------------------------------------------------------------------
# Entrypoint da fase
# ---------------------------------------------------------------------------

def run_fase3():
    if not REPOS_JSON.exists():
        raise FileNotFoundError(
            f"{REPOS_JSON} não encontrado — rode as fases anteriores primeiro."
        )

    repos     = json.loads(REPOS_JSON.read_text())
    ok_count  = 0

    for repo in repos:
        log.info("[Fase 3] %s", repo["full_name"])
        success = _analyze_repo(repo)
        repo["sourcemeter_ok"] = success
        if success:
            ok_count += 1
            out_dir = RAW_DIR / repo_dir_name(repo["owner"], repo["repo"]) / "sourcemeter"
            repo["class_csv"]  = str(out_dir / "Class.csv")
            repo["method_csv"] = str(out_dir / "Method.csv")

    REPOS_JSON.write_text(json.dumps(repos, indent=2, ensure_ascii=False))
    log.info("Fase 3 concluída — %d/%d repos", ok_count, len(repos))


if __name__ == "__main__":
    run_fase3()
