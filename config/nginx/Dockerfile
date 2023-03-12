FROM nginx:mainline-alpine
RUN apk update && apk add --no-cache openssl
COPY renew.sh /docker-entrypoint.d/renew.sh
RUN chmod +x /docker-entrypoint.d/renew.sh
