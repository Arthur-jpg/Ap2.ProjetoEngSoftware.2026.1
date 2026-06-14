# Decisão 04 — Contagem de bugs com o SpotBugs

## Por quê

A variável resposta do estudo é **Number of bugs** por classe. Escolhemos o
**SpotBugs** (sucessor do FindBugs) por analisar **bytecode**, o que detecta
defeitos reais de implementação com menos falsos positivos que analisadores de
fonte (PMD/Sonar). Análise sobre fonte foi descartada no plano.

## Como

- `src/run_spotbugs.py:spotbugs_command` →
  `java -jar spotbugs.jar -textui -xml:withMessages -output <xml> <classes_dir>`.
- `find_classes_dir` localiza o bytecode compilado (Maven `target/classes`,
  Gradle `build/classes/java/main`).
- A contagem por classe é feita na Fase 5 a partir do XML
  (`src/spotbugs_parse.py:count_bugs_by_class`), que garante o critério de aceite:
  **a soma das contagens por classe == nº de `<BugInstance>`** com classe associada.
- Classes internas/anônimas (`Foo$Bar`) são colapsadas para a classe externa
  (`utils.normalize_class_name`) para casar com a saída do CK.

## Decisão-chave: ausência ≠ zero

SpotBugs exige bytecode; repos com `build_ok=false` **não** geram XML. Na Fase 5,
essas classes ficam com `Number_of_bugs = NaN` (**ausente**), nunca `0`. Tratar
"não analisado" como "zero bugs" enviesaria a variável resposta. Ver
`docs/decisions/05-dataset-join.md` e `08-threats-to-validity.md`.

## Multi-módulo: analisar TODOS os diretórios de classes

`find_classes_dirs` (`run_spotbugs.py`) retorna **todos** os raízes de bytecode
(`target/classes`, `build/classes/java/main`) de todos os módulos — não desce em
subpacotes. Correção de um bug que subcontava bugs: a versão anterior pegava só o
1º diretório com `.class` (um subpacote raso), então o SpotBugs analisava uma
fração das classes. Ex.: `cross_asset_ems` tem **13 módulos** (0 → 172 bugs após a
correção); `CodeBite` tem 3 (backend/common/worker). O SpotBugs recebe todos os
diretórios como alvos.

## Testes

`tests/test_spotbugs_parse.py` (soma == total de BugInstance; colapso de classe
interna; XML vazio → {}); `tests/test_spotbugs_command.py` (forma do comando;
`find_classes_dirs` retorna raiz, multi-módulo, não desce em pacotes).

## Referências

`docs/refs.bib`: `spotbugs`. Justificativa do uso de métricas/bugs: `subramanyam2003`.
