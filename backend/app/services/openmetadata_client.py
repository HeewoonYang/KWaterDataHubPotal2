"""OpenMetadata REST API 경량 클라이언트 + 동기화 서비스 (REQ-DHUB-005-003-6).

- catalog_dataset → OM Table entity PUT
- catalog_lineage  → OM Lineage edge PUT
- migration_audit_log → OM PipelineStatus/CustomProperty 로 감사이력 전송
- 모든 호출 결과는 openmetadata_sync_log 에 기록

운영 환경: config.OPENMETADATA_URL 과 JWT_TOKEN 필수.
미설정/네트워크 실패 시 SKIPPED 상태로 로그만 남기고 계속 진행 (fail-safe).
"""
from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime
from typing import Any, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.catalog import CatalogColumn, CatalogDataset, CatalogLineage
from app.models.dr import OpenmetadataSyncLog

logger = logging.getLogger(__name__)


class OpenMetadataClient:
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None, timeout: float = 10.0):
        self.base_url = (base_url or getattr(settings, "OPENMETADATA_URL", None) or "").rstrip("/")
        self.token = token or getattr(settings, "OPENMETADATA_JWT_TOKEN", None)
        self.timeout = timeout

    @property
    def enabled(self) -> bool:
        return bool(self.base_url and self.token)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}" if self.token else "",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(self, method: str, path: str, json: Optional[dict] = None) -> tuple[int, Any]:
        if not self.enabled:
            return 0, {"skipped": True, "reason": "OPENMETADATA_URL 또는 JWT_TOKEN 미설정"}
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.request(method, url, headers=self._headers(), json=json)
                try:
                    data = resp.json()
                except Exception:
                    data = {"raw": resp.text[:500]}
                return resp.status_code, data
        except Exception as e:
            return 0, {"error": str(e)[:500]}

    # ── entity helpers ────────────────────────────────────────────
    def put_table(self, dataset: CatalogDataset, columns: list[CatalogColumn], service_name: str = "kwater-datahub") -> tuple[int, Any]:
        """catalog_dataset → OM Table entity upsert."""
        db_name = (dataset.source_system or "default").replace(" ", "_").lower()
        fqn = f"{service_name}.{db_name}.public.{dataset.dataset_name}"
        payload = {
            "name": dataset.dataset_name,
            "displayName": dataset.dataset_name_kr or dataset.dataset_name,
            "description": dataset.description or "",
            "tableType": "Regular",
            "databaseSchema": f"{service_name}.{db_name}.public",
            "columns": [{
                "name": c.column_name,
                "displayName": c.column_name_kr or c.column_name,
                "dataType": (c.data_type or "VARCHAR").upper(),
                "dataLength": c.length or 0,
                "description": c.description or "",
                "tags": [],
            } for c in columns],
            "tags": [],
            "customProperties": {
                "hub_dataset_id": str(dataset.id),
                "classification_id": str(dataset.classification_id) if dataset.classification_id else "",
                "grade_id": str(dataset.grade_id) if dataset.grade_id else "",
                "owner_department": dataset.owner_department or "",
                "hub_fqn": fqn,
                "hub_om_fqn": dataset.openmetadata_fqn or "",
            },
        }
        return self._request("PUT", "/api/v1/tables", payload)

    def put_lineage(self, upstream_fqn: str, downstream_fqn: str, pipeline_fqn: Optional[str] = None) -> tuple[int, Any]:
        payload = {
            "edge": {
                "fromEntity": {"id": upstream_fqn, "type": "table"},
                "toEntity": {"id": downstream_fqn, "type": "table"},
                "lineageDetails": {"pipeline": {"id": pipeline_fqn, "type": "pipeline"} if pipeline_fqn else None,
                                    "sqlQuery": ""},
            }
        }
        return self._request("PUT", "/api/v1/lineage", payload)

    def push_audit(self, entity_type: str, entity_id: str, event: dict[str, Any]) -> tuple[int, Any]:
        """감사이벤트 송신 (OM의 activity feed / threads API 사용 가능)."""
        payload = {"entityId": entity_id, "entityType": entity_type, "event": event}
        return self._request("POST", "/api/v1/feed", payload)


# ── 동기화 서비스 레이어 ─────────────────────────────────────────
_client = OpenMetadataClient()


def sync_catalog_dataset(db: Session, dataset_id: uuid.UUID) -> OpenmetadataSyncLog:
    """catalog_dataset 과 컬럼을 OM 에 PUT 하고 로그 기록."""
    dataset = db.execute(select(CatalogDataset).where(CatalogDataset.id == dataset_id)).scalar_one_or_none()
    if not dataset:
        return _log_sync(db, "TABLE", dataset_id, None, "SKIPPED", 0, "dataset 없음", None, None)

    columns = db.execute(select(CatalogColumn).where(CatalogColumn.dataset_id == dataset_id)).scalars().all()

    payload_name = dataset.dataset_name
    t0 = time.time()
    status_code, resp = _client.put_table(dataset, list(columns))
    duration = int((time.time() - t0) * 1000)

    status = _classify_status(status_code, resp)
    return _log_sync(db, "TABLE", dataset_id, payload_name, status, status_code,
                        (resp or {}).get("error") or (None if status == "SUCCESS" else str(resp)[:500]),
                        {"dataset_id": str(dataset_id), "cols": len(columns)}, resp,
                        duration_ms=duration)


def sync_catalog_lineage(db: Session, lineage_id: uuid.UUID) -> OpenmetadataSyncLog:
    lineage = db.execute(select(CatalogLineage).where(CatalogLineage.id == lineage_id)).scalar_one_or_none()
    if not lineage:
        return _log_sync(db, "LINEAGE", lineage_id, None, "SKIPPED", 0, "lineage 없음", None, None)

    upstream_fqn = str(lineage.upstream_dataset_id or "")
    downstream_fqn = str(lineage.downstream_dataset_id or "")
    t0 = time.time()
    status_code, resp = _client.put_lineage(upstream_fqn, downstream_fqn)
    duration = int((time.time() - t0) * 1000)
    status = _classify_status(status_code, resp)
    return _log_sync(db, "LINEAGE", lineage_id, f"{upstream_fqn}→{downstream_fqn}",
                        status, status_code, (resp or {}).get("error") or None,
                        {"upstream": upstream_fqn, "downstream": downstream_fqn}, resp,
                        duration_ms=duration)


def sync_migration_audit(db: Session, migration_id: uuid.UUID, action: str, details: dict) -> OpenmetadataSyncLog:
    """이관 감사 이벤트 OM 송신."""
    t0 = time.time()
    status_code, resp = _client.push_audit("migration", str(migration_id), {"action": action, **details})
    duration = int((time.time() - t0) * 1000)
    status = _classify_status(status_code, resp)
    return _log_sync(db, "AUDIT", migration_id, f"migration.{action}", status, status_code,
                        None, {"migration_id": str(migration_id), "action": action, **details}, resp,
                        duration_ms=duration)


def _classify_status(status_code: int, resp: Any) -> str:
    if isinstance(resp, dict) and resp.get("skipped"):
        return "SKIPPED"
    if 200 <= status_code < 300:
        return "SUCCESS"
    if status_code == 0:
        return "FAIL"   # 네트워크/미설정
    return "FAIL"


def _log_sync(
    db: Session, entity_type: str, entity_id: Optional[uuid.UUID], entity_name: Optional[str],
    status: str, http_status: int, error_message: Optional[str],
    payload: Optional[dict], response: Any, duration_ms: Optional[int] = None,
) -> OpenmetadataSyncLog:
    log = OpenmetadataSyncLog(
        id=uuid.uuid4(),
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        sync_direction="PUSH",
        operation="UPSERT",
        status=status,
        http_status=http_status or None,
        error_message=error_message,
        payload=payload,
        response=(response if isinstance(response, (dict, list)) else {"raw": str(response)[:500]}),
        started_at=datetime.now(),
        duration_ms=duration_ms,
    )
    db.add(log)
    db.flush()
    return log


def sync_pending_all(db: Session, limit: int = 50) -> dict[str, int]:
    """PENDING 상태 로그를 재시도 + 최근 catalog/lineage 대상 누락분 동기화."""
    # 우선 PENDING 재시도 (재시도 자체가 PENDING 상태를 UPSERT 로 재발송)
    pending = db.execute(
        select(OpenmetadataSyncLog).where(OpenmetadataSyncLog.status == "PENDING").limit(limit)
    ).scalars().all()
    retried = 0
    for p in pending:
        if p.entity_type == "TABLE" and p.entity_id:
            sync_catalog_dataset(db, p.entity_id)
            retried += 1
        elif p.entity_type == "LINEAGE" and p.entity_id:
            sync_catalog_lineage(db, p.entity_id)
            retried += 1
    db.commit()
    return {"retried": retried}
