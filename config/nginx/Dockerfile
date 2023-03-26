FROM nginx:mainline-alpine
RUN apk update && apk add --no-cache curl openssl

COPY bootstrap.sh /docker-entrypoint.d/98-bootstrap.sh
RUN chmod +x /docker-entrypoint.d/98-bootstrap.sh

COPY create_certs.sh /root/create_certs.sh
RUN chmod +x /root/create_certs.sh

RUN (crontab -l; echo "* * * * * /root/create_certs.sh") | sort -u | crontab -

COPY renew.sh /docker-entrypoint.d/99-renew.sh
RUN chmod +x /docker-entrypoint.d/99-renew.sh

COPY pixelfed/public /usr/share/nginx/html
