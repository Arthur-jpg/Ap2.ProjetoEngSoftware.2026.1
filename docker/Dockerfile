# Base JDK 21 (jammy/Ubuntu 22.04, Python 3.10 — wheels estáveis p/ pandas).
# JDK 21 é o mais compatível: todos os wrappers Gradle (7.4–8.10) e o Tycho
# rodam nele; nenhum suporta JDK 25 ainda (class file major 69).
# JDK 25 é instalado À PARTE (abaixo) só para repos que compilam release 25.
# Ver docs/decisions/00-fase2-builds-triagem.md.
FROM eclipse-temurin:21-jdk-jammy

# JDK 25 secundário, copiado da imagem oficial. Usado por repos release-25.
COPY --from=eclipse-temurin:25-jdk-jammy /opt/java/openjdk /opt/java/jdk25
ENV JAVA21_HOME=/opt/java/openjdk
ENV JAVA25_HOME=/opt/java/jdk25

RUN apt-get update && apt-get install -y \
    git \
    maven \
    wget \
    unzip \
    python3 \
    python3-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Gradle
ENV GRADLE_VERSION=8.7
RUN wget -q https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip \
    && unzip -q gradle-${GRADLE_VERSION}-bin.zip -d /opt \
    && rm gradle-${GRADLE_VERSION}-bin.zip
ENV PATH="/opt/gradle-${GRADLE_VERSION}/bin:${PATH}"

# SpotBugs 4.10.x — necessário para analisar bytecode Java 25 (BCEL atualizado).
# Versões < 4.9.7 não leem class files compilados para Java 25.
ENV SPOTBUGS_VERSION=4.10.2
RUN wget -q https://github.com/spotbugs/spotbugs/releases/download/${SPOTBUGS_VERSION}/spotbugs-${SPOTBUGS_VERSION}.tgz \
    && tar -xzf spotbugs-${SPOTBUGS_VERSION}.tgz -C /opt \
    && rm spotbugs-${SPOTBUGS_VERSION}.tgz
ENV SPOTBUGS_HOME=/opt/spotbugs-${SPOTBUGS_VERSION}
ENV PATH="${SPOTBUGS_HOME}/bin:${PATH}"

# CK — motor de métricas OO (Aniche). Download automatizado do Maven Central
# (substitui o download manual do SourceMeter). Ver docs/decisions/03-metricas-ck.md.
ENV CK_VERSION=0.7.0
ENV CK_JAR=/opt/ck/ck.jar
RUN mkdir -p /opt/ck \
    && wget -q "https://repo1.maven.org/maven2/com/github/mauricioaniche/ck/${CK_VERSION}/ck-${CK_VERSION}-jar-with-dependencies.jar" \
       -O "${CK_JAR}"

WORKDIR /app

# venv isolado (PEP 668: não instalar deps no Python do sistema).
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:${PATH}"

COPY requirements.txt .
RUN . "$VIRTUAL_ENV/bin/activate" && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# A imagem base (eclipse-temurin) tem um ENTRYPOINT próprio
# (/__cacert_entrypoint.sh) que falha ao receber args como `--fase 1`.
# Resetamos o ENTRYPOINT para o nosso, de modo que os args do `docker run`
# (ex.: --fase 1) sejam anexados ao main.py e lidos pelo argparse.
# 'python' é o do venv (via PATH).
ENTRYPOINT ["python", "src/main.py"]
CMD []
