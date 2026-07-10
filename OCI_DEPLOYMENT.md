
## Oracle Cloud Infrastructure (OCI) Deployment

### Option 1: Manual VM Setup

1. Create an OCI VM (Ubuntu 22.04, ARM or x86)
2. SSH into the VM: `ssh ubuntu@YOUR_VM_IP`
3. Run setup: `bash setup-oci-vm.sh`
4. Clone repo and configure `.env`
5. Start with systemd or docker-compose

### Option 2: Terraform (Automated)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your OCI credentials
terraform init
terraform apply
```

### Option 3: GitHub Actions Auto-Deploy

1. Add these secrets to your GitHub repository:
   - `OCI_VM_IP` — Your VM's public IP
   - `OCI_USER` — SSH username (usually `ubuntu`)
   - `OCI_SSH_KEY` — Private SSH key for the VM

2. Push to `main` branch triggers auto-deployment

### Required GitHub Secrets for OCI

| Secret | Description |
|--------|-------------|
| `OCI_VM_IP` | Public IP of your OCI VM |
| `OCI_USER` | SSH username (e.g., `ubuntu`) |
| `OCI_SSH_KEY` | Private SSH key (full key content) |

### OCI VM Firewall Rules

Ensure these ports are open in OCI Security List:
- 22 (SSH)
- 8080 (Health server)
- 3000 (Optional web port)
