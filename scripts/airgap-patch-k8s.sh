#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# K-water DataHub Portal - K8s 매니페스트 폐쇄망 패치
# k8s/*.yaml 의 이미지 참조와 도메인을 폐쇄망 환경에 맞게 일괄 변경
#
# 사용법:
#   ./airgap-patch-k8s.sh                     # 대화형 (질문 후 패치)
#   ./airgap-patch-k8s.sh --registry reg.internal:5000 --domain datahub.internal.kwater.or.kr --issuer internal-ca
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K8S_DIR="$(dirname "$SCRIPT_DIR")/k8s"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info() { echo -e "${GREEN}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }

# 기본값
REGISTRY=""
DOMAIN=""
ISSUER=""

# 인자 파싱
while [[ $# -gt 0 ]]; do
  case $1 in
    --registry) REGISTRY="$2"; shift 2;;
    --domain)   DOMAIN="$2"; shift 2;;
    --issuer)   ISSUER="$2"; shift 2;;
    *) echo "Unknown option: $1"; exit 1;;
  esac
done

# 대화형 입력 (인자 미전달 시)
if [ -z "$REGISTRY" ]; then
  read -rp "내부 레지스트리 주소 (예: registry.kwater.or.kr): " REGISTRY
fi
if [ -z "$DOMAIN" ]; then
  read -rp "폐쇄망 도메인 (예: datahub.internal.kwater.or.kr): " DOMAIN
fi
if [ -z "$ISSUER" ]; then
  read -rp "TLS ClusterIssuer 이름 (예: internal-ca) [기본: internal-ca]: " ISSUER
  ISSUER="${ISSUER:-internal-ca}"
fi

info "=== K8s 매니페스트 패치 ==="
info "  레지스트리: ${REGISTRY}"
info "  도메인: ${DOMAIN}"
info "  TLS Issuer: ${ISSUER}"

# ── 이미지 교체 ──
info "[1/4] 이미지 참조 교체..."

# backend.yaml, frontend.yaml → 내부 레지스트리
sed -i "s|image: registry.kwater.or.kr/datahub/backend:|image: ${REGISTRY}/datahub/backend:|g" "${K8S_DIR}/backend.yaml" 2>/dev/null || true
sed -i "s|image: registry.kwater.or.kr/datahub/frontend:|image: ${REGISTRY}/datahub/frontend:|g" "${K8S_DIR}/frontend.yaml" 2>/dev/null || true

# 인프라 이미지
sed -i "s|image: postgres:16.4-alpine|image: ${REGISTRY}/postgres:16.4-alpine|g" "${K8S_DIR}/postgres.yaml" 2>/dev/null || true
sed -i "s|image: postgis/postgis:16-3.4-alpine|image: ${REGISTRY}/postgis/postgis:16-3.4-alpine|g" "${K8S_DIR}/postgres.yaml" 2>/dev/null || true
sed -i "s|image: redis:7.4-alpine|image: ${REGISTRY}/redis:7.4-alpine|g" "${K8S_DIR}/redis.yaml" 2>/dev/null || true
sed -i "s|image: quay.io/minio/minio:|image: ${REGISTRY}/minio/minio:|g" "${K8S_DIR}/minio.yaml" 2>/dev/null || true

# celery (backend 이미지 사용)
sed -i "s|image: registry.kwater.or.kr/datahub/backend:|image: ${REGISTRY}/datahub/backend:|g" "${K8S_DIR}/celery.yaml" 2>/dev/null || true
sed -i "s|image: registry.kwater.or.kr/datahub/backend:|image: ${REGISTRY}/datahub/backend:|g" "${K8S_DIR}/migration-job.yaml" 2>/dev/null || true

# ── 도메인 교체 ──
info "[2/4] 도메인 교체..."
sed -i "s|datahub.kwater.or.kr|${DOMAIN}|g" "${K8S_DIR}/ingress.yaml"

# ConfigMap CORS/SAML 도메인도 교체
sed -i "s|https://datahub.kwater.or.kr|https://${DOMAIN}|g" "${K8S_DIR}/configmap.yaml"

# ── TLS Issuer 교체 ──
info "[3/4] TLS ClusterIssuer 교체..."
sed -i "s|cert-manager.io/cluster-issuer: \"letsencrypt-prod\"|cert-manager.io/cluster-issuer: \"${ISSUER}\"|g" "${K8S_DIR}/ingress.yaml"

# ── ImagePullSecret 추가 (없으면) ──
info "[4/4] ImagePullSecret 확인..."
for f in backend.yaml frontend.yaml celery.yaml migration-job.yaml; do
  filepath="${K8S_DIR}/${f}"
  if [ -f "$filepath" ] && ! grep -q "imagePullSecrets" "$filepath"; then
    warn "  ${f}: imagePullSecrets 미설정 — 수동 추가 필요"
    echo "  # 다음 내용을 spec.template.spec 하위에 추가:"
    echo "  #   imagePullSecrets:"
    echo "  #     - name: registry-credentials"
  fi
done

info "=== 패치 완료 ==="
echo ""
echo "변경된 파일 확인:"
cd "${K8S_DIR}" && git diff --stat . 2>/dev/null || ls -la *.yaml
echo ""
echo "다음 단계:"
echo "  1) imagePullSecrets 수동 추가 (필요 시)"
echo "  2) kubectl apply -f k8s/ 순서대로 배포"
