#!/bin/bash
set -e
VERSION=${1:-latest}
IMAGE="jabastien/web-rsync"
docker buildx build --platform linux/amd64,linux/arm64 \
  -f backend/Dockerfile \
  -t "$IMAGE:$VERSION" -t "$IMAGE:latest" \
  --push .
