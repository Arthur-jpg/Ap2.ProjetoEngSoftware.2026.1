#!/bin/bash
set -e

IMAGE_NAME="metrics-pipeline"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "Erro: arquivo .env não encontrado. Copie .env.example para .env e preencha GITHUB_TOKEN."
    exit 1
fi

echo "Construindo imagem Docker..."
docker build --platform linux/amd64 -f "$SCRIPT_DIR/docker/Dockerfile" -t "$IMAGE_NAME" "$SCRIPT_DIR"

echo "Executando pipeline..."
docker run --rm --platform linux/amd64 \
    -v "$SCRIPT_DIR/data:/app/data" \
    --env-file "$SCRIPT_DIR/.env" \
    "$IMAGE_NAME" "$@"
