FROM pixelfed as builder

FROM nginx:mainline-alpine
COPY --from=builder /var/www/public /var/www/public

COPY link_storage.sh /docker-entrypoint.d/90-link-storage.sh
RUN find /docker-entrypoint.d/ -type f -iname "*.sh" -exec chmod +x {} \;
