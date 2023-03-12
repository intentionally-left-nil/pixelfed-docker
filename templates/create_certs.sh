#! /bin/sh

set -x

domain=${px.domain.web}
domain_alias=${px.domain.web_alias}
cert_dir="/root/.acme.sh/certs/$domain"

if [ ! -f "$cert_dir/cert.pem" ]; then
# First, try to untar the data from the backup file
  tar x -v -f backup.tar -C /root || exit 1
fi

mkdir -p "$cert_dir" || exit 1

if [ ! -f /root/.acme.sh/dhparams.pem ]; then
  openssl dhparam -dsaparam -out /root/.acme.sh/dhparams.pem 4096 || exit 1
fi

if [ ! -f "$cert_dir/cert.pem" ]; then
  /root/.acme.sh/acme.sh --accountconf /root/account.conf --server letsencrypt --issue -d "$domain" -d "$domain_alias" --stateless || exit 1
  /root/.acme.sh/acme.sh --accountconf /root/account.conf --install-cert -d "$domain" \
  --cert-file "$cert_dir/cert.pem" \
  --key-file "$cert_dir/key.pem" \
  --fullchain-file "$cert_dir/fullchain.pem" \
  --reloadcmd "nginx -s reload || true" || exit 1
fi
