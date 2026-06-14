# Decisão 07 — Análise estatística

## Por quê

O dataset (`data/dataset.csv`, 11.459 classes × métricas OO + bugs) precisa de uma
análise que (a) caracterize o perfil estrutural do código de IA e (b) responda à
questão central: **métricas OO se relacionam com defeitos?** As escolhas estatísticas
seguem das propriedades dos dados.

## Como (`notebooks/analise.ipynb`)

Gerado por `notebooks/gen_notebook.py` e executado sobre o dataset real. Seções:

1. **Pré-processamento** — métricas reais do CK (`LOC, WMC, CBO, RFC, DIT, NOC,
   LCOM, LCOM_norm, NM, NPM, McCC_avg, McCC_max`). Não há colunas SourceMeter.
2. **Descritiva** — média/mediana/percentis; revela forte assimetria à direita.
3. **Normalidade (Kolmogorov–Smirnov)** — H0 normal **rejeitada** em todas as
   métricas (p≪0,05). Justifica métodos não paramétricos.
4. **Outliers (IQR)** — boxplots; classes extremas em uma minoria.
5. **Code smells por threshold** — God Class (WMC>20 & LCOM_norm>0,7), alta
   complexidade (McCC_max>10), acoplamento (CBO>14), tamanho (LOC>500), interface
   inchada (NPM>20). Limiares da literatura (Fowler 1999).
6. **McCC** — distribuição de McCC_avg/McCC_max, distintos do WMC (McCabe 1976).
7. **Correlação de Spearman entre métricas** — não paramétrica (dados não normais).
8. **Bugs × métricas (questão de pesquisa)** — Spearman de cada métrica vs
   `Number_of_bugs`, **só nas 1.771 classes de repos compilados** (NaN excluído).
9. **PCA + K-Means (k=3)** — arquétipos estruturais de classe.
10. **Comparação entre repositórios.**
11. **Síntese para o artigo.**

## Decisões-chave

- **Spearman, não Pearson:** dados assimétricos e não normais (seção 3). Spearman
  capta relação monotônica sem supor normalidade/linearidade.
- **Bugs: 0 vs NaN.** Classe de repo analisado sem achado = 0; classe de repo não
  compilado = NaN (excluída da análise de bugs). Sem isso, a correlação seria
  enviesada (só veria classes com bug). Ver `05-dataset-join.md` e `08`.
- **Correlação, não regressão preditiva.** Com N=10 repos e bugs moderadamente
  correlacionados, um modelo preditivo seria sobre-ajustado; ficamos no descritivo
  (Subramanyam & Krishnan 2003; D'Ambros 2012).

## Resultado principal (executado)

Sobre 1.771 classes (6 repos compilados): todas as métricas de
tamanho/complexidade/coesão correlacionam positiva e significativamente com bugs
(ρ≈0,20–0,31, p<10⁻¹⁷); **DIT** fraco (ρ≈0,05) e **NOC** não significativo (p≈0,60).
Figuras: `notebooks/*.png` (incl. `bugs_correlacao.png`).

## Reprodutibilidade

`python notebooks/gen_notebook.py` regenera o .ipynb; executar com
`jupyter nbconvert --execute` (cwd em `notebooks/`, lê `../data/dataset.csv`).

## Referências
`docs/refs.bib`: `mccabe1976`, `fowler1999`, `ck1994`, `subramanyam2003`,
`basili1996`, `dambros2012`.
