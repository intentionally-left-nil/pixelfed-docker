FROM awscli
RUN apk update && apk --no-cache add tini

COPY ./backup.sh /etc/periodic/daily/backup.sh
RUN chmod +x /etc/periodic/daily/backup.sh

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/usr/sbin/crond", "-f", "-d", "0"]
