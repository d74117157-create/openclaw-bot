#!/bin/bash
# OpenClaw Render Deploy Script
# Run this on your local machine with the Render CLI installed

set -e

echo "OpenClaw Elite — Render Deployment"
echo "==================================="

# Check for render CLI
if ! command -v render &> /dev/null; then
    echo "Installing Render CLI..."
    npm install -g @render/cli
fi

# Verify login
render whoami || (echo "Please login: render login" && exit 1)

# Deploy from blueprint
echo "Deploying from GitHub blueprint..."
render blueprint apply https://github.com/d74117157-create/openclaw-bot

echo ""
echo "Deployment initiated!"
echo "Monitor at: https://dashboard.render.com"
