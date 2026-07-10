# OCI VM Terraform

Creates Oracle VM with networking, firewall, SSH keys.

## Usage

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your compartment OCID
terraform init
terraform apply -auto-approve
```

## Outputs

- `vm_public_ip` — paste into GitHub Secret `OCI_VM_HOST`
- `github_secret_value` — paste into GitHub Secret `OCI_SSH_KEY`
