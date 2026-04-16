#!/bin/bash
# K-water DataHub Portal - Kubernetes 배포 스크립트
# 사용법: ./k8s/deploy.sh [build|apply|all|status|delete]

set -e

REGISTRY="registry.kwater.or.kr/datahub"
TAG="${TAG:-latest}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "============================================"
echo "  K-water DataHub Portal - K8S Deploy"
echo "  Registry: $REGISTRY"
echo "  Tag: $TAG"
echo "============================================"

case "${1:-all}" in
  build)
    echo ""
    echo ">>> Building Docker images..."
    docker build -t $REGISTRY/frontend:$TAG -f "$PROJECT_DIR/frontend/Dockerfile" "$PROJECT_DIR/frontend"
    docker build -t $REGISTRY/backend:$TAG -f "$PROJECT_DIR/backend/Dockerfile" "$PROJECT_DIR/backend"
    echo ">>> Images built successfully"
    ;;

  push)
    echo ""
    echo ">>> Pushing images to registry..."
    docker push $REGISTRY/frontend:$TAG
    docker push $REGISTRY/backend:$TAG
    echo ">>> Images pushed successfully"
    ;;

  apply)
    echo ""
    echo ">>> Applying K8S manifests..."
    kubectl apply -f "$SCRIPT_DIR/namespace.yaml"
    kubectl apply -f "$SCRIPT_DIR/configmap.yaml"
    kubectl apply -f "$SCRIPT_DIR/secret.yaml"
    kubectl apply -f "$SCRIPT_DIR/postgres.yaml"
    kubectl apply -f "$SCRIPT_DIR/redis.yaml"
    echo ">>> Waiting for DB ready..."
    kubectl wait --for=condition=ready pod -l app=postgres -n datahub --timeout=60s
    kubectl apply -f "$SCRIPT_DIR/backend.yaml"
    kubectl apply -f "$SCRIPT_DIR/frontend.yaml"
    kubectl apply -f "$SCRIPT_DIR/celery.yaml"
    kubectl apply -f "$SCRIPT_DIR/ingress.yaml"
    kubectl apply -f "$SCRIPT_DIR/hpa.yaml"
    echo ">>> All manifests applied"
    ;;

  all)
    $0 build
    $0 push
    $0 apply
    ;;

  status)
    echo ""
    echo ">>> Cluster Status"
    kubectl get all -n datahub
    echo ""
    kubectl get ingress -n datahub
    echo ""
    kubectl top pods -n datahub 2>/dev/null || true
    ;;

  rollout)
    echo ""
    echo ">>> Rolling update..."
    kubectl rollout restart deployment/backend -n datahub
    kubectl rollout restart deployment/frontend -n datahub
    kubectl rollout restart deployment/celery-worker -n datahub
    kubectl rollout status deployment/backend -n datahub --timeout=120s
    kubectl rollout status deployment/frontend -n datahub --timeout=120s
    echo ">>> Rollout complete"
    ;;

  delete)
    echo ""
    echo ">>> Deleting all resources..."
    kubectl delete namespace datahub --ignore-not-found
    echo ">>> Deleted"
    ;;

  *)
    echo "Usage: $0 [build|push|apply|all|status|rollout|delete]"
    echo ""
    echo "  build   - Build Docker images"
    echo "  push    - Push images to registry"
    echo "  apply   - Apply K8S manifests"
    echo "  all     - Build + Push + Apply"
    echo "  status  - Show cluster status"
    echo "  rollout - Rolling restart all deployments"
    echo "  delete  - Delete all resources"
    exit 1
    ;;
esac

echo ""
echo ">>> Done!"
