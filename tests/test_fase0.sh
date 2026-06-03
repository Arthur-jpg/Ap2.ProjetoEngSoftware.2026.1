#!/bin/bash
# Teste da Fase 0: verifica que todas as ferramentas estão disponíveis no container.
# Rodar de dentro do container Docker.

set -e

ERROS=0

check() {
    local label="$1"
    local cmd="$2"
    if eval "$cmd" > /dev/null 2>&1; then
        echo "[OK] $label"
    else
        echo "[FALHA] $label"
        ERROS=$((ERROS + 1))
    fi
}

echo "=== Teste Fase 0: ambiente ==="

check "java"      "java -version"
check "mvn"       "mvn -v"
check "gradle"    "gradle -v"
check "python3"   "python3 --version"
check "git"       "git --version"
check "spotbugs"  "spotbugs -version"

# SourceMeter: só verifica se existe o binário (download manual)
if [ -x "${SOURCEMETER_HOME}/SourceMeterJava" ]; then
    echo "[OK] SourceMeter"
else
    echo "[AVISO] SourceMeter não encontrado em ${SOURCEMETER_HOME}/SourceMeterJava"
    echo "        Faça o download em https://github.com/sed-inf-u-szeged/OpenStaticAnalyzer"
    echo "        e coloque o binário Linux em tools/SourceMeter/"
fi

if [ "$ERROS" -eq 0 ]; then
    echo ""
    echo "Fase 0: PASSOU"
    exit 0
else
    echo ""
    echo "Fase 0: FALHOU ($ERROS erro(s))"
    exit 1
fi
