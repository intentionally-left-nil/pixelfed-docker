#! /bin/sh
set +x

{
  lock_file="/root/db_backup.lock"
  if [ -f "$lock_file" ]; then
    echo "backup.sh already running"
    exit 0
  fi

  touch "$lock_file"
  trap 'rm "$lock_file"' EXIT


  now=$(date +%s) || exit 1
  aws --endpoint-url "$AWS_ENDPOINT_URL" s3 cp "s3://$AWS_SOURCE_BUCKET" "s3://$AWS_DEST_BUCKET/$now/" --recursive || exit 1
  echo "Created backup at $AWS_DEST_BUCKET/$now"

  files=$(aws --endpoint-url "$AWS_ENDPOINT_URL" s3 ls "s3://$AWS_DEST_BUCKET" | awk '{print $2}' | sort -nr)
  i=1;
  for filename in $files; do
    if [ "$i" -gt "$MAX_BACKUPS" ]; then
      echo "removing $AWS_DEST_BUCKET/$filename"
      aws --endpoint-url "$AWS_ENDPOINT_URL" s3 rm "s3://$AWS_DEST_BUCKET/$filename" || exit 1
    else
      echo "$AWS_DEST_BUCKET/$filename is backup $i"
    fi
    i="$((i+1))"
  done

# Redirect stdout to process 1's stdout, stderr to process 1's stderr
# This way it will end up in the docker logs
} 1>/proc/1/fd/1 2>/proc/1/fd/2
