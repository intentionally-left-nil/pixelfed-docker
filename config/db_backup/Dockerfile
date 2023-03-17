FROM python:alpine AS builder

ENV AWSCLI_VERSION=2.11.3

RUN apk update && apk add --no-cache \
    curl \
    make \
    cmake \
    gcc \
    g++ \
    libc-dev \
    libffi-dev \
    openssl-dev

RUN curl https://awscli.amazonaws.com/awscli-${AWSCLI_VERSION}.tar.gz | tar -xz \
    && cd awscli-${AWSCLI_VERSION} \
    && ./configure --prefix=/opt/aws-cli/ --with-download-deps \
    && make \
    && make install

FROM python:alpine
RUN apk update && apk --no-cache add groff postgresql-client tini
COPY --from=builder /opt/aws-cli/ /opt/aws-cli/
RUN ln -s /opt/aws-cli/bin/aws /usr/bin/aws

COPY ./backup.sh /etc/periodic/daily/backup.sh
RUN chmod +x /etc/periodic/daily/backup.sh

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/usr/sbin/crond", "-f", "-d", "0"]
