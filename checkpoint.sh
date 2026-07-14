#!/bin/bash
# CHECKPOINT SYSTEM
# OpenClaw Digital Empire — Git Checkpoints
# Usage: ./checkpoint.sh [before|after] [change-name]

ACTION=$1
CHANGE_NAME=$2
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [ -z "$ACTION" ] || [ -z "$CHANGE_NAME" ]; then
    echo "Usage: ./checkpoint.sh [before|after] [change-name]"
    exit 1
fi

if [ "$ACTION" == "before" ]; then
    git add .
    git commit -m "CHECKPOINT-BEFORE-${CHANGE_NAME}-${TIMESTAMP}"
    git tag "checkpoint-before-${CHANGE_NAME}-${TIMESTAMP}"
    echo "Checkpoint BEFORE ${CHANGE_NAME} created"

elif [ "$ACTION" == "after" ]; then
    git add .
    git commit -m "CHECKPOINT-AFTER-${CHANGE_NAME}-${TIMESTAMP}"
    git tag "checkpoint-after-${CHANGE_NAME}-${TIMESTAMP}"
    echo "Checkpoint AFTER ${CHANGE_NAME} created"
else
    echo "Invalid action. Use 'before' or 'after'"
    exit 1
fi
