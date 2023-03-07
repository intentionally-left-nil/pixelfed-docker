FROM python:alpine
RUN apk update && apk add --no-cache tini
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["python", "/app.py"]
