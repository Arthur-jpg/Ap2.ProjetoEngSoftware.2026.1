# Decisão 09 — A dificuldade de compilar projetos Java feitos com IA

## Contexto e por que isto importa para a pesquisa

A variável resposta do estudo (*Number of bugs* via SpotBugs) só existe para repos
que **compilam** — SpotBugs analisa bytecode. Portanto, a taxa de compilação da
amostra é um fator de primeira ordem para a validade do estudo, não um mero detalhe
de engenharia. Este documento registra o que descobrimos ao tentar compilar 10
repositórios Java com contribuição do Claude, e por que isso foi surpreendentemente
difícil.

## A jornada (de 2/10 para 6/10)

| Etapa | builds OK | O que mudou |
|---|---|---|
| Inicial (JDK 17) | 2/10 | amostra original, com 2 apps Android |
| Curadoria | 3/10 | excluídos Android + 3 repos não-Java; backfill |
| Detecção de subdir | — | pulumi (`sdk/java`) e golf-api (`api`) passam a ser detectados |
| JDK 25 | 4/10 | conserta Maven release-25, **quebra** Gradle/Tycho |
| JDK 21 + retry-25 | **6/10** | JDK 21 default; retry em JDK 25 só p/ release-25 |

## Padrões de falha observados (e o que dizem sobre código de IA)

### 1. Versões de toolchain muito recentes e heterogêneas
O ecossistema Java contribuído por IA usa JDKs **muito novos e inconsistentes**:
- `adriandeleon/Editora`, `jbiscella/H-tchen-Mail`: exigem **release 25** (JDK 25).
- `tim-mila/golf-api`, `yksi7417/cross_asset_ems`: exigem **JDK 21**.
- `nxmatic/rke2lab`: enforcer exige **JDK 25 + Maven 3.9**.

Nenhum JDK único compila todos. Pior: **JDK novo demais quebra ferramentas de build
antigas** — wrappers Gradle 7.4–8.10 não suportam JDK 25 (`Unsupported class file
major version 69`), e o Tycho (OSGi) rejeita `JavaSE-25` e até `JavaSE-21`
(`cloudempiere/...searchindex` só conhecia um ambiente mais antigo).

> **Leitura para a pesquisa:** código gerado/assistido por IA tende a adotar a
> versão de linguagem *mais nova disponível no momento*, sem travar uma toolchain
> reprodutível. Isso gera projetos que compilam "na máquina do autor naquela semana"
> mas não num ambiente padronizado — um sintoma de baixa portabilidade/manutenção.

### 2. "Java" no GitHub ≠ projeto Java
3 repos rotulados "Java" pelo GitHub não eram projetos Java OO:
- `adamzwasserman/honest-code-traces`: livro multi-linguagem (~10 .java).
- `mechanicus01/programing`: repo de estudo (1 .java).
- `akrishnanDG/schematizer-skill`: Java só em fixtures de teste.

> **Leitura:** o rótulo de linguagem do GitHub é por contagem de bytes e engana em
> repos de IA, que frequentemente misturam docs/skills/exemplos. Exigimos
> `>= 20 .java + build file` para entrar na amostra.

### 3. Build files fora do raiz
`pulumi/pulumi-java` (build em `sdk/java/`) e `golf-api` (em `api/`) não têm build
no raiz — comum em monorepos. Resolvido com `find_build` (busca em subdiretórios,
ignorando fixtures).

### 4. Etapas de geração de código e reatores multi-módulo
- `pulumi/pulumi-java`: o compile falha porque falta gerar código gRPC
  (`pulumirpc.Provider`) antes — passo não acionado por `compileJava`.
- `apache/flink-agents`: reator multi-módulo onde um módulo e2e precisa de um
  `jar:tests` que o goal `compile` não produz.

> **Leitura:** projetos de IA raramente documentam o pipeline de build completo
> (codegen, ordem de módulos). O `mvn compile`/`gradle compileJava` "ingênuo" não
> basta, e o conhecimento de como buildar fica implícito.

## A solução de engenharia adotada (reprodutível)

1. **Dois JDKs na imagem** (`docker/Dockerfile`): base **JDK 21** (compatível com
   todos os wrappers Gradle e Tycho) + **JDK 25** copiado à parte.
2. **Seleção automática** (`clone_build._build`): tenta JDK 21; se o log indicar
   `release version 25 not supported`/`JavaSE-25` (`needs_jdk25_retry`), refaz com
   JDK 25. Não refaz em `major version 69` (Gradle velho p/ JDK novo).
3. **Detecção de build em subdiretório** (`find_build`), ignorando fixtures.
4. **Captura de `build.log`** por repo para diagnóstico.
5. **Curadoria reprodutível** (`config.EXCLUDE_REPOS`/`PINNED_REPOS`,
   `_is_android_via_api`, `select_final`).

## Estado final (3ª execução, 2026-06-14): 6/10 compilam

| Repo | build | Observação |
|---|---|---|
| Kyu-seok/CodeBite | ✅ (Gradle, JDK 21) | |
| yksi7417/cross_asset_ems | ✅ (Gradle, JDK 21) | |
| adriandeleon/Editora | ✅ (Maven, JDK 25 retry) | |
| jbiscella/H-tchen-Mail | ✅ (Maven, JDK 25 retry) | |
| tim-mila/golf-api | ✅ (Maven subdir `api`, JDK 21) | |
| shossain786/utem-core | ✅ (Maven, JDK 21) | |
| apache/flink-agents | ❌ | reator: falta `jar:tests` |
| pulumi/pulumi-java | ❌ | falta codegen gRPC |
| nxmatic/rke2lab | ❌ | exige Maven 3.9 |
| cloudempiere/...searchindex | ❌ | Tycho não aceita JavaSE-21/25 |

Os 4 que não compilam **entram no estudo com métricas do CK** (análise de fonte, não
exige build), porém com `Number_of_bugs = NaN` (ausente ≠ zero). Isso é tratado como
**ameaça à validade** (ver `08-threats-to-validity.md`): a variável resposta cobre 6
dos 10 repos.

## Conclusão para o artigo

A baixa taxa de compilação "pronta para uso" (inicialmente 20%, elevada a 60% com
esforço de engenharia não-trivial) é, ela própria, um **achado**: repositórios Java
com forte contribuição de IA tendem a (a) fixar versões de linguagem muito recentes
sem travar toolchain reprodutível, (b) misturar conteúdo não-Java sob o rótulo
"Java", e (c) depender de etapas de build implícitas (codegen, multi-módulo). Tudo
isso são sinais relevantes de **portabilidade e manutenibilidade** — exatamente as
dimensões que as métricas OO buscam capturar.

## Referências
`docs/refs.bib`: `basili1996`, `subramanyam2003` (métricas ↔ qualidade/manutenção).
