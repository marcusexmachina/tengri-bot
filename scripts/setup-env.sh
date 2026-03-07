#!/usr/bin/env bash
# Interactive setup of .env on the host. Run once after provisioning.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$REPO_ROOT/.env"

if [[ -f "$ENV_FILE" ]]; then
  echo ".env already exists. Overwrite? (y/N)"
  read -r ans
  [[ "$ans" != "y" && "$ans" != "Y" ]] && exit 0
fi

cp "$REPO_ROOT/.env.example" "$ENV_FILE"
chmod 600 "$ENV_FILE"

echo "Enter TELEGRAM_TOKEN (from BotFather):"
read -r token
sed -i.bak "s|your_bot_token_from_botfather|$token|" "$ENV_FILE"

echo "Enter TELEGRAM_GROUP (chat ID, e.g. -1001234567890):"
read -r group
sed -i.bak "s|-1001234567890|$group|" "$ENV_FILE"

# Uncomment STATE_FILE for Docker
sed -i.bak 's|# STATE_FILE=|STATE_FILE=|' "$ENV_FILE"
rm -f "$ENV_FILE.bak"

echo "Created $ENV_FILE"
