#!/bin/bash
# OpenClaw Git Checkpoint System
# Usage: ./checkpoint.sh before "major-refactor"
#        ./checkpoint.sh complete "major-refactor"

set -euo pipefail

ACTION=$1
NAME=$2
BRANCH=$(git rev-parse --abbrev-ref HEAD)
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

if [ "$ACTION" == "before" ]; then
    TAG="checkpoint-before-${NAME}-${TIMESTAMP}"
    git add -A
    git commit -m "checkpoint: before ${NAME} [auto]" || true
    git tag -a "$TAG" -m "Checkpoint before: ${NAME}"
    git push origin "$TAG"
    echo "Checkpoint created: $TAG"
elif [ "$ACTION" == "complete" ]; then
    TAG="checkpoint-complete-${NAME}-${TIMESTAMP}"
    git add -A
    git commit -m "checkpoint: complete ${NAME} [auto]" || true
    git tag -a "$TAG" -m "Checkpoint complete: ${NAME}"
    git push origin "$TAG"
    echo "Checkpoint created: $TAG"
else
    echo "Usage: $0 {before|complete} <change-name>"
    exit 1
fi
