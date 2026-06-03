FROM eclipse-temurin:17-jdk

RUN apt-get update && apt-get install -y \
    git \
    maven \
    wget \
    unzip \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Gradle
ENV GRADLE_VERSION=8.7
RUN wget -q https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip \
    && unzip -q gradle-${GRADLE_VERSION}-bin.zip -d /opt \
    && rm gradle-${GRADLE_VERSION}-bin.zip
ENV PATH="/opt/gradle-${GRADLE_VERSION}/bin:${PATH}"

# SpotBugs
ENV SPOTBUGS_VERSION=4.8.6
RUN wget -q https://github.com/spotbugs/spotbugs/releases/download/${SPOTBUGS_VERSION}/spotbugs-${SPOTBUGS_VERSION}.tgz \
    && tar -xzf spotbugs-${SPOTBUGS_VERSION}.tgz -C /opt \
    && rm spotbugs-${SPOTBUGS_VERSION}.tgz
ENV SPOTBUGS_HOME=/opt/spotbugs-${SPOTBUGS_VERSION}
ENV PATH="${SPOTBUGS_HOME}/bin:${PATH}"

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# tools/ e data/ são montados em runtime via -v
# SourceMeter: esperado em /app/tools/SourceMeter/ (download manual)
ENV SOURCEMETER_HOME=/app/tools/SourceMeter
ENV PATH="${SOURCEMETER_HOME}:${PATH}"

CMD ["python3", "src/main.py"]
