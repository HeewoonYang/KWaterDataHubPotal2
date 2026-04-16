# K-water DataHub Portal - Kubernetes 배포

## 구조

```
k8s/
├── namespace.yaml    # datahub 네임스페이스
├── configmap.yaml    # 환경변수 (DB URL, Redis, CORS 등)
├── secret.yaml       # 비밀정보 (DB 비밀번호, JWT 키)
├── postgres.yaml     # PostgreSQL 16 + PVC (20Gi)
├── redis.yaml        # Redis 7
├── backend.yaml      # FastAPI (replicas: 2)
├── frontend.yaml     # Vue3+Nginx (replicas: 2)
├── celery.yaml       # Celery Worker (replicas: 2) + Beat (replicas: 1)
├── ingress.yaml      # Nginx Ingress (datahub.kwater.or.kr)
├── hpa.yaml          # HPA (backend: 2~8, worker: 2~6)
├── deploy.sh         # 배포 스크립트
└── README.md
```

## Docker → K8S 흐름

```
1. 로컬 개발/테스트 (Docker Compose)
   docker compose up -d --build
   http://localhost:8088

2. 이미지 빌드 + 레지스트리 Push
   TAG=v1.0.0 ./k8s/deploy.sh build
   TAG=v1.0.0 ./k8s/deploy.sh push

3. K8S 클러스터 배포
   TAG=v1.0.0 ./k8s/deploy.sh apply

4. 상태 확인
   ./k8s/deploy.sh status

5. 롤링 업데이트
   ./k8s/deploy.sh rollout
```

## 동일 이미지 원칙

| 환경 | 이미지 | 설정 |
|------|--------|------|
| Docker (테스트) | `frontend:latest` / `backend:latest` | docker-compose.yml (환경변수) |
| K8S (운영) | `registry.kwater.or.kr/datahub/frontend:v1.0.0` | configmap.yaml + secret.yaml |

**Dockerfile은 동일**, 환경변수만 다름.

## 리소스 할당

| Pod | Replicas | CPU (req/limit) | Memory (req/limit) |
|-----|----------|-----------------|---------------------|
| backend | 2~8 (HPA) | 250m / 2 | 512Mi / 2Gi |
| frontend | 2 | 100m / 500m | 128Mi / 512Mi |
| celery-worker | 2~6 (HPA) | 250m / 2 | 512Mi / 2Gi |
| celery-beat | 1 | 100m / 500m | 256Mi / 512Mi |
| postgres | 1 | 250m / 1 | 512Mi / 2Gi |
| redis | 1 | 100m / 500m | 128Mi / 512Mi |

## 사전 요구사항

- K8S 클러스터 (1.28+)
- Nginx Ingress Controller
- Container Registry (`registry.kwater.or.kr` 또는 변경)
- kubectl 설정 완료
- PV Provisioner (PVC 지원)

## 커스터마이징

- **도메인 변경**: `ingress.yaml`의 `datahub.kwater.or.kr` 수정
- **레지스트리 변경**: `deploy.sh`의 `REGISTRY` 변수 수정
- **DB 비밀번호 변경**: `secret.yaml` 수정 후 `kubectl apply`
- **스케일링 조정**: `hpa.yaml`의 min/max replicas 변경
