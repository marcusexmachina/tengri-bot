# TNN News Bot — Migration Plan to Lightsail (Same Instance as Tengri)

**Purpose:** Migrate tnn-news-bot to the same Lightsail instance as tengri-bot, reusing the infrastructure and patterns we established. This document is a standalone plan for use in a separate Cursor tab or session focused on tnn-news-bot.

**Target host:** Same Lightsail instance (2 GB RAM, 1 vCPU, 60 GB SSD) at `52.60.223.22` — `/opt/tengri-bot` and `/opt/tnn-news-bot` will coexist.

---

## 1. What We Did for Tengri-Bot (Reference)

| Component | Tengri implementation |
|-----------|------------------------|
| **Terraform** | Lightsail instance, static IP, key pair; ECR repo; S3 bucket (backups); IAM OIDC role for GitHub Actions; IAM host user (ECR pull + S3) |
| **CI/CD** | GitHub Actions: lint (Ruff), test (pytest), build Docker (linux/amd64), push to ECR, SSH deploy (`docker compose pull && up -d`) |
| **Secrets** | GitHub: `AWS_ROLE_ARN`, `SSH_PRIVATE_KEY`, `DEPLOY_HOST`. Host: `.env` (TELEGRAM_TOKEN, TELEGRAM_GROUP, etc.) |
| **Deploy path** | `/opt/tengri-bot` |
| **Backup** | Cron: tar Docker volume → S3 `backups/` with lifecycle (7d standard, 30d Glacier, 90d expire) |
| **Docker** | `docker-compose.prod.yml` uses ECR image; `STATE_FILE`; named volume for data |

---

## 2. TNN News Bot — Differences to Account For

| Aspect | Tengri | TNN |
|--------|--------|-----|
| **Entry** | `python bot.py` | `python -m tnn_bot` |
| **State** | JSON files | SQLite (`/data/state.db`) |
| **Dependencies** | Slim: telegram, dotenv. Optional NSFW: torch, transformers | tweepy, telethon, openai, opencv, Pillow, imagehash, etc. (~250–400 MB) |
| **Env vars** | TELEGRAM_TOKEN, TELEGRAM_GROUP, STATE_FILE | TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL, TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION_STRING, X_BEARER_TOKEN, OPENAI_API_KEY |
| **Config** | config.py + .env | config.json + .env |
| **Volume** | `tengri-bot-data` → `/app/data` | `tnn_bot_data` → `/data` |
| **Repo** | tengri-bot | tnn-news-bot (separate repo) |

---

## 3. Decisions Made

| # | Question | Decision |
|---|----------|----------|
| 1 | GitHub repo | `https://github.com/marcusexmachina/tnn-news-bot.git` |
| 2 | Deploy branch | `main` |
| 3 | OIDC role | **Separate** IAM role for tnn (not shared with tengri) |
| 4 | Terraform | **Separate** Terraform (in tnn repo or standalone) |
| 5 | SSH key | Same key as tengri (same host) |
| 6 | Tests | No tests exist; CI skips pytest or add minimal smoke test |
| 7 | Ruff | Add `pyproject.toml` with Ruff config |
| 8 | config.json | Committed, baked into image; mount optional for override |
| 9 | Telethon session | `TELEGRAM_SESSION_STRING` (preferred); file fallback at `/data/telegram_session.session` |
| 10 | Backup | **Separate** S3 bucket and cron for tnn |
| 11 | Resource limits | Yes — `mem_limit: 512m` (and optionally `cpus`) per container |

---

## 4. Migration Plan — Step by Step

### Phase 1: Terraform (Separate — in tnn-news-bot or infra repo)

Create a **new** Terraform configuration for tnn (do not add to tengri Terraform):

1. **ECR repo:**
   ```hcl
   resource "aws_ecr_repository" "tnn" {
     name                 = "tnn-news-bot"
     image_tag_mutability = "MUTABLE"
     image_scanning_configuration { scan_on_push = true }
   }
   ```

2. **S3 bucket for tnn backups** (separate from tengri):
   ```hcl
   resource "aws_s3_bucket" "tnn_backups" {
     bucket = "tnn-news-bot-backups-${data.aws_caller_identity.current.account_id}"
   }

   resource "aws_s3_bucket_lifecycle_configuration" "tnn_backups" {
     bucket = aws_s3_bucket.tnn_backups.id

     rule {
       id     = "backup-lifecycle"
       status = "Enabled"

       transition {
         days          = 7
         storage_class = "GLACIER"
       }

       expiration {
         days = 90
       }
     }
   }
   ```

3. **IAM host user** for tnn (separate from tengri host user):
   - ECR pull for `tnn-news-bot`
   - S3 put/get for tnn backup bucket
   - On host: add credentials as `[tnn]` profile in `~/.aws/credentials`; deploy and backup scripts use `AWS_PROFILE=tnn` when operating on tnn.

4. **IAM OIDC role for GitHub Actions** (separate from tengri):
   ```hcl
   # Trust: repo:marcusexmachina/tnn-news-bot:ref:refs/heads/main
   # (Restrict to main; use repo:marcusexmachina/tnn-news-bot:* only if you deploy from other branches)
   # Permissions: ECR push, assume role
   ```

**Outputs:** `tnn_ecr_repository_url`, `tnn_backup_bucket`, `tnn_oidc_role_arn`

---

### Phase 2: TNN Repo — CI/CD (GitHub Actions)

Create `.github/workflows/ci.yml` in tnn-news-bot:

- **Lint:** Ruff (add `pyproject.toml` with `[tool.ruff]` — no tests exist, so skip pytest)

   **pyproject.toml** (minimal Ruff config):
   ```toml
   [project]
   name = "tnn-news-bot"
   # ... existing metadata ...

   [tool.ruff]
   target-version = "py312"
   line-length = 100

   [tool.ruff.lint]
   select = ["E", "F", "I", "N", "W"]
   ignore = ["N806", "F841"]
   # E501: omit to enforce line-length 100; add E501 to ignore if relaxing for legacy code
   ```
- **Build:** `docker build --platform linux/amd64 -t $ECR_REGISTRY/tnn-news-bot:latest .`
- **Push:** ECR
- **Deploy:** SSH to same host, run:
  ```bash
  cd /opt/tnn-news-bot && \
  set -a && [ -f .env ] && . .env && set +a && \
  AWS_PROFILE=tnn aws ecr get-login-password --region ca-central-1 | docker login --username AWS --password-stdin $ECR_REGISTRY && \
  docker compose -f docker-compose.prod.yml pull && \
  docker compose -f docker-compose.prod.yml up -d
  ```
  **ECR_REGISTRY:** Must be set on the host. Add to `/opt/tnn-news-bot/.env` (e.g. `ECR_REGISTRY=981498563925.dkr.ecr.ca-central-1.amazonaws.com`). The deploy step sources `.env` before running Compose so the image reference `${ECR_REGISTRY}/tnn-news-bot:latest` resolves.

**Secrets** (in tnn-news-bot repo): `AWS_ROLE_ARN` (tnn OIDC role), `SSH_PRIVATE_KEY` (same as tengri), `DEPLOY_HOST` (`52.60.223.22`).

---

### Phase 3: TNN Repo — Docker and Prod Compose

1. **Dockerfile:** Ensure it builds for `linux/amd64` (or add `--platform` in CI). `config.json` is already `COPY config.json .` — baked in. No mount override needed unless you want runtime override.

2. **docker-compose.prod.yml** (new file):
   ```yaml
   services:
     bot:
       image: ${ECR_REGISTRY}/tnn-news-bot:latest
       container_name: tnn-news-bot
       restart: unless-stopped
       env_file: .env
       environment:
         DB_PATH: /data/state.db
         CONFIG_PATH: /app/config.json
       volumes:
         - tnn_bot_data:/data
       mem_limit: 512m
       cpus: "0.5"
       healthcheck:
         test: ["CMD", "python", "-c", "import sqlite3; sqlite3.connect('/data/state.db')"]
         interval: 60s
         timeout: 5s
         retries: 3
         start_period: 30s
   volumes:
     tnn_bot_data:
   ```
   - **config.json:** Baked into image; optional mount `./config.json:/app/config.json:ro` if you need host override.
   - **Telethon:** Use `TELEGRAM_SESSION_STRING` in `.env` (recommended). If using file session, it lives at `/data/telegram_session.session` (persisted in volume).

---

### Phase 4: Host Setup (One-Time)

On the **existing** Lightsail instance:

1. **Create directory:**
   ```bash
   sudo mkdir -p /opt/tnn-news-bot
   sudo chown ubuntu:ubuntu /opt/tnn-news-bot
   ```

2. **Clone tnn-news-bot** (or copy files):
   ```bash
   git clone https://github.com/marcusexmachina/tnn-news-bot.git /opt/tnn-news-bot
   sudo chown -R ubuntu:ubuntu /opt/tnn-news-bot
   ```

3. **Create .env:** The repo has no `.env.example`. Add one (see below) or create `.env` from this template:
   ```bash
   # Required
   TELEGRAM_BOT_TOKEN=
   TELEGRAM_CHANNEL=
   TELEGRAM_API_ID=
   TELEGRAM_API_HASH=
   TELEGRAM_SESSION_STRING=
   X_BEARER_TOKEN=
   OPENAI_API_KEY=
   # Deploy (host only)
   ECR_REGISTRY=981498563925.dkr.ecr.ca-central-1.amazonaws.com
   ```
   - `TELEGRAM_SESSION_STRING` — use `scripts/telegram_session.py` to generate; put in `.env`

4. **config.json** — already in repo (baked into image); no host copy needed unless overriding

5. **Add ECR_REGISTRY** to .env (e.g. `981498563925.dkr.ecr.ca-central-1.amazonaws.com`)

6. **First deploy:** Either push to main (CI will build and deploy) or manually:
   ```bash
   cd /opt/tnn-news-bot
   export ECR_REGISTRY=981498563925.dkr.ecr.ca-central-1.amazonaws.com
   AWS_PROFILE=tnn aws ecr get-login-password --region ca-central-1 | docker login --username AWS --password-stdin $ECR_REGISTRY
   docker compose -f docker-compose.prod.yml pull
   docker compose -f docker-compose.prod.yml up -d
   ```

7. **Host AWS credentials:** Add tnn IAM user to `~/.aws/credentials`:
   ```ini
   [tnn]
   aws_access_key_id = ...
   aws_secret_access_key = ...
   ```

---

### Phase 5: Backup (Separate S3 Bucket and Cron)

TNN uses its **own** S3 bucket (`tnn-news-bot-backups-<account-id>`) and cron job.

**Backup script** (e.g. `scripts/backup-to-s3.sh` in tnn repo):
```bash
#!/bin/bash
set -e
export AWS_PROFILE=tnn
BUCKET="${S3_BACKUP_BUCKET:-tnn-news-bot-backups-981498563925}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
# Volume name: tnn-news-bot_tnn_bot_data (Compose project = dir name "tnn-news-bot", volume = tnn_bot_data)
# If you run Compose with a different project name, the volume name will change.
docker run --rm -v tnn-news-bot_tnn_bot_data:/data alpine tar -czf - -C /data . | \
  aws s3 cp - "s3://$BUCKET/backups/backup-$TIMESTAMP.tar.gz"
```

**Cron** (4 AM to stagger with tengri at 3 AM):
```cron
0 4 * * * S3_BACKUP_BUCKET=tnn-news-bot-backups-981498563925 /opt/tnn-news-bot/scripts/backup-to-s3.sh
```

---

### Phase 6: Verification

- Both containers running: `docker ps`
- Tengri: `/opt/tengri-bot`, `tengri-bot` container
- TNN: `/opt/tnn-news-bot`, `tnn-news-bot` container
- Logs: `docker compose -f docker-compose.prod.yml logs -f` in each directory
- **Backup verification:** List S3 objects: `AWS_PROFILE=tnn aws s3 ls s3://tnn-news-bot-backups-981498563925/backups/` — or run a periodic test restore to confirm the cron is working.

---

### Phase 7: Rollback (Optional)

If a deploy breaks the bot:

1. **Revert to previous image:** Tag a known-good image as `:previous` before deploy:
   ```bash
   docker tag $ECR_REGISTRY/tnn-news-bot:latest $ECR_REGISTRY/tnn-news-bot:previous
   ```
2. **Rollback:** In `docker-compose.prod.yml` temporarily use `:previous` instead of `:latest`, or:
   ```bash
   docker pull $ECR_REGISTRY/tnn-news-bot:previous
   docker tag $ECR_REGISTRY/tnn-news-bot:previous $ECR_REGISTRY/tnn-news-bot:latest
   docker compose -f docker-compose.prod.yml up -d
   ```

---

## 5. Checklist Summary

- [ ] Terraform (separate): ECR repo, S3 bucket, IAM host user (ECR + S3), OIDC role for `marcusexmachina/tnn-news-bot`
- [ ] TNN repo: Add `pyproject.toml` with Ruff config
- [ ] TNN repo: Add `.github/workflows/ci.yml` (lint, build, push, deploy)
- [ ] TNN repo: Add `docker-compose.prod.yml` (with `mem_limit: 512m`, `cpus: "0.5"`, healthcheck)
- [ ] TNN repo: Add `scripts/backup-to-s3.sh`
- [ ] TNN repo: Add `.env.example` (or document required vars in this doc)
- [ ] GitHub: Add secrets to tnn repo (`AWS_ROLE_ARN`, `SSH_PRIVATE_KEY`, `DEPLOY_HOST`)
- [ ] Host: Create `/opt/tnn-news-bot`, clone repo, create .env
- [ ] Host: First deploy (manual or via CI)
- [ ] Host: Add backup cron for tnn (4 AM)
- [ ] Verify: Both bots running, logs clean

---

## 6. File Reference (TNN Repo)

| Path | Purpose |
|-----|---------|
| `Dockerfile` | Already exists; ensure linux/amd64 in CI |
| `docker-compose.yml` | Local dev; add `docker-compose.prod.yml` for ECR |
| `main.py` | Entry via `python -m tnn_bot` (scheduler) |
| `config.json` | Committed, baked into image |
| `.env` | Secrets (host only) |
| `.env.example` | **Add this** — template with placeholders for all required vars (see Phase 4 step 3) |
| `requirements.txt` | Dependencies |

---

## 7. Resource Sharing (Same Instance)

| Resource | Tengri | TNN | Total |
|----------|--------|-----|-------|
| RAM | ~150 MB (limit 512m) | ~350 MB (limit 512m) | ~1 GB |
| CPU | Low | Low–medium | 1 vCPU shared |
| Disk | Volume + image | Volume + image | 60 GB SSD sufficient |

No port conflicts (both are Telegram bots, no exposed ports).
