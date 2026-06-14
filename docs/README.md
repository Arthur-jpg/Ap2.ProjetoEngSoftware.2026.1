# docs/

Documentação de pesquisa do projeto. Cada parte da implementação tem um
explicador em `decisions/` com **por quê + como + referências**, atualizado na
mesma mudança que altera o código (regra do `CLAUDE.md`). As citações se acumulam
em `refs.bib`, reusado pelo artigo.

## Índice de decisões

| Doc | Tema | Status |
|---|---|---|
| `decisions/00-fase2-builds-triagem.md` | Como rodar Fase 2 + triagem de builds | ✅ |
| `decisions/01-selecao-repos.md` | Seleção dos repos (build-aware; exclusão Android) | ✅ |
| `decisions/02-deteccao-claude.md` | Sinais de detecção do Claude | ✅ |
| `decisions/03-metricas-ck.md` | Motor de métricas = CK (vs SourceMeter/javalang) | ✅ |
| `decisions/04-spotbugs-bugs.md` | Bugs por classe via SpotBugs | ✅ |
| `decisions/05-dataset-join.md` | Montagem do dataset (Fase 5) | ✅ |
| `decisions/06-jacoco-crap.md` | Cobertura (JaCoCo) + CRAP (Fase 6, reservada) | TODO |
| `decisions/07-analise-estatistica.md` | Spearman, KS, PCA/clusters, bugs×métricas | ✅ |
| `decisions/08-threats-to-validity.md` | Ameaças à validade | ✅ |
| `decisions/09-dificuldade-build-projetos-ia.md` | Dificuldade de compilar projetos Java de IA | ✅ |

## Artigo

`artigo.tex` / `main.tex` (importados de `feat/alternativo`). **Números
desatualizados** (proxy javalang) — ver o cabeçalho de `artigo.tex` com a lista
do que refazer a partir de `data/dataset.csv` e `notebooks/analise.ipynb`. O
usuário finaliza o artigo. Bibliografia em `refs.bib`.

## Notebook

`notebooks/analise.ipynb` (gerado por `gen_notebook.py`, executado sobre o dataset
real). Figuras: `notebooks/*.png` (incl. `bugs_correlacao.png`, novo).
