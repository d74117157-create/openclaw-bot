# OpenClaw Oracle Cloud Free Tier Migration

## Prerequisites

- Oracle Cloud Free Tier account
- Ubuntu VM (Always Free: 1/8 OCPU, 1GB RAM)
- Docker + Docker Compose installed
- Domain name (optional, for SSL)

## Setup

1. **Create Oracle VM**
   ```bash
   # In Oracle Cloud Console
   # Compute → Instances → Create Instance
   # Shape: VM.Standard.E2.1.Micro (Always Free)
   # Image: Ubuntu 22.04
   ```

2. **Install Docker**
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   ```

3. **Deploy**
   ```bash
   export OCI_HOST=your.vm.ip.address
   ./oracle/deploy.sh
   ```

4. **SSL (optional)**
   ```bash
   # Place cert.pem and key.pem in oracle/ssl/
   # Or use Let's Encrypt
   ```

## Services

| Service | Port | Description |
|---------|------|-------------|
| App | 8080 | OpenClaw API |
| PostgreSQL | 5432 | Database |
| Nginx | 80/443 | Reverse proxy + SSL |

## Backup

```bash
./oracle/backup.sh
```

## Restore

```bash
./oracle/restore.sh /home/opc/backups/db_20260721_120000.sql
```

## Monitoring

```bash
# Check containers
docker ps

# Check logs
docker logs -f openclaw_app_1

# Health check
curl https://your.vm.ip/health
```
