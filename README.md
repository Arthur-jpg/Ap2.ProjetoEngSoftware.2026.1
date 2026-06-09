# Pipeline de Métricas de Qualidade — Código Java com IA (Claude)

Coleta repositórios Java onde o **Claude (Anthropic)** foi contribuidor, extrai métricas OO por classe e gera um dataset para análise estatística da qualidade do código produzido com assistência de IA.

---

## Como funciona

```
GitHub API → clone dos repos → extração de métricas → SpotBugs → dataset.csv → análise no notebook
   Fase 1        Fase 2              Fase 3              Fase 4      Fase 5
```

| Fase | O que faz | Saída |
|---|---|---|
| 1 | Busca repos Java com commits do Claude via API do GitHub | `data/repos.json` |
| 2 | Clona os 10 repos e tenta compilar (Maven/Gradle) | `data/raw/<repo>/` |
| 3 | Extrai métricas OO de cada `.java` (via `javalang`) | `Class.csv`, `Method.csv` |
| 4 | Conta bugs com SpotBugs (apenas repos compilados) | `spotbugs.xml`, `bugs_por_classe.csv` |
| 5 | Junta tudo em um dataset final | `data/dataset.csv` |

---

## Pré-requisitos

| Ferramenta | Observação |
|---|---|
| [Docker Desktop](https://www.docker.com/products/docker-desktop) | macOS ou Windows (WSL2) |
| [Git](https://git-scm.com/downloads) | Para clonar este repositório |
| [Python 3.11+](https://www.python.org/downloads) | Apenas para rodar o notebook de análise |
| Conta no GitHub | Para gerar o token de API |

---

## 1. Clonar o projeto

```bash
git clone https://github.com/<seu-usuario>/projetoAp2.git
cd projetoAp2
```

---

## 2. Configurar o token do GitHub

O pipeline usa a API do GitHub para buscar repositórios. Você precisa de um token de acesso pessoal.

1. Acesse: [github.com/settings/tokens](https://github.com/settings/tokens)
2. Clique em **"Generate new token (classic)"**
3. Marque o escopo `public_repo`
4. Copie o token gerado (começa com `ghp_...`)

Crie o arquivo `.env` na raiz do projeto:

```bash
# macOS / Linux
cp .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env
```

Edite o `.env` e coloque seu token:

```
GITHUB_TOKEN=ghp_seuTokenAqui
```

> O `.env` está no `.gitignore` e nunca será enviado ao GitHub.

---

## 3. Rodar o pipeline completo

Com o Docker Desktop aberto:

```bash
# macOS / Linux
chmod +x run.sh
./run.sh
```

```powershell
# Windows (PowerShell)
docker build -f docker/Dockerfile -t metrics-pipeline .
docker run --rm -v "${PWD}/data:/app/data" --env-file .env metrics-pipeline
```

O `run.sh` builda a imagem Docker e executa todas as fases em sequência. Fases já concluídas são puladas automaticamente.

---

## 4. Rodar fase por fase (opcional)

```bash
./run.sh --fase 1   # descoberta de repos
./run.sh --fase 2   # clone e build
./run.sh --fase 3   # extração de métricas OO
./run.sh --fase 4   # SpotBugs
./run.sh --fase 5   # dataset final
```

> A Fase 1 pode levar alguns minutos por causa do rate limit da API do GitHub. Os logs mostram o progresso em tempo real.

---

## 5. Rodar a análise estatística (notebook)

O notebook analisa o `data/dataset.csv` gerado pelo pipeline.

```bash
# Instale as dependências (uma vez)
pip install pandas matplotlib seaborn scipy scikit-learn statsmodels jupyter

# Abra o notebook
jupyter notebook notebooks/analise.ipynb
```

O notebook cobre:
- Estatística descritiva (média, mediana, DP, percentis)
- Histogramas e teste de normalidade (Kolmogorov-Smirnov)
- Detecção de outliers (critério IQR)
- **Code smells** por threshold (God Class, Alta Complexidade, Acoplamento Excessivo, etc.)
- **Complexidade ciclomática** (McCC\_avg e McCC\_max por classe)
- Matriz de correlação de Spearman
- **PCA + K-Means** (3 arquétipos de classes)
- Comparação entre repositórios

---

## 6. Testar cada fase

Os testes validam as saídas e rodam localmente (sem Docker):

```bash
pip install -r requirements.txt

python tests/test_fase1.py   # valida data/repos.json
python tests/test_fase2.py   # valida clone e build
python tests/test_fase3.py   # valida Class.csv e Method.csv
```

---

## Estrutura do projeto

```
projetoAp2/
├── docker/
│   ├── Dockerfile            # JDK 11 + Maven + Gradle + Python + SpotBugs
│   └── entrypoint.sh
├── src/
│   ├── main.py               # orquestrador (--fase N)
│   ├── github_discovery.py   # Fase 1
│   ├── clone_build.py        # Fase 2
│   ├── run_sourcemeter.py    # Fase 3 (extração via javalang)
│   ├── run_spotbugs.py       # Fase 4
│   ├── build_dataset.py      # Fase 5
│   ├── config.py             # caminhos e configurações
│   └── utils.py
├── notebooks/
│   └── analise.ipynb         # análise estatística completa
├── data/
│   ├── repos.json            # gerado na Fase 1
│   ├── raw/                  # dados brutos por repo
│   └── dataset.csv           # gerado na Fase 5
├── tests/
│   ├── test_fase1.py
│   ├── test_fase2.py
│   └── test_fase3.py
├── artigo.tex                # artigo científico com os resultados
├── run.sh                    # build Docker + execução do pipeline
├── requirements.txt
└── .env.example
```

---

## Métricas extraídas por classe

| Categoria | Métricas |
|---|---|
| Tamanho | LOC, CLOC |
| Complexidade | WMC, McCC\_avg, McCC\_max |
| Acoplamento | CBO, RFC |
| Herança | DIT |
| Coesão | LCOM5 |
| Interface | NM, NPM |
| Bugs | Number\_of\_bugs (SpotBugs, apenas repos compilados) |
