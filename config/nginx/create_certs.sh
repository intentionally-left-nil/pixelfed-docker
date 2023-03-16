#! /bin/sh

set -x

{
  acme_dir=/root/.acme.sh
  cert_dir="$acme_dir/certs/$ACME_DOMAIN"

  lock_file="/root/create_certs.lock"
  if [ -f "$lock_file" ]; then
    echo "create_certs already running"
    exit 0
  fi

  touch "$lock_file"
  trap 'rm "$lock_file"' EXIT

  if ! "$acme_dir/acme.sh" --list | grep "$ACME_DOMAIN"; then
    echo "Creating the certificate for $ACME_DOMAIN and $ACME_DOMAIN_ALIAS"
    "$acme_dir/acme.sh" --server letsencrypt --issue -d "$ACME_DOMAIN" -d "$ACME_DOMAIN_ALIAS" --stateless || exit 1

    echo "Certificate created! Copying it over to $cert_dir"
    "$acme_dir/acme.sh" --install-cert -d "$ACME_DOMAIN" \
    --cert-file "$cert_dir/cert.pem" \
    --key-file "$cert_dir/key.pem" \
    --fullchain-file "$cert_dir/fullchain.pem" \
    --reloadcmd "nginx -s reload || true" || exit 1

    ls -la "$cert_dir"
  fi

  if "$acme_dir/acme.sh" --list | grep "$ACME_DOMAIN"; then
    echo "The certificate has been installed, uninstalling the cron job"
    crontab -l | grep -v 'create_certs' | crontab -
  fi
# Redirect stdout to process 1's stdout, stderr to process 1's stderr
# This way it will end up in the docker logs

} 1>/proc/1/fd/1 2>/proc/1/fd/2
