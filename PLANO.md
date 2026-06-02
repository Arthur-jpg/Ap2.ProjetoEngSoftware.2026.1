# Plano — Pipeline de métricas de código OO (Java) com contribuição do Claude

## Context

Trabalho de Engenharia de Software (análise de métricas de código). Objetivo:
estudar a **qualidade de código gerado por IA (Claude)** em projetos **Java (OO)**.
Hipótese: se o Claude é contribuidor de um repositório, alguém pediu para ele
commitar → ele teve impacto real no projeto.

A **unidade de análise é a classe** (não o repo). Cada repo qualificado gera várias
linhas (uma por classe). Variáveis por classe:

- **Tamanho/volume:** LOC, CLOC
- **Complexidade:** WMC e **complexidade ciclomática (McCC)** agregada por classe
  (`McCC_avg`, `McCC_max`) — distinta do WMC (ver nota)
- **Acoplamento/interação:** CBO, RFC
- **Herança:** DIT
- **Coesão:** LCOM5
- **Composição/interface pública:** NM, NPM
- **Análise estática:** WarningMajor, Design Rules, Coupling Metric Rules,
  Documentation Metric Rules, Size Metric Rules
- **Variável resposta:** Number of bugs

> **Nota McCC:** no SourceMeter, McCC (McCabe) é por **método**. Como a unidade é a
> classe, agregamos: `McCC_avg` (média) e `McCC_max` (máximo). É **distinto do
> WMC**, que é a *soma* das complexidades ciclomáticas dos métodos da classe.

## Decisões tomadas

- **Métricas:** SourceMeter (gera tudo, exceto bugs, num run sobre o **fonte**).
- **Detecção do Claude:** dois sinais — (A) mensagem de commit com
  `Co-Authored-By: Claude <noreply@anthropic.com>`; (B) autor/committer com email
  `@anthropic.com` ou nome "Claude". Repo qualifica se QUALQUER commit casar A ou B.
- **Number of bugs:** **SpotBugs** (sobre bytecode). Source-based (PMD/Sonar)
  descartado.
- **Seleção dos repos (nesta ordem):** (1) Java; (2) tem Claude; (3) os **10 com
  mais estrelas** entre os que sobram.
- **Unidade:** TODAS as classes de cada repo qualificado.
- **Ambiente:** **Docker** (container Linux) — roda igual no macOS e no Windows
  (Docker Desktop + WSL2).
- **Escala:** exatamente **10 repos**.

## Compilar vs. executar (importante)

- **SourceMeter:** analisa só o **fonte**. Não compila nem executa.
- **SpotBugs:** precisa do **bytecode** → `mvn compile` / `gradle compileJava`.
  **Nunca** executa o app.
- O pipeline **nunca roda os projetos**; a única etapa que compila é a do SpotBugs.

## Riscos

- **SourceMeter é antigo (~2019):** pode falhar em Java 17+ (records, sealed). Ele
  tolera erro por arquivo; na curadoria, preferir repos parseáveis.
- **SpotBugs exige compilar:** repos que não buildam não geram Number of bugs.
  Priorizar, entre os 10, os que compilam limpo.
- **GitHub Search Commits API:** exige `GITHUB_TOKEN` e tem rate limit (~30 req/min).
- **Join de nomes:** normalizar classes internas/anônimas entre SourceMeter e SpotBugs.

## Estrutura do projeto

```
projetoAp2/
├── PLANO.md                  # este documento
├── docker/
│   ├── Dockerfile            # JDK 17 + Maven + Gradle + Python3 + SourceMeter + SpotBugs
│   └── entrypoint.sh
├── tools/
│   ├── SourceMeter/          # binário Linux (download manual; ver README)
│   └── spotbugs/             # SpotBugs CLI
├── src/
│   ├── config.py             # regex do Claude, mapa de colunas, paths
│   ├── github_discovery.py   # Fase 1
│   ├── clone_build.py        # Fase 2
│   ├── run_sourcemeter.py    # Fase 3
│   ├── run_spotbugs.py       # Fase 4
│   ├── build_dataset.py      # Fase 5
│   ├── utils.py              # logging, normalização de nomes, subprocess
│   └── main.py               # orquestra, com flag --fase para rodar uma por vez
├── data/
│   ├── repos.json
│   ├── raw/<owner>__<repo>/  # saídas brutas SourceMeter + SpotBugs
│   └── dataset.csv           # FINAL: uma linha por classe
├── tests/                    # checagens por fase
├── notebooks/analise.ipynb   # (opcional) análise estatística posterior
├── requirements.txt          # requests, pandas, python-dotenv, lxml
├── .env.example              # GITHUB_TOKEN=
└── run.sh                    # build da imagem + docker run com volume em ./data
```

---

# Fases executáveis (rodar e testar uma de cada vez)

Cada fase: **objetivo → o que implementar → saída → como testar (critério de aceite)**.
Rodar via `python src/main.py --fase N`. Só avança quando o teste da fase passar.

## Fase 0 — Setup do ambiente (Docker + deps)
- **Implementar:** `docker/Dockerfile`, `requirements.txt`, `.env.example`,
  `run.sh`, `src/config.py`. Documentar download do SourceMeter no README.
- **Saída:** imagem Docker construída; `GITHUB_TOKEN` carregado do `.env`.
- **Testar:** `docker build` conclui; dentro do container, `java -version`,
  `mvn -v`, `python --version`, SourceMeter e SpotBugs respondem. Critério: todos
  respondem sem erro.

## Fase 1 — Descoberta de repos (`src/github_discovery.py`)
- **Implementar:** Search Commits API pelos dois sinais; agregar por repo;
  confirmar `language == Java`; ordenar por `stargazers_count` desc; pegar os **10**.
- **Saída:** `data/repos.json` (owner, repo, default_branch, stars, sinais).
- **Testar:** `repos.json` com 10 entradas, todas Java, todas com flag de Claude,
  ordenadas por estrelas. Validação automática em `tests/`.

## Fase 2 — Clone & build (`src/clone_build.py`)
- **Implementar:** `git clone` do default branch; confirmar Claude via `git log`;
  detectar build (Maven/Gradle) e rodar **apenas `compile`**; registrar `build_ok`.
- **Saída:** repos em `data/raw/...`; `repos.json` com `claude_confirmed`, `build_ok`.
- **Testar:** 10 clonados; `claude_confirmed=true`; relatório de `build_ok`.

## Fase 3 — SourceMeter (`src/run_sourcemeter.py`)
- **Implementar:** rodar `SourceMeterJava` no fonte; coletar `*-Class.csv`
  (métricas-alvo) e `*-Method.csv` (McCC por método).
- **Saída:** CSVs em `data/raw/<repo>/sourcemeter/`.
- **Testar:** `*-Class.csv` contém colunas-alvo; `*-Method.csv` contém McCC.

## Fase 4 — SpotBugs (`src/run_spotbugs.py`)
- **Implementar:** rodar SpotBugs (`-textui -xml:withMessages`) nas classes
  compiladas (`build_ok=true`); parsear XML; contar bugs por classe.
- **Saída:** `data/raw/<repo>/spotbugs.xml` + `bugs_por_classe.csv`.
- **Testar:** soma das contagens por classe == total de `<BugInstance>` no XML.

## Fase 5 — Dataset final (`src/build_dataset.py`)
- **Implementar:** agregar `*-Method.csv` → `McCC_avg`, `McCC_max`; join com
  `*-Class.csv`; join com SpotBugs (classes sem bug → 0); coluna `repo`; concatenar.
- **Saída:** `data/dataset.csv` — **uma linha por classe**.
- **Testar:** (a) uma linha por classe; (b) colunas-alvo presentes e numéricas;
  (c) `Number of bugs` com zeros e valores >0; (d) `McCC_avg`/`McCC_max` ≠ WMC.

---

## Verificação end-to-end
1. Rodar `main.py` para **1 repo** ponta a ponta (build → SourceMeter → SpotBugs →
   linha no dataset).
2. Rodar as 5 fases para os 10 repos; validar sanidade do `dataset.csv`.
3. **Cross-OS:** a dupla (Windows/WSL2) roda `run.sh` e obtém o mesmo `dataset.csv`.

## Fora de escopo
- A análise estatística/modelagem (regressão de Number of bugs etc.).
- Download do binário do SourceMeter (manual; documentado no README).
