FROM alpine:latest
RUN apk update && apk add --no-cache curl openssl

ARG acme_email
RUN curl https://get.acme.sh > install.sh && chmod +x install.sh
RUN ./install.sh email="$acme_email"
RUN mkdir -p /root/.acme.sh/ca
RUN rm install.sh
ENTRYPOINT ["/root/.acme.sh/acme.sh"]
