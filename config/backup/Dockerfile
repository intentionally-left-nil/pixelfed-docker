FROM ghcr.io/intentionally-left-nil/awscli:latest
RUN apk update && apk --no-cache add groff postgresql-client tini bash

COPY ./backup.sh /etc/periodic/daily/backup.sh
RUN chmod +x /etc/periodic/daily/backup.sh

COPY ./restore.sh /root/restore.sh
RUN chmod +x /root/restore.sh

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/usr/sbin/crond", "-f"]
