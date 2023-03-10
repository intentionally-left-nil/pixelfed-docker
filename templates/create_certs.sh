#! /bin/sh

if [ ! -f /root/.acme.sh/dhparams.pem ]; then
  openssl dhparam -dsaparam -out /root/.acme.sh/dhparams.pem 4096
fi

if [ ! -f /root/.acme.sh/${px.domain.web}_ecc/${px.domain.web}.cer ]; then
  /root/.acme.sh/acme.sh --accountconf /root/account.conf --server letsencrypt --issue -d ${px.domain.web} -d ${px.domain.web_alias} --stateless
  ln -s /root/.acme.sh/${px.domain.web}_ecc /root/.acme.sh/certs
fi
