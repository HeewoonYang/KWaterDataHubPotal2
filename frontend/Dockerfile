# Stage 1: Build
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Serve
FROM nginx:1.27-alpine

# 런타임 ENV 주입 스크립트
COPY docker-entrypoint.sh /docker-entrypoint-runtime.sh
RUN chmod +x /docker-entrypoint-runtime.sh

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# nginx:alpine 은 이미 비root(nginx) 로 동작 가능한 구성. readOnlyRootFilesystem 가 필요하면 emptyDir 추가.
EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost/ > /dev/null || exit 1

CMD ["/docker-entrypoint-runtime.sh"]
