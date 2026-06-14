# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project Overview

Software Engineering **research project** (IBMEC, AP2): study the quality of **AI-assisted
code** by measuring object-oriented metrics on **Java** GitHub repositories where **Claude**
is a contributor. One project = one paper = one repository. Prioritize **correctness of the
metrics**, clarity, and reproducibility over production abstractions.

Unit of analysis = the **class**. The final deliverable is `data/dataset.csv` (one row per
class) plus a statistical analysis (`notebooks/analise.ipynb`) and a paper (`artigo.tex`).

## Tooling

- **Language:** Python 3 (orchestration) driving **Java 17** static-analysis tools.
- **Dependencies:** `pip` + `requirements.txt` (NOT uv/poetry/conda).
- **Environment:** **Docker** (`docker/Dockerfile`) for cross-OS reproducibility — JDK 17,
  Maven, Gradle, SpotBugs, and the **CK** metrics jar (auto-downloaded).
- **Static-analysis tools:** OO metrics via **CK 0.7.0** (`com.github.mauricioaniche/ck`,
  env `CK_JAR`), SpotBugs (bugs), and — later — JaCoCo (coverage) for CRAP.

### Common commands
```bash
./run.sh                              # build Docker image + run pipeline with ./data mounted
python src/main.py                    # run all phases (skips Fase 1 if repos.json exists)
python src/main.py --fase N           # run only phase N (1..5; 6 later for JaCoCo/CRAP)
python -m pytest tests/               # or: bash tests/test_fase0.sh ; python tests/test_fase1.py
pip install -r requirements.txt       # local (non-Docker) deps
```

Never commit secrets. `GITHUB_TOKEN` comes from `.env` (see `.env.example`); never hardcode it.

## Project Structure
```
.
|-- PLANO.md                 # the phased plan + acceptance criteria (source of truth)
|-- docker/                  # Dockerfile + entrypoint (the reproducible environment)
|-- tools/                   # SourceMeter / CK / SpotBugs binaries (mounted, not committed)
|-- src/                     # one module per phase, imported by main.py
|   |-- config.py            # paths, Claude-detection regex, CSV column maps
|   |-- github_discovery.py  # Fase 1
|   |-- clone_build.py       # Fase 2
|   |-- run_sourcemeter.py   # Fase 3 (OO metrics)
|   |-- run_spotbugs.py      # Fase 4 (bugs)
|   |-- build_dataset.py     # Fase 5 (join → dataset.csv)
|   |-- utils.py             # log, run(), name normalization
|   |-- main.py              # --fase orchestrator
|-- data/
|   |-- repos.json           # Fase-1 contract: the 10 selected repos + flags
|   |-- raw/<owner>__<repo>/ # clones + per-repo tool outputs (generated)
|   |-- dataset.csv          # FINAL: one row per class (generated)
|-- tests/                   # one acceptance check per phase
|-- notebooks/analise.ipynb  # statistical analysis (consumes dataset.csv)
|-- requirements.txt
```

Rules:
- Reusable logic lives in `src/` and is imported; `main.py` stays a thin orchestrator and each
  `run_faseN()` is the single entry point for its phase.
- **`data/repos.json` is a contract** between phases — treat its shape as an API; don't break
  field names (`owner`, `repo`, `default_branch`, `claude_confirmed`, `build_ok`, ...).
- **Never hand-edit generated outputs** (`data/raw/**`, `dataset.csv`); regenerate them.
- Don't commit: clones under `data/raw/`, tool binaries in `tools/`, `.env`, large CSVs/figures
  if heavy. Check `.gitignore` first.

## Pipeline phases & contracts

Run and validate **one phase at a time** (`--fase N`); only advance when that phase's test passes.

| Fase | Module | Input | Output | Test |
|------|--------|-------|--------|------|
| 1 | github_discovery | GitHub API + token | `data/repos.json` (10 Java repos) | test_fase1 |
| 2 | clone_build | repos.json | clones in `data/raw/`, `build_ok` flags | test_fase2 |
| 3 | run_sourcemeter | clones | `*-Class.csv`, `*-Method.csv` | test_fase3 |
| 4 | run_spotbugs | compiled bytecode (`build_ok`) | `spotbugs.xml`, bugs/class | test_fase4 |
| 5 | build_dataset | all of the above | `data/dataset.csv` | test_fase5 |
| 6 (later) | run_jacoco | repos whose **tests run** | `LineCoverage`, `BranchCoverage`, `CRAP` | test_fase6 |

**Compile vs. run:** the OO-metrics tool reads source only; SpotBugs needs `compile`d bytecode;
**only Fase 6 (JaCoCo/CRAP) runs the test suite** — and never the application itself.

## Metrics (target columns in dataset.csv) — CK's REAL schema

CK column names are the source of truth (verified from CK 0.7.0 `ResultWriter.java`).

- Size: `LOC`  *(CK has no comment-line metric → no `CLOC`)*
- Complexity: `WMC` (= Σ per-method McCabe), `McCC_avg`, `McCC_max` (per-method McCabe,
  aggregated from `method.csv` `wmc` — **≠ WMC**) — McCabe 1976
- Coupling: `CBO`, `RFC`  ·  Inheritance: `DIT`, `NOC` — Chidamber & Kemerer 1994
- Cohesion: `LCOM` (CK&K 1994) and `LCOM_norm` (CK `lcom*`, **LCOM\*** Henderson-Sellers 1996)
  — **not** "LCOM5 (Hitz & Montazeri)"
- Interface: `NM` (`totalMethodsQty`), `NPM` (`publicMethodsQty`)
- Coverage/quality (Fase 6, reserved): `LineCoverage`, `BranchCoverage`,
  `CRAP = comp²·(1−cov)³ + comp` (Savoia 2007)
- Response variable: `Number of bugs` (SpotBugs; **NaN when not analyzed — never 0**)

**DROPPED — CK cannot produce these, do NOT zero-fill:** `CLOC`, `WarningMajor`,
`Design_Rules`, `Coupling_Metric_Rules`, `Documentation_Metric_Rules`, `Size_Metric_Rules`
(SourceMeter-only). The column map lives in `src/config.py` (`CLASS_COLUMNS`/`METHOD_COLUMNS`).

**Metric integrity is the project's whole point.** CK computes genuine CBO/DIT/RFC/LCOM/WMC.
Do **not** ship regex/heuristic proxies under these names, and do not leave columns hardcoded
to 0 — mark uncomputed values as null and document them.

## Code Style

- PEP 8, 120-char lines. Type hints on public functions in `src/`.
- Docstrings (Portuguese is fine — match the existing code) stating what a phase does, its inputs,
  and its outputs.
- **DRY:** before adding code, search for an existing helper/column and reuse it (e.g.
  `utils.run`, `utils.normalize_class_name`, `utils.repo_dir_name`, `config.*_COLUMNS`). Generalize
  the original instead of forking a near-copy.
- **KISS / YAGNI:** simplest thing that works; plain functions + pandas idioms over clever
  abstractions. This is research code.
- No magic numbers: tool versions, paths, regexes, and thresholds live in `config.py` / Dockerfile,
  not inline.
- **Fail loudly** on tool/subprocess errors in the data path — don't silently swallow a failed
  SourceMeter/SpotBugs run and emit empty CSVs. Per-repo tolerance is fine **if logged**.

## Development Workflow: strict TDD (mandatory)

**Pure test-driven development for ALL code. No exceptions, no "test-after."** Every change is
atomic and paired with a test written **first** that verifies the behavior actually works.

1. **Red** — write a failing test that specifies the exact desired behavior, and run it to see it
   fail for the right reason.
2. **Green** — write the **minimal** code to make it pass.
3. **Refactor** — clean up for simplicity and readability while keeping every test green.

Rules:
- Write the test **before** the implementation, every cycle. Keep units small and atomic.
- Tests must assert **real functionality and outcomes** — correct metric values, correct CSV
  shape/contents, correct joins — not weak "it ran without error" smoke checks.
- **Never weaken an assertion** to make a test pass; fix the root cause.
- Keep the whole suite green after every change; run it constantly.
- Per phase: extend `tests/test_faseN` to encode PLANO.md's acceptance criterion, then implement
  `run_faseN()` to satisfy it. Prove each phase on **one** building repo (`talk-to-repo`) before
  scaling to 10.
- `repos.json` / CSV schema changes must update all consumers (later phases + notebook) **and**
  their tests in the same change.
- Validate joins explicitly: class-name normalization between the metrics tool and SpotBugs
  (`utils.normalize_class_name`) is a known failure point for inner/anonymous classes — write a
  test for it.

## Reproducibility

- Everything runs from `./run.sh` (Docker) or `python src/main.py --fase N`; results land under
  `data/` mounted as a volume.
- Pin tool versions (Dockerfile ENV) so reruns are deterministic. **Automate tool downloads**
  (SourceMeter/CK) in the Dockerfile rather than manual steps.
- Don't overwrite results silently; a rerun should reproduce the same `dataset.csv`.
- Record, alongside results, which metric tool + version produced them.

## Documentation & references (research project)

This is a research project — **every design decision must cite a paper**, kept in `docs/`.

- For each implemented part, write/update `docs/decisions/NN-<topic>.md` with **why** (with a
  citation), **how**, and **what was rejected** — in the *same change* that touches the code.
- Accumulate citations in `docs/refs.bib` (BibTeX); the paper (`docs/artigo.tex`) reuses it.
- Canonical refs: CK 1994 (`ck1994`), McCabe 1976 (`mccabe1976`), Henderson-Sellers 1996
  (`hendersonsellers1996`), Savoia 2007 (`savoia2007`), Subramanyam & Krishnan 2003
  (`subramanyam2003`), D'Ambros 2012 (`dambros2012`), Basili 1996, Fowler 1999.
- Don't introduce a metric, tool, or statistical choice in code without a matching cited doc.

## Git Conventions

- **The agent must NEVER run `git commit`, `git push`, or otherwise create commits.**
  Only the **user** commits. Make changes in the working tree and leave them for the user
  to review and commit. Do not stage or commit on their behalf, even when asked to "save".
- Never write secrets into tracked files: real tokens go ONLY in `.env` (gitignored);
  `.env.example` holds a **placeholder**. The `GITHUB_TOKEN` comes from `.env`.
- Never commit: `data/raw/**`, `.env`, tool binaries, heavy figures (hygiene, when the
  user does commit).

## What NOT to Do

- Don't emit **proxy metrics** under real metric names, or leave columns constant-zero — use a
  genuine tool or mark values null and document the limitation.
- Don't run the analyzed **applications**; only `compile` (SpotBugs) and, in Fase 6, run **tests**
  (JaCoCo) — nothing else.
- Don't silently treat non-building / no-test repos as `bugs=0` / `coverage=0`; missing ≠ zero.
- Don't hand-edit generated CSVs or `repos.json`; fix the producing phase and regenerate.
- Don't duplicate logic between the notebook and `src/`; promote shared logic into `src/`.
- Don't break the `repos.json` / dataset schema without updating every consumer and its test.
