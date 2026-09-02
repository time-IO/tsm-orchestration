FROM node:25.8-slim AS js-builder

RUN mkdir /datasourcefrontend
COPY ./app /datasourcefrontend

WORKDIR /datasourcefrontend

RUN npm ci
RUN npm run build

FROM nginx:1.29-alpine AS webserver

# Pull latest security-fixed Alpine packages for runtime image.
RUN apk upgrade --no-cache libexpat zlib

COPY --from=js-builder /datasourcefrontend/dist/spa /usr/share/nginx/html
COPY ./docker/generic-image/default.conf /etc/nginx/conf.d/default.conf

COPY ./docker/generic-image/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh \
  && chown -R nginx:nginx /usr/share/nginx/html

EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
