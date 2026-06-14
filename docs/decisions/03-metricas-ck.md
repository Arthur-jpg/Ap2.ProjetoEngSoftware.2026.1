# Decisão 03 — Métricas OO com o CK

## Por quê

A unidade de análise é a **classe**, e o estudo precisa de métricas OO *reais*
(não aproximações). Avaliamos três opções:

- **SourceMeter** (plano original): gera todas as métricas, mas é antigo (~2019),
  exige download manual e é frágil em Java 17+ (records, sealed). Ameaça à
  reprodutibilidade e à validade interna.
- **javalang** (ramo `feat/alternativo`): reimplementação em Python cujas métricas
  eram *proxies* que não correspondiam aos nomes (CBO = nº de imports; DIT = 0/1;
  LCOM5 caseiro; violações zeradas). Inválido para um estudo de métricas.
- **CK** (Aniche) — **escolhido**: ferramenta consolidada e citável que computa as
  métricas de Chidamber & Kemerer de verdade, roda sobre o **fonte** (não compila),
  suporta Java 17 e tem distribuição automatizável (Maven Central).

## Como

- CK **0.7.0**, jar `ck-0.7.0-jar-with-dependencies.jar`, baixado no `Dockerfile`
  do Maven Central (env `CK_JAR=/opt/ck/ck.jar`).
- Invocação (`src/run_sourcemeter.py:ck_command`):
  `java -jar ck.jar <repo> false 0 false <out>/` → gera `class.csv` e `method.csv`
  em `data/raw/<repo>/ck/`.
- Mapa de colunas (`src/config.py`) usa os **cabeçalhos verbatim** do CK 0.7.0
  (verificados em `ResultWriter.java`): `cbo, dit, rfc, wmc, lcom, lcom*, noc, loc,
  totalMethodsQty, publicMethodsQty`.

### Colunas e seus significados / referências

| dataset | CK | métrica | referência |
|---|---|---|---|
| LOC | loc | linhas de código | — |
| WMC | wmc | soma da complexidade ciclomática | McCabe 1976 |
| McCC_avg/max | method.csv `wmc` agregado | complexidade por método | McCabe 1976 |
| CBO | cbo | acoplamento entre objetos | Chidamber & Kemerer 1994 |
| RFC | rfc | response for a class | Chidamber & Kemerer 1994 |
| DIT | dit | profundidade de herança | Chidamber & Kemerer 1994 |
| NOC | noc | número de filhos | Chidamber & Kemerer 1994 |
| LCOM | lcom | falta de coesão (original) | Chidamber & Kemerer 1994 |
| LCOM_norm | lcom* | LCOM normalizado 0–1 | Henderson-Sellers 1996 |
| NM / NPM | totalMethodsQty / publicMethodsQty | nº de métodos (total/públicos) | — |

## O que foi rejeitado / removido

- **CLOC** (linhas de comentário): o CK **não** produz essa métrica → removida do
  schema (não inventada/zerada).
- **WarningMajor, RuleViolations_Design/Coupling/Documentation/Size**: eram do
  SourceMeter; o CK não emite violações de regra → **removidas**, não zeradas.
  Se forem necessárias no futuro, virão de um linter dedicado (PMD/Checkstyle) em
  fase própria e explicitamente citada.
- **"LCOM5 (Hitz & Montazeri)"**: rótulo incorreto do plano original. A métrica
  normalizada do CK é o **LCOM\*** de Henderson-Sellers; renomeada honestamente
  para `LCOM_norm`.

## Testes

`tests/test_config_schema.py` (schema só com colunas reais do CK; sem colunas do
SourceMeter; `lcom*`→`LCOM_norm`); `tests/test_ck_command.py` (forma do comando).

## Referências

Ver `docs/refs.bib`: `ck1994`, `mccabe1976`, `hendersonsellers1996`, `aniche-ck`.
