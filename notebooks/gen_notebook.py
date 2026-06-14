"""Gera notebooks/analise.ipynb adaptado ao dataset REAL do CK.

Diferenças vs. a versão antiga (feat/alternativo, métricas-proxy javalang):
- Schema real do CK: LCOM, LCOM_norm, NOC (não LCOM5; sem colunas SourceMeter).
- DIT real (não 0/1).
- NOVA seção de bugs: Number_of_bugs por classe — análise descritiva e
  correlação de Spearman métrica×bugs (a questão de pesquisa central), só nas
  classes de repos que compilaram (NaN = não analisado, excluído).
Rode: python notebooks/gen_notebook.py  → escreve notebooks/analise.ipynb
"""
import json
from pathlib import Path

OUT = Path(__file__).parent / "analise.ipynb"


def md(*lines):
    return {"cell_type": "markdown", "metadata": {}, "source": list(lines)}


def code(*lines):
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": list(lines)}


cells = [
    md("# Análise de Métricas de Qualidade — Código Java com Contribuição do Claude\n",
       "\n",
       "Dataset real extraído com a ferramenta **CK** (Chidamber & Kemerer 1994) + bugs do **SpotBugs**.\n",
       "Unidade de análise = a **classe**. Métricas OO genuínas (DIT, CBO, RFC, LCOM, LCOM\\* etc.),\n",
       "diferente da versão anterior baseada em proxies."),

    code("import warnings; warnings.filterwarnings('ignore')\n",
         "import numpy as np, pandas as pd\n",
         "import matplotlib.pyplot as plt, seaborn as sns\n",
         "from scipy import stats\n",
         "from sklearn.preprocessing import StandardScaler\n",
         "from sklearn.decomposition import PCA\n",
         "from sklearn.cluster import KMeans\n",
         "sns.set_style('whitegrid'); ALPHA = 0.05"),

    md("## 1. Carregamento e pré-processamento"),
    code("df_raw = pd.read_csv('../data/dataset.csv')\n",
         "print('Shape:', df_raw.shape)\n",
         "print('Repos:', df_raw['repo'].nunique())\n",
         "df_raw.head()"),
    code("# Métricas OO reais do CK (sem colunas de identificação nem a resposta).\n",
         "METRICAS = ['LOC','WMC','CBO','RFC','DIT','NOC','LCOM','LCOM_norm','NM','NPM','McCC_avg','McCC_max']\n",
         "METRICAS = [c for c in METRICAS if c in df_raw.columns]\n",
         "# df_m: base de métricas (todas as classes); McCC pode faltar p/ classe sem método.\n",
         "df = df_raw.copy()\n",
         "print('Classes:', len(df), '| Métricas:', len(METRICAS))"),

    md("## 2. Estatística descritiva"),
    code("desc = df[METRICAS].describe(percentiles=[.25,.5,.75,.90,.95]).T\n",
         "desc.round(2)"),

    md("## 3. Distribuição e normalidade (Kolmogorov–Smirnov)\n",
       "H0: distribuição normal. Esperamos rejeitar (dados de software são assimétricos)."),
    code("PLOT = [c for c in ['LOC','WMC','CBO','RFC','DIT','LCOM_norm','McCC_avg','McCC_max'] if c in df.columns]\n",
         "fig, axes = plt.subplots(2, 4, figsize=(16, 7)); axes = axes.flatten()\n",
         "for i, col in enumerate(PLOT):\n",
         "    d = df[col].dropna()\n",
         "    axes[i].hist(d, bins=40, color='steelblue', alpha=0.8, density=True, edgecolor='white')\n",
         "    axes[i].set_title(col); axes[i].set_ylabel('Densidade')\n",
         "for j in range(len(PLOT), len(axes)): axes[j].set_visible(False)\n",
         "plt.suptitle('Histogramas das métricas'); plt.tight_layout()\n",
         "plt.savefig('normalidade.png', bbox_inches='tight'); plt.show()"),
    code("ks = []\n",
         "for col in METRICAS:\n",
         "    d = df[col].dropna()\n",
         "    stat, pval = stats.kstest(d, 'norm', args=(d.mean(), d.std()))\n",
         "    ks.append({'Variável': col, 'D': round(stat,4), 'p': f'{pval:.1e}',\n",
         "               'Normal?': 'Não' if pval < ALPHA else 'Sim'})\n",
         "pd.DataFrame(ks).set_index('Variável')"),

    md("## 4. Outliers (critério IQR)"),
    code("fig, axes = plt.subplots(2, 4, figsize=(16, 7)); axes = axes.flatten()\n",
         "for i, col in enumerate(PLOT):\n",
         "    axes[i].boxplot(df[col].dropna(), vert=True); axes[i].set_title(col)\n",
         "for j in range(len(PLOT), len(axes)): axes[j].set_visible(False)\n",
         "plt.suptitle('Boxplots (IQR)'); plt.tight_layout()\n",
         "plt.savefig('boxplot.png', bbox_inches='tight'); plt.show()"),

    md("## 5. Code smells por threshold (literatura CK / Fowler 1999)"),
    code("smells = {\n",
         "    'God Class\\n(WMC>20 & LCOM_norm>0.7)': ((df['WMC']>20) & (df['LCOM_norm']>0.7)).sum(),\n",
         "    'Alta Complexidade\\n(McCC_max>10)':      (df['McCC_max']>10).sum(),\n",
         "    'Acopl. Excessivo\\n(CBO>14)':            (df['CBO']>14).sum(),\n",
         "    'Classe Grande\\n(LOC>500)':              (df['LOC']>500).sum(),\n",
         "    'Interface Inchada\\n(NPM>20)':           (df['NPM']>20).sum(),\n",
         "}\n",
         "fig, ax = plt.subplots(figsize=(10,4))\n",
         "vals = list(smells.values()); pcts = [v/len(df)*100 for v in vals]\n",
         "bars = ax.bar(list(smells.keys()), pcts, color='steelblue', alpha=0.8, edgecolor='white')\n",
         "for b,v,p in zip(bars, vals, pcts):\n",
         "    ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.05, f'{v}\\n({p:.1f}%)', ha='center', va='bottom', fontsize=9)\n",
         "ax.set_ylabel('% das classes'); ax.set_title('Code smells (thresholds da literatura)')\n",
         "plt.tight_layout(); plt.savefig('code_smells.png', bbox_inches='tight'); plt.show()\n",
         "smells"),

    md("## 6. Complexidade ciclomática (McCC) — McCabe 1976\n",
       "McCC_avg/McCC_max são distintos do WMC (soma)."),
    code("fig, axes = plt.subplots(1, 3, figsize=(14,4))\n",
         "for ax, col in zip(axes, ['McCC_avg','McCC_max','WMC']):\n",
         "    axes_d = df[col].dropna()\n",
         "    ax.hist(axes_d, bins=40, color='indianred', alpha=0.8, edgecolor='white'); ax.set_title(col)\n",
         "plt.suptitle('McCC vs WMC'); plt.tight_layout()\n",
         "plt.savefig('mccc.png', bbox_inches='tight'); plt.show()"),

    md("## 7. Correlação de Spearman entre métricas\n",
       "Spearman (não paramétrico) porque os dados não são normais (seção 3)."),
    code("corr = df[METRICAS].corr(method='spearman')\n",
         "mask = np.triu(np.ones_like(corr, dtype=bool))\n",
         "fig, ax = plt.subplots(figsize=(12,10))\n",
         "sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='RdYlGn', center=0, vmin=-1, vmax=1, ax=ax, annot_kws={'size':8}, linewidths=0.5)\n",
         "ax.set_title('Matriz de Correlação de Spearman'); plt.tight_layout()\n",
         "plt.savefig('correlacao.png', bbox_inches='tight'); plt.show()"),

    md("## 8. **Bugs vs. métricas — a questão de pesquisa central**\n",
       "Métricas OO predizem defeitos? (Subramanyam & Krishnan 2003; Basili 1996.)\n",
       "Usamos **só as classes de repos que compilaram** (Number_of_bugs não-NaN);\n",
       "classes não analisadas (build falhou) são NaN e ficam de fora."),
    code("built = df[df['Number_of_bugs'].notna()].copy()\n",
         "print(f'Classes com dado de bug: {len(built)} de {built[\"repo\"].nunique()} repos')\n",
         "print(f'Classes com >=1 bug: {(built.Number_of_bugs>0).sum()} | total de bugs: {int(built.Number_of_bugs.sum())}')\n",
         "built['Number_of_bugs'].describe()"),
    code("# Spearman de cada métrica vs Number_of_bugs\n",
         "rows = []\n",
         "for m in METRICAS:\n",
         "    sub = built[[m,'Number_of_bugs']].dropna()\n",
         "    rho, p = stats.spearmanr(sub[m], sub['Number_of_bugs'])\n",
         "    rows.append({'Métrica': m, 'rho': round(rho,3), 'p': f'{p:.1e}',\n",
         "                 'sig': '***' if p<0.001 else '**' if p<0.01 else '*' if p<0.05 else 'ns'})\n",
         "bug_corr = pd.DataFrame(rows).sort_values('rho', key=lambda s: s.abs(), ascending=False).set_index('Métrica')\n",
         "bug_corr"),
    code("fig, ax = plt.subplots(figsize=(9,5))\n",
         "bc = bug_corr.copy(); bc['rho'] = bc['rho'].astype(float)\n",
         "bc = bc.sort_values('rho')\n",
         "ax.barh(bc.index, bc['rho'], color=['seagreen' if x>0 else 'indianred' for x in bc['rho']])\n",
         "ax.axvline(0, color='k', lw=0.8); ax.set_xlabel('Spearman rho (métrica vs Number_of_bugs)')\n",
         "ax.set_title('Correlação métrica×bugs (classes de repos compilados)')\n",
         "plt.tight_layout(); plt.savefig('bugs_correlacao.png', bbox_inches='tight'); plt.show()"),

    md("## 9. PCA + Cluster (K-Means)"),
    code("dfc = df[METRICAS].dropna().copy()\n",
         "X = StandardScaler().fit_transform(dfc)\n",
         "pca = PCA(n_components=4); comp = pca.fit_transform(X)\n",
         "for i,v in enumerate(pca.explained_variance_ratio_):\n",
         "    print(f'  PC{i+1}: {v*100:.1f}% (acum {pca.explained_variance_ratio_[:i+1].sum()*100:.1f}%)')\n",
         "km = KMeans(n_clusters=3, random_state=42, n_init=10)\n",
         "lab = km.fit_predict(X)\n",
         "fig, ax = plt.subplots(figsize=(8,6))\n",
         "for k,c in zip(range(3), ['steelblue','tomato','seagreen']):\n",
         "    m = lab==k; ax.scatter(comp[m,0], comp[m,1], s=12, alpha=0.4, color=c, label=f'cluster {k}')\n",
         "ax.set_xlabel('PC1'); ax.set_ylabel('PC2'); ax.legend(); ax.set_title('PCA + K-Means (k=3)')\n",
         "plt.tight_layout(); plt.savefig('pca_clusters.png', bbox_inches='tight'); plt.show()"),

    md("## 10. Comparação entre repositórios"),
    code("cols_repo = [c for c in ['LOC','WMC','CBO','RFC','McCC_avg','LCOM_norm'] if c in df.columns]\n",
         "rs = df.groupby('repo')[cols_repo].mean().round(2); rs['n'] = df.groupby('repo').size()\n",
         "rs = rs.sort_values('WMC', ascending=False); rs"),

    md("## 11. Síntese para o artigo"),
    code("print('=== SÍNTESE ===')\n",
         "print(f'Classes: {len(df)} | Repos: {df.repo.nunique()}')\n",
         "print(f'Classes com bug data: {len(built)} | bugs totais: {int(built.Number_of_bugs.sum())}')\n",
         "print()\n",
         "print('Métricas (média / mediana / max):')\n",
         "for c in METRICAS:\n",
         "    s=df[c].dropna(); print(f'  {c:10s}: {s.mean():.2f} / {s.median():.0f} / {s.max():.0f}')\n",
         "print()\n",
         "print('Top correlações métrica×bugs:')\n",
         "print(bug_corr.head(6).to_string())"),
]

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
print(f"escrito: {OUT}  ({len(cells)} células)")
