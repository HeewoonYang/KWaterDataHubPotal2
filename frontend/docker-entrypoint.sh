#!/bin/sh
# nginx 기동 전 런타임 env 를 /usr/share/nginx/html/env.js 로 출력한다.
# K8s ConfigMap 의 값을 컨테이너 시작 시 주입 → 이미지 재빌드 없이 환경 전환 가능.
set -e

: "${API_BASE_URL:=/api/v1}"
: "${APP_ENV:=production}"

cat > /usr/share/nginx/html/env.js <<EOF
// 이 파일은 컨테이너 기동 시 docker-entrypoint.sh 가 생성합니다.
window.__ENV__ = {
  API_BASE_URL: "${API_BASE_URL}",
  APP_ENV: "${APP_ENV}"
};
EOF

exec nginx -g 'daemon off;'
