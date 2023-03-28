FROM nginx:mainline-alpine

RUN deluser www-data || true
RUN delgroup www-data || true
RUN adduser -D -H -u 1000 -s /bin/sh www-data
RUN sed -i -e 's/user\s\+nginx;/user www-data;/' /etc/nginx/nginx.conf

RUN apk update && apk add --no-cache curl openssl

COPY bootstrap.sh /docker-entrypoint.d/98-bootstrap.sh
COPY renew.sh /docker-entrypoint.d/99-renew.sh
COPY link_storage.sh /docker-entrypoint.d/90-link-storage.sh
COPY create_certs.sh /root/create_certs.sh

RUN find /docker-entrypoint.d/ -type f -iname "*.sh" -exec chmod +x {} \;
RUN chmod +x /root/create_certs.sh

RUN (crontab -l; echo "* * * * * /root/create_certs.sh") | sort -u | crontab -
COPY pixelfed/public /usr/share/nginx/html
