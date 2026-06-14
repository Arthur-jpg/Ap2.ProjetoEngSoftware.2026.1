# Nota P1 — Re-rodar a Fase 2 e triagem de builds

A correção de builds exige Docker (Maven/Gradle/JDK) — não roda na máquina local.
Esta nota descreve como rodar e como diagnosticar cada falha a partir dos logs.

## Como rodar (em Docker)

```bash
# .env precisa ter GITHUB_TOKEN=...
./run.sh --fase 1     # (re)descobre/atualiza repos.json — confirma os 2 repos novos
./run.sh --fase 2     # clona + compila os 10; grava build.log por repo
```

Saída por repo: `data/raw/<owner>__<repo>/build.log` (comando, exit code, stdout, stderr)
e flags `claude_confirmed` / `build_ok` atualizadas em `data/repos.json`.

> Os repos novos (`apache/flink-agents`, `pulumi/pulumi-java`) entram sem flags;
> a Fase 2 as preenche. Os 2 repos Android foram removidos da amostra
> (ver `01-selecao-repos.md`).

## O que mudou na Fase 2 (P1)

- `clone_build.detect_build_system` distingue **maven / gradle / android** (Android =
  Gradle + AndroidManifest.xml).
- `clone_build.build_command` escolhe o alvo: `mvn compile`, `gradle compileJava` ou
  `assembleDebug` (Android). Como Android foi excluído da amostra, o caminho Android
  não deve ser exercido — fica como salvaguarda.
- **Captura de log**: todo build grava `build.log` (antes só havia um booleano).

## Triagem da 1ª execução (2026-06-14) — 3/10 buildaram

| Repo | Resultado | Causa / ação |
|---|---|---|
| Kyu-seok/CodeBite | ✅ build OK (Gradle) | 820 .java |
| cloudempiere/...searchindex | ✅ build OK (Maven) | 42 .java |
| shossain786/utem-core | ✅ build OK (Maven) | 161 .java |
| apache/flink-agents | ❌ Maven | reator multi-módulo: módulo e2e-tests precisa de `jar:tests` que `compile` não gera. Toolchain não optado → **limitação documentada** |
| nxmatic/rke2lab | ❌ Maven | enforcer exige **JDK 25 + Maven 3.9**; imagem tem 17/3.6 → **limitação documentada** |
| pulumi/pulumi-java | ⚠️ "sem build file" no raiz | build real em `sdk/java/` (Gradle) → **corrigido** (find_build em subdir) |
| tim-mila/golf-api | ⚠️ "sem build file" no raiz | build em `api/` (Maven) → **corrigido** (find_build em subdir) |
| adamzwasserman/honest-code-traces | ❌ não-Java | livro multi-linguagem (~10 .java) → **excluído + backfill** |
| mechanicus01/programing | ❌ não-Java | 1 .java → **excluído + backfill** |
| akrishnanDG/schematizer-skill | ❌ não-Java | Java só em `test-repo/` (fixtures) → **excluído + backfill** |

### Correções aplicadas (TDD)
- **`find_build`** (`clone_build.py`): localiza build file no raiz OU em subdiretório
  (ignora fixtures `test-repo/testdata/...`). Resolve pulumi (`sdk/java`) e golf-api (`api`).
- **Curadoria** (`config.py`): 3 repos não-Java excluídos; backfill com 3 projetos Java
  reais (cross_asset_ems 506 .java, Editora 359, H-tchen-Mail 230). `select_final`
  garante os fixados na amostra final.

### 2ª execução (2026-06-14) — diagnóstico: maioria é versão de JDK

Com a amostra curada, as falhas restantes foram quase todas **incompatibilidade de
versão de JDK** (imagem tinha JDK 17; repos pedem 21/25):

| Repo | Erro | Precisa |
|---|---|---|
| adriandeleon/Editora | `release version 25 not supported` | JDK 25 |
| jbiscella/H-tchen-Mail | `release version 25 not supported` | JDK 25 |
| tim-mila/golf-api | `release version 21 not supported` | JDK 21 |
| yksi7417/cross_asset_ems | Gradle toolchain `languageVersion=21` | JDK 21 |
| nxmatic/rke2lab | enforcer: JDK 25 + Maven 3.9 | JDK 25 (+Maven) |
| pulumi/pulumi-java | falta código gerado (`pulumirpc.Provider`) | codegen, não JDK |
| apache/flink-agents | reator precisa de `jar:tests` | multi-módulo, não JDK |

### Correção: upgrade para JDK 25 + SpotBugs 4.10.2
- **`docker/Dockerfile`**: `FROM eclipse-temurin:25-jdk-jammy` (JDK 25 compila alvos
  release 21 e 25). **SpotBugs 4.10.2** (4.8.6 não lê bytecode Java 25 — BCEL antigo).
  CK 0.7.0 roda no JDK 25 (analisa fonte, não bytecode).
- Esperado pós-upgrade: Editora, H-tchen-Mail, golf-api compilam; cross_asset_ems
  provável (Gradle acha o JDK 25).

### 3ª execução (2026-06-14): JDK 25 quebrou os repos Gradle/Tycho

JDK 25 consertou os Maven release-25 (Editora, H-tchen-Mail ✅) mas **quebrou**:
- **Gradle** (CodeBite, cross_asset_ems, pulumi): wrappers 7.4–8.10 não suportam
  JDK 25 → `Unsupported class file major version 69`.
- **searchindex** (Tycho/OSGi): `Unknown OSGi execution environment: JavaSE-25`.

Nenhum JDK único serve a todos. **Solução (dois JDKs + retry):**
- Imagem base = **JDK 21** (compatível com todos os wrappers Gradle e Tycho;
  compila release 21). JDK 25 instalado à parte (`/opt/java/jdk25`).
- `clone_build._build` tenta com **JDK 21**; se o log indicar `release version 25
  not supported`/`JavaSE-25` (`needs_jdk25_retry`), refaz com **JDK 25**.
- NÃO refaz em `major version 69` (isso é Gradle velho p/ JDK novo — retry pioraria).

Esperado: JDK 21 recupera CodeBite, cross_asset_ems, searchindex; retry-25 cobre
Editora, H-tchen-Mail; golf-api (release 21) e utem-core seguem OK → ~7/10.

### Limitações que persistem (não-JDK)
- `pulumi/pulumi-java`: falta etapa de geração de código gRPC antes do compile.
- `apache/flink-agents`: reator multi-módulo precisa de test-jar.
- `rke2lab`: exige Maven 3.9 (jammy tem 3.6.3) além do enforcer.
- Esses entram com **CK (métricas)** mas `Number_of_bugs` = NaN. Documentar em
  `08-threats-to-validity.md`.

Depois de re-rodar `--fase 1` e `--fase 2`, **me envie os `build.log`** dos novos repos
(cross_asset_ems, Editora, H-tchen-Mail) e de pulumi/golf-api para confirmar.
```
