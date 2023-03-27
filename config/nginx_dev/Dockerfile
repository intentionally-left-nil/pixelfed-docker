FROM pixelfed as builder

FROM nginx:mainline-alpine
COPY --from=builder /var/www/public /var/www/public
