#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# K-water DataHub Portal - 폐쇄망 이전 패키지 생성 스크립트
# 인터넷망에서 실행 → USB/망간자료전송용 tar.gz 생성
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
EXPORT_DIR="${PROJECT_DIR}/airgap-export-${TIMESTAMP}"
ARCHIVE_NAME="datahub-airgap-${TIMESTAMP}.tar.gz"

# 내부 레지스트리 (폐쇄망 harbor/registry)
INTERNAL_REGISTRY="${INTERNAL_REGISTRY:-registry.kwater.or.kr}"

# ── 색상 출력 ──
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

info "=== 폐쇄망 이전 패키지 생성 시작 ==="
info "출력 디렉토리: ${EXPORT_DIR}"
mkdir -p "${EXPORT_DIR}/images" "${EXPORT_DIR}/swagger-ui" "${EXPORT_DIR}/vendor"

# ═══════════════════════════════════════════════════
# 1단계: 프로젝트 Docker 이미지 빌드
# ═══════════════════════════════════════════════════
info "[1/6] Docker 이미지 빌드..."
cd "$PROJECT_DIR"
docker compose build --no-cache frontend backend

# ═══════════════════════════════════════════════════
# 2단계: 모든 이미지 save (프로젝트 + 외부 의존)
# ═══════════════════════════════════════════════════
info "[2/6] Docker 이미지 저장..."

# 프로젝트 이미지
IMAGES=(
  "datahub/frontend:v0.1.0"
  "datahub/backend:v0.1.0"
)

# 외부 인프라 이미지 (pull 후 save)
INFRA_IMAGES=(
  "postgis/postgis:16-3.4-alpine"
  "redis:7.4-alpine"
  "quay.io/minio/minio:RELEASE.2024-12-18T13-15-44Z"
)

for img in "${INFRA_IMAGES[@]}"; do
  info "  Pulling: $img"
  docker pull "$img" || warn "  이미 존재하는 이미지 사용: $img"
  IMAGES+=("$img")
done

# 전체 이미지를 하나의 tar로 저장
info "  이미지 저장 중... (시간 소요)"
docker save "${IMAGES[@]}" | gzip > "${EXPORT_DIR}/images/all-images.tar.gz"
info "  이미지 크기: $(du -sh "${EXPORT_DIR}/images/all-images.tar.gz" | cut -f1)"

# ═══════════════════════════════════════════════════
# 3단계: Swagger UI 오프라인 번들 다운로드
# ═══════════════════════════════════════════════════
info "[3/6] Swagger UI 오프라인 번들 다운로드..."
SWAGGER_VERSION="5.18.2"
REDOC_VERSION="2.1.5"

curl -fsSL "https://cdn.jsdelivr.net/npm/swagger-ui-dist@${SWAGGER_VERSION}/swagger-ui-bundle.js" \
  -o "${EXPORT_DIR}/swagger-ui/swagger-ui-bundle.js"
curl -fsSL "https://cdn.jsdelivr.net/npm/swagger-ui-dist@${SWAGGER_VERSION}/swagger-ui.css" \
  -o "${EXPORT_DIR}/swagger-ui/swagger-ui.css"
curl -fsSL "https://cdn.jsdelivr.net/npm/redoc@${REDOC_VERSION}/bundles/redoc.standalone.js" \
  -o "${EXPORT_DIR}/swagger-ui/redoc.standalone.js"
info "  Swagger UI v${SWAGGER_VERSION}, ReDoc v${REDOC_VERSION} 다운로드 완료"

# ═══════════════════════════════════════════════════
# 4단계: Oracle Instant Client 오프라인 복사
# ═══════════════════════════════════════════════════
info "[4/6] Oracle Instant Client 다운로드..."
ORACLE_IC_URL="https://download.oracle.com/otn_software/linux/instantclient/2115000/instantclient-basiclite-linux.x64-21.15.0.0.0dbru.zip"
if [ -f "${PROJECT_DIR}/backend/vendor/instantclient-basiclite-linux.x64-21.15.0.0.0dbru.zip" ]; then
  cp "${PROJECT_DIR}/backend/vendor/instantclient-basiclite-linux.x64-21.15.0.0.0dbru.zip" \
     "${EXPORT_DIR}/vendor/"
  info "  기존 vendor 파일 복사"
else
  curl -fsSLo "${EXPORT_DIR}/vendor/instantclient-basiclite-linux.x64-21.15.0.0.0dbru.zip" \
    "$ORACLE_IC_URL"
  info "  Oracle Instant Client 다운로드 완료"
fi

# ═══════════════════════════════════════════════════
# 5단계: K8s 매니페스트 + 환경설정 템플릿 복사
# ═══════════════════════════════════════════════════
info "[5/6] K8s 매니페스트 및 설정 파일 복사..."
cp -r "${PROJECT_DIR}/k8s" "${EXPORT_DIR}/k8s"
cp "${PROJECT_DIR}/.env.example" "${EXPORT_DIR}/.env.example"
cp "${PROJECT_DIR}/docker-compose.yml" "${EXPORT_DIR}/docker-compose.yml"

# ═══════════════════════════════════════════════════
# 6단계: 폐쇄망 배포 스크립트 생성
# ═══════════════════════════════════════════════════
info "[6/6] 배포 스크립트 생성..."
cat > "${EXPORT_DIR}/airgap-import.sh" << 'IMPORT_EOF'
#!/usr/bin/env bash
# ═══════════════════════════════════════════════════
# K-water DataHub Portal - 폐쇄망 Import 스크립트
# 폐쇄망에서 실행: Docker 이미지 로드 + 파일 배치
# ═══════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTERNAL_REGISTRY="${INTERNAL_REGISTRY:-registry.kwater.or.kr}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

info "=== 폐쇄망 Import 시작 ==="

# 1. Docker 이미지 로드
info "[1/5] Docker 이미지 로드..."
docker load -i "${SCRIPT_DIR}/images/all-images.tar.gz"

# 2. 내부 레지스트리로 태그 변경 + push
info "[2/5] 내부 레지스트리에 push..."

TAG_MAP=(
  "datahub/frontend:v0.1.0|${INTERNAL_REGISTRY}/datahub/frontend:v0.1.0"
  "datahub/backend:v0.1.0|${INTERNAL_REGISTRY}/datahub/backend:v0.1.0"
  "postgis/postgis:16-3.4-alpine|${INTERNAL_REGISTRY}/postgis/postgis:16-3.4-alpine"
  "redis:7.4-alpine|${INTERNAL_REGISTRY}/redis:7.4-alpine"
  "quay.io/minio/minio:RELEASE.2024-12-18T13-15-44Z|${INTERNAL_REGISTRY}/minio/minio:RELEASE.2024-12-18T13-15-44Z"
)

for entry in "${TAG_MAP[@]}"; do
  SRC="${entry%%|*}"
  DST="${entry##*|}"
  info "  ${SRC} -> ${DST}"
  docker tag "$SRC" "$DST"
  docker push "$DST" || warn "  push 실패 (레지스트리 접근 확인): $DST"
done

# 3. Swagger UI 정적 파일 배치
info "[3/5] Swagger UI 정적 파일 배치..."
TARGET_STATIC=""
if [ -d "/path/to/project/backend/app/static" ]; then
  TARGET_STATIC="/path/to/project/backend/app/static"
else
  read -rp "백엔드 프로젝트 경로 입력 (예: /home/datahub/dataHubPotal2/backend/app/static): " TARGET_STATIC
fi
if [ -d "$TARGET_STATIC" ] || mkdir -p "$TARGET_STATIC"; then
  cp "${SCRIPT_DIR}/swagger-ui/"* "$TARGET_STATIC/"
  info "  Swagger UI 파일 배치 완료: $TARGET_STATIC"
else
  warn "  Swagger UI 파일 수동 배치 필요: ${SCRIPT_DIR}/swagger-ui/ → backend/app/static/"
fi

# 4. Oracle Instant Client 배치
info "[4/5] Oracle Instant Client vendor 배치..."
VENDOR_DIR=""
if [ -d "/path/to/project/backend/vendor" ]; then
  VENDOR_DIR="/path/to/project/backend/vendor"
else
  read -rp "백엔드 vendor 경로 입력 (예: /home/datahub/dataHubPotal2/backend/vendor): " VENDOR_DIR
fi
if [ -d "$VENDOR_DIR" ] || mkdir -p "$VENDOR_DIR"; then
  cp "${SCRIPT_DIR}/vendor/"*.zip "$VENDOR_DIR/" 2>/dev/null || true
  info "  Oracle Instant Client 배치 완료"
else
  warn "  수동 배치 필요: ${SCRIPT_DIR}/vendor/ → backend/vendor/"
fi

# 5. K8s 매니페스트 배포 안내
info "[5/5] K8s 배포 안내"
echo ""
echo "══════════════════════════════════════════════════════"
echo " 남은 수동 작업:"
echo "══════════════════════════════════════════════════════"
echo ""
echo " 1) K8s Secret 생성:"
echo "    kubectl -n datahub create secret generic datahub-secret \\"
echo "      --from-literal=POSTGRES_USER=<DB유저> \\"
echo "      --from-literal=POSTGRES_PASSWORD=<DB비밀번호> \\"
echo "      --from-literal=JWT_SECRET_KEY=\$(openssl rand -hex 32) \\"
echo "      --from-literal=OBJECT_STORAGE_ACCESS_KEY=<MinIO키> \\"
echo "      --from-literal=OBJECT_STORAGE_SECRET_KEY=<MinIO시크릿>"
echo ""
echo " 2) ConfigMap 환경변수 수정 (k8s/configmap.yaml):"
echo "    - DATABASE_URL: 폐쇄망 DB 주소"
echo "    - REDIS_URL: 폐쇄망 Redis 주소"
echo "    - CORS_ORIGINS: 폐쇄망 도메인"
echo "    - SAML_*: 내부 IdP URL"
echo "    - ERP_API_URL: 내부 ERP URL"
echo "    - DISTRIBUTION_API_ENDPOINT: 내부 유통 API URL"
echo ""
echo " 3) Ingress 도메인/TLS 수정 (k8s/ingress.yaml):"
echo "    - host: <폐쇄망 도메인>"
echo "    - cert-manager issuer: 내부 CA"
echo ""
echo " 4) K8s 이미지 참조 확인:"
echo "    - 모든 yaml의 image: ${INTERNAL_REGISTRY}/... 확인"
echo ""
echo " 5) 순서대로 배포:"
echo "    kubectl apply -f k8s/namespace.yaml"
echo "    kubectl apply -f k8s/rbac.yaml"
echo "    kubectl apply -f k8s/secret.yaml  # (Sealed Secret 사용 시 별도)"
echo "    kubectl apply -f k8s/configmap.yaml"
echo "    kubectl apply -f k8s/postgres.yaml"
echo "    kubectl apply -f k8s/redis.yaml"
echo "    kubectl apply -f k8s/minio.yaml"
echo "    kubectl apply -f k8s/migration-job.yaml"
echo "    kubectl apply -f k8s/backend.yaml"
echo "    kubectl apply -f k8s/celery.yaml"
echo "    kubectl apply -f k8s/frontend.yaml"
echo "    kubectl apply -f k8s/ingress.yaml"
echo "    kubectl apply -f k8s/hpa.yaml"
echo "    kubectl apply -f k8s/pdb.yaml"
echo "    kubectl apply -f k8s/networkpolicy.yaml"
echo "    kubectl apply -f k8s/limitrange.yaml"
echo ""
echo "══════════════════════════════════════════════════════"

info "=== Import 완료 ==="
IMPORT_EOF
chmod +x "${EXPORT_DIR}/airgap-import.sh"

# ═══════════════════════════════════════════════════
# 환경변수 변경 체크리스트 생성
# ═══════════════════════════════════════════════════
cat > "${EXPORT_DIR}/CHECKLIST.md" << 'CHECKLIST_EOF'
# 폐쇄망 이전 체크리스트

## 이전 전 (인터넷망)
- [ ] `airgap-export.sh` 실행 완료
- [ ] 생성된 tar.gz 파일 USB/망간자료전송 준비

## 이전 후 (폐쇄망)
- [ ] `airgap-import.sh` 실행 → Docker 이미지 로드 + 레지스트리 push
- [ ] K8s Secret 생성 (DB/JWT/MinIO 크리덴셜)
- [ ] ConfigMap 환경변수 수정:
  - [ ] `DATABASE_URL` → 폐쇄망 PostgreSQL 주소
  - [ ] `DATABASE_URL_SYNC` → 동기 연결 문자열
  - [ ] `REDIS_URL` → 폐쇄망 Redis 주소
  - [ ] `CORS_ORIGINS` → 폐쇄망 도메인 (예: `["https://datahub.internal.kwater.or.kr"]`)
  - [ ] `SAML_SP_ENTITY_ID` → 폐쇄망 SP 도메인
  - [ ] `SAML_SP_ACS_URL` → 폐쇄망 ACS URL
  - [ ] `SAML_IDP_ENTITY_ID` → 내부 IdP Entity ID
  - [ ] `SAML_IDP_SSO_URL` → 내부 IdP SSO URL
  - [ ] `ERP_API_URL` → 내부 ERP API
  - [ ] `DISTRIBUTION_API_ENDPOINT` → 내부 유통 API
  - [ ] `OBJECT_STORAGE_ENDPOINT` → 폐쇄망 MinIO 주소
- [ ] Ingress 수정:
  - [ ] `host: datahub.kwater.or.kr` → 폐쇄망 도메인
  - [ ] `cert-manager.io/cluster-issuer` → 내부 CA ClusterIssuer
- [ ] K8s 이미지 참조 → 내부 레지스트리 경로 확인
- [ ] Alembic 마이그레이션 실행 확인
- [ ] Swagger UI 정적 파일 배치 확인 (`/docs` 접속 테스트)
- [ ] 시드 데이터 투입 (필요 시)
- [ ] 기능 테스트:
  - [ ] 로그인/SSO
  - [ ] 대시보드 조회
  - [ ] 데이터 카탈로그 검색
  - [ ] API 키 발급
  - [ ] 데이터 다운로드

## 롤백
- 이전 버전 이미지 태그로 Deployment 롤백: `kubectl rollout undo deployment/<name> -n datahub`
CHECKLIST_EOF

# 최종 아카이브 생성
info "최종 아카이브 생성: ${ARCHIVE_NAME}"
cd "$(dirname "$EXPORT_DIR")"
tar czf "${ARCHIVE_NAME}" "$(basename "$EXPORT_DIR")"

info "=== 완료 ==="
info "아카이브: $(dirname "$EXPORT_DIR")/${ARCHIVE_NAME}"
info "크기: $(du -sh "$(dirname "$EXPORT_DIR")/${ARCHIVE_NAME}" | cut -f1)"
echo ""
echo "다음 단계: ${ARCHIVE_NAME} 을 USB 또는 망간자료전송으로 폐쇄망에 전달 후"
echo "  tar xzf ${ARCHIVE_NAME} && cd $(basename "$EXPORT_DIR") && ./airgap-import.sh"
