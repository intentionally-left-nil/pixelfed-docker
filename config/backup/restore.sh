#! /bin/bash
set -o pipefail

# https://stackoverflow.com/a/14203146/3029173
for i in "$@"; do
  case $i in
    -t=*|--timestamp=*)
      backup_timestamp="${i#*=}"
      shift
      ;;
    -n=*|--backup-number=*)
      backup_number="${i#*=}"
      shift
      ;;
    -d=*|--dest-environment=*)
      dest_environment="${i#*=}"
      shift
      ;;
    -s=*|--source-environment=*)
      source_environment="${i#*=}"
      shift
      ;;
    --restore-db)
      restore_db=1
      shift
      ;;
    --restore-s3)
      restore_s3=1
      shift
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    -l|--list)
      list_backups=1
      shift
      ;;
    -h|--help)
      printf -- "restore.sh Restore the S3 bucket or the database from backups\nFlags\n-d=<ENV> or --dest-environment=<ENV> where ENV is either prod or dev\n This is where you want your backups restored TO\n\n"
      printf -- "-s=<ENV> or --source-environment=<ENV> where ENV is either prod or dev. This is where the backups are coming from. Defaults to the source-environment if not specified\n Useful if restoring from prod->dev\n\n"
      printf -- "-l or --list: Display a list of the current backups for the source environment, and then exit. No restoration is performed if this flag is set\n\n"
      printf -- "-t=<TIMESTAMP> or --timestamp=<TIMESTAMP> selects the backup to use for restoring. See --list to determine the timestamp to use. You can either use --timestamp or --backup-number to select the backup\n\n"
      printf -- "-n=<INT> or --backup-number=<INT> selects the backup to use for restoring. A backup-number of 1 corresponds to the most recent backup. 2 corresponds to the second most recent backup, and so on\n\n"
      printf -- "--restore-db Pass this flag in to restore the database, otherwise the database will be unaffected\n\n"
      printf -- "--restore-s3 Pass this flag in to restore the S3 bucket, otherwise the S# bucket will be unaffected\n\n"
      printf -- "--dry-run Pass this flag in to see what would happen if you ran the script, without any changes taking place\n\n"
      printf -- "Examples:\nView the backups on dev: restore.sh -s=dev --list\n"
      printf -- "Restore prod fully from the last backup: restore.sh -s=prod -n=1 --restore-db --restore-s3\n"
      printf -- "Restore the dev environment to be a copy of prod: restore.sh -s=prod -d=dev -n=1 --restore-db --restore-s3\n"

      ;;
    -*|--*)
      echo "Unknown option $i"
      exit 1
      ;;
    *)
      ;;
  esac
done
source_environment=${source_environment:-$dest_environment}
if [ "$dest_environment" = "prod" ]; then
  AWS_SOURCE_BUCKET="$AWS_PROD_SOURCE_BUCKET"
else
  AWS_SOURCE_BUCKET="$AWS_DEV_SOURCE_BUCKET"
fi

if [ -z "$source_environment" ]; then
  echo "Missing --source-environment=prod or --source-environment=dev"
  exit 1
fi

if [ "$source_environment" != "prod" ] && [ "$source_environment" != "dev" ]; then
  echo "--source-environment must be either dev or prod"
  exit 1
fi

if [ -n "$backup_number" ] && [ -n "$timestamp" ]; then
  echo "You cannot use --backup-number and --timestamp at the same time. Choose one"
  exit 1
fi

mapfile -t files < <(aws --endpoint-url "$AWS_ENDPOINT_URL" s3 ls "s3://$AWS_DEST_BUCKET/$source_environment/db/" | awk '{print $2}' | sort -nr)

if [ "${#files[*]}" -eq 0 ]; then
  echo "No backups exist in $source_environment"
  exit 1
fi

i=0;
for timestamp in "${files[@]}"; do
  # Remove the trailing slash from the foldername
  timestamp=${timestamp%/}
  files[i]="$timestamp"
  i="$((i+1))"
done


if [ "${list_backups:-0}" = "1" ]; then
  i=1;
  for timestamp in "${files[@]}"; do
    pretty=$(date -R -d "@$timestamp")
    printf "%s)\t%s\t%s\n" "$i" "$timestamp" "$pretty"
    i="$((i+1))"
  done
  exit 0
fi

if [ -n "$backup_number" ]; then
  backup_number=$((backup_number))
  if [ "$backup_number" -lt 1 ]; then
    echo "The --backup-number must be >= 1"
    exit 1
  fi
  if [ "$backup_number" -gt "${#files[*]}" ]; then
    echo "There are only ${#files[*]} backups available. Choose a smaller number"
    exit 1
  fi
  backup_index="$((backup_number-1))"
  backup_timestamp="${files[backup_index]}"
fi

if [ -z "$backup_timestamp" ]; then
  echo "Missing --timestamp or --backup-number"
  exit 1
fi

found_timestamp=
for f in "${files[@]}"; do
  if [ "$f" = "$backup_timestamp" ]; then
    pretty=$(date -R -d "@$timestamp")
    found_timestamp=1
    break
  fi
done

if [ -z "$found_timestamp" ]; then
  echo "Could not find the timestamp $backup_timestamp in the $source_environment backups"
  exit 1
fi

if [ -z "$restore_s3" ] && [ -z "$restore_db" ]; then
  echo "Neither --restore-s3 nor --restore-db are set. Nothing to do"
  exit 0
fi

printf -- "Restoring backup %s\t%s\n" "$backup_timestamp" "$pretty"

if [ -n "$restore_s3" ]; then

  source="s3://$AWS_DEST_BUCKET/$source_environment/cloud_files/$backup_timestamp"
  dest="s3://$AWS_SOURCE_BUCKET"
  echo "Restoring $source to $dest"

  if [ -n "$dry_run" ]; then
    echo "NOT actually restoring the files because --dry-run is set"
  else
    read -r -p "Do you wish to continue y/n?: " confirm
    if [ "$confirm" = "y" ]; then
      aws --endpoint-url "$AWS_ENDPOINT_URL" s3 cp "$source" "$dest" --recursive || exit 1
      echo "Successfully restored the S3 bucket from backup"
    else
      echo "NOT restoring the files to S3"
    fi
  fi
fi

if [ -n "$restore_db" ]; then
  source="s3://$AWS_DEST_BUCKET/$source_environment/db/$backup_timestamp/pg.dmp"
  echo "Restoring the database from $source"
  if [ -n "$dry_run" ]; then
    echo "NOT actually restoring the database because --dry-run is set"
  else
    read -r -p "Do you wish to continue y/n?: " confirm
    if [ "$confirm" = "y" ]; then
      aws --endpoint-url "$AWS_ENDPOINT_URL" s3 cp "$source" '-' | pg_restore -d "postgres://postgres:$POSTGRES_PASSWORD@db:5432" --clean --create --if-exists -e ||  exit 1
      echo "Successfully restored the database from backup"
    else
      echo "NOT restoring the database"
    fi
  fi
fi
