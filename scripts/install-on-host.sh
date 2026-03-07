#!/usr/bin/env bash
# Run this ON the Lightsail instance (as ubuntu) after first boot.
# Installs Docker, Docker Compose, AWS CLI, and sets up /opt/tengri-bot.
set -e

# Install Docker
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add ubuntu to docker group
sudo usermod -aG docker ubuntu

# Install AWS CLI
sudo apt-get install -y awscli || true
if ! command -v aws &>/dev/null; then
  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
  unzip -o /tmp/awscliv2.zip -d /tmp
  sudo /tmp/aws/install
fi

# Create app directory and clone repo (or copy files manually)
sudo mkdir -p /opt/tengri-bot
sudo chown ubuntu:ubuntu /opt/tengri-bot

echo "Done. Log out and back in for docker group."
echo ""
echo "Next steps (see SETUP_RUNBOOK.md):"
echo "  1. Clone repo to /opt/tengri-bot or copy docker-compose.prod.yml + scripts/"
echo "  2. Run scripts/setup-env.sh to create .env"
echo "  3. Configure AWS credentials (ECR pull + S3 backup)"
echo "  4. Add ECR_REGISTRY to .env"
echo "  5. Add backup cron"
