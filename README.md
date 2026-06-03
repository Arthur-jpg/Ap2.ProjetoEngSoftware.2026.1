# Pipeline de métricas de código OO — Java + Claude

Analisa repositórios Java onde o Claude é contribuidor, extrai métricas por classe
(SourceMeter) e conta bugs (SpotBugs), gerando `data/dataset.csv`.

---

## Índice

1. [Pré-requisitos](#1-pré-requisitos)
2. [Clonar o repositório](#2-clonar-o-repositório)
3. [Instalar o Docker Desktop](#3-instalar-o-docker-desktop)
4. [Criar o token do GitHub](#4-criar-o-token-do-github)
5. [Configurar o arquivo .env](#5-configurar-o-arquivo-env)
6. [Baixar o SourceMeter](#6-baixar-o-sourcemeter)
7. [Testar o ambiente (Fase 0)](#7-testar-o-ambiente-fase-0)
8. [Executar cada fase](#8-executar-cada-fase)
9. [Testar cada fase](#9-testar-cada-fase)
10. [Saídas geradas](#10-saídas-geradas)
11. [Métricas coletadas por classe](#11-métricas-coletadas-por-classe)

---

## 1. Pré-requisitos

| Ferramenta | Onde baixar | Observação |
|---|---|---|
| Git | https://git-scm.com/downloads | Para clonar o repositório |
| Docker Desktop | https://www.docker.com/products/docker-desktop | macOS ou Windows (WSL2) |
| Python 3.11+ | https://www.python.org/downloads | Só para rodar os testes localmente |
| Conta no GitHub | https://github.com | Para gerar o token de API |

---

## 2. Clonar o repositório

```bash
git clone https://github.com/<seu-usuario>/projetoAp2.git
cd projetoAp2
```

---

## 3. Instalar o Docker Desktop

### macOS

1. Acesse https://www.docker.com/products/docker-desktop e clique em **Download for Mac**
2. Abra o `.dmg` baixado e arraste o Docker para a pasta Aplicativos
3. Abra o Docker pelo Launchpad e aguarde o ícone da baleia aparecer na barra de status
4. Confirme que funcionou:
   ```bash
   docker --version
   ```

### Windows

1. Acesse https://www.docker.com/products/docker-desktop e clique em **Download for Windows**
2. Execute o instalador `.exe`
3. Durante a instalação, marque a opção **"Use WSL 2 instead of Hyper-V"** (recomendado)
4. Reinicie o computador se solicitado
5. Abra o Docker Desktop pela barra de tarefas
6. Confirme que funcionou no terminal (PowerShell ou CMD):
   ```powershell
   docker --version
   ```

> **Windows — se o WSL2 não estiver instalado:**
> Abra o PowerShell como administrador e rode:
> ```powershell
> wsl --install
> ```
> Reinicie e abra o Docker Desktop novamente.

---

## 4. Criar o token do GitHub

O pipeline usa a API do GitHub para buscar repositórios. Você precisa de um token de acesso pessoal.

1. Acesse: https://github.com/settings/tokens
2. Clique em **"Generate new token (classic)"**
3. Em **Note**, coloque um nome descritivo (ex: `pipeline-metricas`)
4. Em **Expiration**, escolha pelo menos 30 dias
5. Em **Select scopes**, marque apenas:
   - `public_repo` (leitura de repositórios públicos)
6. Clique em **"Generate token"**
7. **Copie o token gerado** — ele só aparece uma vez. Começa com `ghp_...`

---

## 5. Configurar o arquivo .env

Na raiz do projeto, crie o arquivo `.env` a partir do exemplo:

### macOS / Linux

```bash
cp .env.example .env
```

### Windows (PowerShell)

```powershell
Copy-Item .env.example .env
```

Abra o arquivo `.env` com qualquer editor de texto e substitua o valor:

```
GITHUB_TOKEN=ghp_seuTokenAqui123456
```

> O arquivo `.env` está no `.gitignore` — ele nunca será enviado ao GitHub.

---

## 6. Baixar o SourceMeter

O SourceMeter é a ferramenta que extrai as métricas de código das classes Java.
Ele precisa ser baixado manualmente (não tem redistribuição automática).

1. Acesse: https://github.com/sed-inf-u-szeged/OpenStaticAnalyzer/releases
2. Na versão mais recente, baixe o arquivo:
   - **Linux (macOS e Windows via Docker):** `OpenStaticAnalyzer-*-x64-linux.tar.gz`
3. Extraia o arquivo baixado
4. Dentro da pasta extraída, localize o executável `SourceMeterJava`
5. Copie **todo o conteúdo** da pasta extraída para `tools/SourceMeter/`

A estrutura deve ficar assim:

```
tools/
└── SourceMeter/
    ├── SourceMeterJava       ← executável principal
    ├── PMD/
    └── ...
```

> **Por que o arquivo Linux mesmo no Windows?**
> O pipeline roda dentro de um container Docker Linux. O Windows e o macOS só
> hospedam o Docker — o SourceMeter sempre roda no Linux do container.

---

## 7. Testar o ambiente (Fase 0)

Antes de rodar o pipeline, verifique se tudo está instalado corretamente.

### macOS / Linux

```bash
chmod +x run.sh
./run.sh bash tests/test_fase0.sh
```

### Windows (PowerShell)

```powershell
docker build -f docker/Dockerfile -t metrics-pipeline .
docker run --rm `
  -v "${PWD}/data:/app/data" `
  -v "${PWD}/tools:/app/tools" `
  --env-file .env `
  metrics-pipeline bash tests/test_fase0.sh
```

**Saída esperada:**

```
=== Teste Fase 0: ambiente ===
[OK] java
[OK] mvn
[OK] gradle
[OK] python3
[OK] git
[OK] spotbugs
[OK] SourceMeter       ← só aparece se você fez o passo 6

Fase 0: PASSOU
```

> Se alguma linha mostrar `[FALHA]`, revise o passo correspondente.

---

## 8. Executar cada fase

### macOS / Linux

```bash
./run.sh --fase 1   # Descoberta de repos no GitHub
./run.sh --fase 2   # Clone e compilação dos repos
./run.sh --fase 3   # Extração de métricas (SourceMeter)
./run.sh --fase 4   # Contagem de bugs (SpotBugs)
./run.sh --fase 5   # Geração do dataset final
```

Para rodar todas as fases em sequência:

```bash
./run.sh
```

### Windows (PowerShell)

Substitua `./run.sh --fase N` por:

```powershell
docker build -f docker/Dockerfile -t metrics-pipeline .
docker run --rm `
  -v "${PWD}/data:/app/data" `
  -v "${PWD}/tools:/app/tools" `
  --env-file .env `
  metrics-pipeline --fase 1
```

Troque `--fase 1` pelo número da fase desejada.

> **Dica:** a Fase 1 leva alguns minutos por causa do rate limit da API do GitHub
> (30 requisições/minuto). Os logs mostram o progresso em tempo real.

---

## 9. Testar cada fase

Após rodar cada fase, execute o teste correspondente para validar a saída.
Os testes rodam localmente (sem Docker), exigem Python 3.11+.

### Instalar dependências de teste (uma vez)

```bash
pip install -r requirements.txt
```

### Rodar os testes

```bash
python tests/test_fase1.py   # valida data/repos.json
```

> Testes das fases 2–5 serão adicionados conforme as fases forem implementadas.

---

## 10. Saídas geradas

| Arquivo | Gerado na fase | Descrição |
|---|---|---|
| `data/repos.json` | Fase 1 | 10 repos selecionados (Java + Claude + top estrelas) |
| `data/raw/<owner>__<repo>/` | Fases 2–4 | Saídas brutas do SourceMeter e SpotBugs |
| `data/dataset.csv` | Fase 5 | Dataset final: uma linha por classe |

---

## 11. Métricas coletadas por classe

| Categoria | Métricas |
|---|---|
| Tamanho/volume | LOC, CLOC |
| Complexidade | WMC, McCC_avg, McCC_max |
| Acoplamento | CBO, RFC |
| Herança | DIT |
| Coesão | LCOM5 |
| Composição/interface | NM, NPM |
| Análise estática | WarningMajor, Design Rules, Coupling Metric Rules, Documentation Metric Rules, Size Metric Rules |
| Variável resposta | Number of bugs |

Consulte `PLANO.md` para decisões de projeto e detalhes de cada fase.
