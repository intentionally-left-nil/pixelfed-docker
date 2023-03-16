#! /bin/sh

set -x
acme_dir=/root/.acme.sh
cert_dir="$acme_dir/certs/$ACME_DOMAIN"

if [ ! -f "$cert_dir/cert.pem" ]; then
  # Nginx is running for the first time on the production server
  # Copy over the acme.sh details from the initial_acme_config
  tar x -v -f /root/initial_acme_config.tar -C /root || exit 1
fi

if [ ! -f "$acme_dir/dhparams.pem" ]; then
  openssl dhparam -dsaparam -out "$acme_dir/dhparams.pem" 4096 || exit 1
fi

if [ ! -f "$cert_dir/self_signed_cert.pem" ]; then
  mkdir -p "$cert_dir" || exit 1
  openssl req -x509 -newkey rsa:4096 -sha256 -days 365 -nodes \
  -keyout "$cert_dir/self_signed_key.pem" \
  -out "$cert_dir/self_signed_cert.pem" \
  -subj "/CN=$ACME_DOMAIN" \
  -addext "subjectAltName=DNS:$ACME_DOMAIN,DNS:$ACME_DOMAIN_ALIAS" || exit 1
fi

if [ ! -f "$cert_dir/cert.pem" ]; then
  # This is the first time running the production server, and the prod certs
  # haven't been generated yet
  # Run the server with a self-signed certificate to solve the chicken/egg
  # problem (since generating the cert requires nginx to be running)
  ln -s "$cert_dir/self_signed_cert.pem" "$cert_dir/cert.pem"
  ln -s "$cert_dir/self_signed_cert.pem" "$cert_dir/fullchain.pem"
  ln -s "$cert_dir/self_signed_key.pem" "$cert_dir/key.pem"
fi

