FROM alpine:latest
RUN apk update && apk add --no-cache curl openssl

RUN touch /root/create_certs.sh
RUN chmod +x /root/create_certs.sh

ENTRYPOINT ["/root/create_certs.sh"]
