# OCI Worker Deployment

## Option A: Terraform (Automated)

```bash
cd terraform
export TF_VAR_tenancy_ocid="YOUR_TENANCY_OCID"
export TF_VAR_compartment_ocid="YOUR_COMPARTMENT_OCID"
export TF_VAR_ssh_public_key="$(cat ~/.ssh/openclaw_oci.pub)"
terraform init
terraform apply
```

Grab the `public_ip` output and add it to GitHub Secrets as `OCI_HOST`.

## Option B: Manual VM + GitHub Actions

1. Create an Oracle Linux 8 VM (Always Free tier: VM.Standard.A1.Flex)
2. Add your SSH public key during creation
3. SSH in: `ssh opc@YOUR_VM_IP`
4. Run: `bash <(curl -s https://raw.githubusercontent.com/d74117157-create/openclaw-bot/main/scripts/oci-setup.sh)`
5. Add `OCI_HOST`, `OCI_USER=opc`, and `OCI_SSH_KEY` (private key) to GitHub Secrets
6. Every push to `main` auto-deploys to the VM

## Required GitHub Secrets

| Secret | Value |
|--------|-------|
| `OCI_HOST` | VM public IP |
| `OCI_USER` | `opc` (default) |
| `OCI_SSH_KEY` | Private SSH key (full PEM) |

## Architecture

```
GitHub Push
    │
    ▼
GitHub Actions ──SSH──► OCI Worker (Oracle Linux 8)
                           │
                           ▼
                    Docker Container (openclaw:latest)
                           │
                    ┌──────┴──────┐
                    ▼             ▼
              Discord Bot    Telegram Bots
              Slack Bot      Trading Engine
```
