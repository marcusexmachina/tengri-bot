#!/usr/bin/env bash
# Backup Docker volume to S3. Run via cron daily at 3 AM EST (8 UTC).
# Requires AWS credentials on host. Set S3_BACKUP_BUCKET.
set -e

BUCKET="${S3_BACKUP_BUCKET}"
VOLUME_NAME="${BACKUP_VOLUME:-tengri-bot_tengri-bot-data}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

if [[ -z "$BUCKET" ]]; then
  echo "S3_BACKUP_BUCKET not set"
  exit 1
fi

docker run --rm -v "$VOLUME_NAME":/data alpine tar -czf - -C /data . | \
  aws s3 cp - "s3://$BUCKET/backups/backup-$TIMESTAMP.tar.gz"
