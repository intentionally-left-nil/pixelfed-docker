FROM ghcr.io/intentionally-left-nil/pixelfed-fpm:0.12.5-fix-s3-federation AS builder

FROM nginx:mainline-alpine
RUN deluser www-data || true
RUN delgroup www-data || true
RUN adduser -D -H -u 1000 -s /bin/sh www-data
RUN sed -i -e 's/user\s\+nginx;/user www-data;/' /etc/nginx/nginx.conf

RUN apk update && apk add --no-cache curl openssl

COPY link_storage.sh /docker-entrypoint.d/90-link-storage.sh

RUN find /docker-entrypoint.d/ -type f -iname "*.sh" -exec chmod +x {} \;

COPY --from=builder /var/www/public /var/www/public
