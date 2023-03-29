#! /bin/bash
set +x
set -o pipefail

{
  lock_file="/root/db_backup.lock"
  if [ -f "$lock_file" ]; then
    echo "backup.sh already running"
    exit 0
  fi

  touch "$lock_file"
  trap 'rm "$lock_file"' EXIT


  now=$(date +%s) || exit 1
  dest_root="s3://$AWS_DEST_BUCKET/${BACKUP_ENVIRONMENT:-prod}"

  echo "Backing up the database to $dest_root/db/$now"
  pg_dump -d "postgres://postgres:$POSTGRES_PASSWORD@db:5432/pixelfed" --format=custom | aws --endpoint-url "$AWS_ENDPOINT_URL" s3 cp - "$dest_root/db/$now/pg.dmp" || exit 1

  echo "Backing up s3://$AWS_SOURCE_BUCKET to $dest_root/cloud_files/$now"
  aws --endpoint-url "$AWS_ENDPOINT_URL" s3 cp "s3://$AWS_SOURCE_BUCKET" "$dest_root/cloud_files/$now" --recursive --quiet || exit 1


  echo "Removing old db backups"
  files=$(aws --endpoint-url "$AWS_ENDPOINT_URL" s3 ls "$dest_root/db/" | awk '{print $2}' | sort -nr)
  i=1;
  for filename in $files; do
    if [ "$i" -gt "$MAX_DB_BACKUPS" ]; then
      echo "removing $dest_root/db/$filename"
      aws --endpoint-url "$AWS_ENDPOINT_URL" s3 rm "$dest_root/db/$filename" --recursive || exit 1
    fi
    i="$((i+1))"
  done

  echo "Removing old cloud backups"
  files=$(aws --endpoint-url "$AWS_ENDPOINT_URL" s3 ls "$dest_root/cloud_files/" | awk '{print $2}' | sort -nr)
  i=1;
  for filename in $files; do
    if [ "$i" -gt "$MAX_FILE_BACKUPS" ]; then
      echo "removing $dest_root/cloud_files/$filename"
      aws --endpoint-url "$AWS_ENDPOINT_URL" s3 rm "$dest_root/cloud_files/$filename" --recursive --quiet || exit 1
    fi
    i="$((i+1))"
  done

# Redirect stdout to process 1's stdout, stderr to process 1's stderr
# This way it will end up in the docker logs
} 1>/proc/1/fd/1 2>/proc/1/fd/2
