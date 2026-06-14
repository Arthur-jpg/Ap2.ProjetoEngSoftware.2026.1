# Decisão 01 — Seleção dos repositórios

## Por quê

O estudo precisa de uma amostra de repositórios **Java** com contribuição real do
**Claude**, e — como a variável resposta é *Number of bugs* via SpotBugs (que exige
bytecode) — os repos precisam **compilar**. A unidade de análise é a classe.

## Regra de seleção (build-aware top-by-stars)

1. Linguagem primária = **Java**.
2. Tem sinal de contribuição do Claude (ver `02-deteccao-claude.md`).
3. Entre os que sobram, os de **mais estrelas** — **exigindo que compilem**, para que
   SpotBugs/bugs funcionem. Repos que não compilam enfraquecem a variável resposta.
4. Tamanho-alvo da amostra: **10 repos**.

Diferença em relação ao plano original: o plano usava "top-10 por estrelas" sem
porta de compilação. Adicionamos a **porta de compilação** porque o objetivo é
modelagem de bugs e bugs só existem para repos que buildam.

## Exclusão de repos Android (e substituição)

Dois repos da amostra inicial eram apps **Android** (`JackZho/android-library-system`,
`JackZho/MusicPlayer`). Foram **excluídos** por estarem fora da população de interesse
(código Java OO "padrão"): exigem o Android SDK (grande, sob licença) para compilar, e
SpotBugs sobre bytecode Android é não-padrão — misturariam código de app com a
população-alvo e inflariam a imagem Docker.

**Substituídos** por dois repos Java com sinal do Claude confirmado:

| Repo | Estrelas | Commits Claude (confirmado) |
|---|---|---|
| `apache/flink-agents` | 390 | 35 |
| `pulumi/pulumi-java` | 82 | 10 |

A amostra resultante (10 repos) está em `data/repos.json`, ordenada por estrelas.
`claude_confirmed`/`build_ok` dos novos repos são definidos ao rodar a Fase 2.

### Reprodutibilidade da curadoria (importante)

A Fase 1 **re-descobre do zero** e sobrescreve `repos.json`. Para a curadoria não
se perder a cada execução, ela é **codificada** (`src/config.py`):

- `EXCLUDE_REPOS` — full_names sempre removidos (os 2 Android).
- `PINNED_REPOS` — includes fixos sempre adicionados (`pulumi/pulumi-java`).
- Além disso, `github_discovery._is_android_via_api` inspeciona a árvore do repo e
  **exclui qualquer repo com `AndroidManifest.xml`** (não só os da lista), e
  `is_android_repo` também detecta o plugin `com.android` no build.gradle.

Assim, `./run.sh --fase 1` reproduz a amostra curada de forma determinística.
Testes: `tests/test_discovery_curation.py`.

## Ameaças à validade (resumo; detalhe em 08)

- **N pequeno (10)** e **viés de estrelas**: amostra não aleatória.
- A troca Android→Java muda o perfil de estrelas (entram repos maiores) — documentado.
- Confirmação do Claude é por sinal de commit; não medimos *quanto* do código é dele.

## Referências

`docs/refs.bib`: motivação métricas↔defeitos `subramanyam2003`, `basili1996`.
