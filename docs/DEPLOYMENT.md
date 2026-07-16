# OpenClaw Superswarm Deployment Guide

## Prerequisites
- Docker & Docker Compose
- GitHub account with repo access
- Render account (primary) or OCI VM (secondary)
- All API keys in `.env` file (NEVER commit this)

## Local Development
```bash
cp .env.example .env
# Edit .env with your keys
docker-compose -f devops/docker/docker-compose.yml up --build
```

## Render Deployment
1. Connect GitHub repo to Render
2. Set environment variables in Render Dashboard
3. Deploy hook auto-triggers on push to `main`

## OCI Deployment
1. Provision VM with Terraform: `terraform apply -chdir=terraform/`
2. Add SSH key to GitHub secrets: `OCI_SSH_KEY`
3. GitHub Actions auto-deploys to OCI on push

## Security Checklist
- [ ] All secrets rotated in last 90 days
- [ ] Branch protection enabled on `main`
- [ ] Security Guardian running (`--daemon`)
- [ ] Backups verified weekly
- [ ] 2FA enabled on all accounts
