# Tengri Bot — Setup Runbook

Step-by-step guide to provision and deploy tengri-bot on AWS Lightsail.

---

## Prerequisites

- AWS account
- GitHub repo (this project)
- Telegram bot token from [@BotFather](https://t.me/BotFather)
- Target group chat ID

---

## Phase 1: Terraform (one-time)

### 1.1 Create GitHub OIDC provider (if not exists)

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

If you get "EntityAlreadyExists", skip this.

### 1.2 Terraform apply

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: set github_org = "your-github-username"

terraform init
terraform plan
terraform apply
```

### 1.3 Save outputs

```bash
# SSH key (add to GitHub Secrets as SSH_PRIVATE_KEY)
terraform output -raw lightsail_private_key > tengri-key.pem
chmod 600 tengri-key.pem

# Public IP (add to GitHub Secrets as DEPLOY_HOST)
terraform output lightsail_public_ip

# IAM role ARN (add to GitHub Secrets as AWS_ROLE_ARN)
terraform output github_actions_role_arn

# ECR registry (for host .env)
terraform output ecr_repository_url

# Host AWS credentials (for ECR pull + S3 backup on the instance)
terraform output -raw host_access_key_id
terraform output -raw host_secret_access_key   # run once, save securely

# S3 bucket (for backup cron)
terraform output s3_backup_bucket
```

---

## Phase 2: GitHub Secrets

Add these in **Settings → Secrets and variables → Actions** → **Secrets** tab.  
Use **Repository secrets** (click **New repository secret**), not Environment secrets.  
Paste the **actual value** (run the command, copy the output, paste into the secret value).

| Secret | How to get the value |
|--------|----------------------|
| `AWS_ROLE_ARN` | Run `terraform output -raw github_actions_role_arn` → copy the full ARN → paste as value |
| `SSH_PRIVATE_KEY` | Open `tengri-key.pem`, copy the entire file (including BEGIN/END lines) → paste as value |
| `DEPLOY_HOST` | Run `terraform output -raw lightsail_public_ip` → copy the IP (e.g. `3.98.xxx.xxx`) → paste as value |

---

## Phase 3: Lightsail instance setup

### 3.1 SSH into the instance

```bash
ssh -i tengri-key.pem ubuntu@<LIGHTSAIL_IP>
```

### 3.2 Run install script

Copy `scripts/install-on-host.sh` to the instance and run:

```bash
chmod +x install-on-host.sh
./install-on-host.sh
```

Log out and back in (for `docker` group).

### 3.3 Clone repo (or copy files)

```bash
# Option A: Clone (if repo is accessible)
git clone https://github.com/YOUR_ORG/tengri-bot.git /opt/tengri-bot
cd /opt/tengri-bot

# Option B: Copy files manually
# Copy: docker-compose.prod.yml, .env.example, scripts/
```

### 3.4 Create .env

```bash
cd /opt/tengri-bot
./scripts/setup-env.sh
# Enter TELEGRAM_TOKEN and TELEGRAM_GROUP when prompted
```

### 3.5 Add ECR_REGISTRY to .env

```bash
echo "ECR_REGISTRY=123456789.dkr.ecr.ca-central-1.amazonaws.com" >> /opt/tengri-bot/.env
# Replace with your ECR registry from: terraform output ecr_repository_url | cut -d/ -f1
```

### 3.6 Configure AWS credentials (for ECR pull + backup)

```bash
mkdir -p ~/.aws
cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = YOUR_HOST_ACCESS_KEY
aws_secret_access_key = YOUR_HOST_SECRET_KEY
EOF
chmod 600 ~/.aws/credentials
```

### 3.7 First deploy (manual)

```bash
cd /opt/tengri-bot
export ECR_REGISTRY=$(terraform output -raw ecr_repository_url | cut -d/ -f1)  # or set manually
aws ecr get-login-password --region ca-central-1 | docker login --username AWS --password-stdin $ECR_REGISTRY
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

(First run will fail until CI has pushed an image. Push to `main` to trigger the first build.)

### 3.8 Backup cron

```bash
crontab -e
# Add (3 AM EST = 8 UTC):
0 8 * * * S3_BACKUP_BUCKET=tengri-bot-backups-ACCOUNT_ID /opt/tengri-bot/scripts/backup-to-s3.sh 2>&1 | logger -t tengri-backup
```

Replace `ACCOUNT_ID` with your AWS account ID.

---

## Phase 4: Verify

1. Push to `main` → CI runs.
2. Check GitHub Actions → build-and-deploy should succeed.
3. Bot should be running in your Telegram group.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `docker: permission denied` | Log out and back in after `usermod -aG docker ubuntu` |
| `no basic auth credentials` | Run `aws ecr get-login-password \| docker login ...` on host |
| `ECR_REGISTRY` empty | Add to .env or export before docker compose |
| Backup fails | Check AWS credentials and S3_BACKUP_BUCKET |
| 409 Conflict | Another bot instance is running; stop it |

---

## File reference

| Path | Purpose |
|------|---------|
| `terraform/` | IaC (Lightsail, ECR, S3, IAM) |
| `.github/workflows/ci.yml` | CI/CD pipeline |
| `docker-compose.prod.yml` | Production compose (ECR image) |
| `scripts/setup-env.sh` | Interactive .env creation |
| `scripts/backup-to-s3.sh` | Backup cron script |
| `scripts/install-on-host.sh` | Docker + AWS CLI on Lightsail |
