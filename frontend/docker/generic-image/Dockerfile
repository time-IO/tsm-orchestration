FROM node:25.2.1 AS js-builder

RUN mkdir /datasourcefrontend
COPY ./app /datasourcefrontend

WORKDIR /datasourcefrontend

RUN npm ci
RUN npm run build

FROM nginx:1.27.3-alpine AS webserver

COPY --from=js-builder /datasourcefrontend/dist/spa /usr/share/nginx/html
COPY ./docker/generic-image/default.conf /etc/nginx/conf.d/default.conf

COPY ./docker/generic-image/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
