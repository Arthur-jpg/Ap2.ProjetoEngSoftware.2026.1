# Decisão 05 — Montagem do dataset (Fase 5)

## Por quê

O dataset final tem **uma linha por classe** com todas as métricas + a variável
resposta, pronto para a análise estatística. Precisa juntar três fontes por classe:
CK `class.csv`, CK `method.csv` (complexidade por método) e bugs do SpotBugs.

## Como (`src/build_dataset.py`)

1. **McCC por classe** (`mccc_per_class`): agrega o `wmc` por método do CK em
   `McCC_avg` (média) e `McCC_max` (máximo). São **distintos do WMC** de classe,
   que é a *soma* (McCabe 1976) — verificado em teste.
2. **Join método→classe e bugs→classe** pelo **nome de classe completo** do CK
   (não o nome simples), evitando colisões entre classes homônimas de pacotes
   diferentes.
3. **Bugs** (`join_bugs`): mapeia contagem por classe; classes sem registro ficam
   **NaN**. Repos não analisados pelo SpotBugs (`_load_bugs` → None) têm a coluna
   inteira como NaN. **Ausência ≠ zero.**
4. Adiciona `repo` e concatena todos os repos em `data/dataset.csv`.

## O que foi rejeitado

- O ramo `feat/alternativo` fazia `fillna(0)` nos bugs e juntava pelo nome
  **simples** da classe — ambos corrigidos aqui (NaN para ausente; join por nome
  completo).

## Testes

`tests/test_build_dataset.py`: McCC avg/max corretos; McCC ≠ WMC; bug ausente = NaN
(não 0); uma linha por classe preservada.

## Referências

`docs/refs.bib`: `mccabe1976`. Interpretação da variável resposta: `subramanyam2003`,
`dambros2012`.
