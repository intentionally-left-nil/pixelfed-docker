FROM ghcr.io/intentionally-left-nil/pixelfed-fpm:0.12.5-fix-s3-federation
RUN apt-get update \
  && apt-get install -y --no-install-recommends cron tini

COPY task.sh /root/task.sh
RUN chmod +x /root/task.sh
RUN echo "*/15 * * * * /root/task.sh" | crontab -
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/usr/sbin/cron", "-f"]
