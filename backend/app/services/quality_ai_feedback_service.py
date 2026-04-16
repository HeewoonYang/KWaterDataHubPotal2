"""품질 결과 → 생성형 AI 학습 피드백 서비스 (REQ-DHUB-004-004 002)

품질 검증 결과 중 저점수·실패 항목을 구조화된 학습 페이로드로 변환해
`quality_ai_feedback` 테이블에 축적하고, 주기적으로 대상 AI 시스템(LLM/RAG/T2SQL) 으로 발송한다.

Dispatch 어댑터:
- STUB (기본): stdout JSON + OperationAiQueryLog 에 합성 학습 질의로 기록
- HTTP: OperationAiModelConfig.endpoint_url 로 POST (본 범위에서는 stub 기반 구현만 완성,
  HTTP 어댑터는 env 전환 지점만 제공)

멱등성: 동일 (source_result_id, target_system) 쌍에 대해 중복 생성 방지.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.catalog import CatalogColumn, CatalogDataset
from app.models.classification import DataClassification, DataGrade
from app.models.distribution import DistributionDataset
from app.models.operation import OperationAiModelConfig, OperationAiQueryLog
from app.models.quality import QualityAiFeedback, QualityCheckResult, QualityRule

logger = logging.getLogger(__name__)

TARGET_SYSTEMS = ("LLM", "RAG", "T2SQL")


# ── 페이로드 생성 ──────────────────────────────────────────────────────
def build_feedback_payload(
    db: Session, result: QualityCheckResult, target_system: str
) -> dict:
    """학습 피드백 JSON 페이로드 생성.

    구조:
    {
      "dataset": {id, name, name_kr, classification, grade, owner_department},
      "quality": {score, check_type, error_count, total_count, failed_details},
      "distribution": {...}  # 유통 결과인 경우만
      "rule": {...}          # 규칙 기반이면
      "recommendation": {type, fix_hint, priority},
      "target_system": "LLM" | "RAG" | "T2SQL",
      "generated_at": "..."
    }
    """
    payload: dict = {
        "target_system": target_system,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "quality": {
            "result_id": result.id,
            "score": float(result.score) if result.score is not None else None,
            "check_type": result.check_type,
            "error_count": result.error_count,
            "total_count": result.total_count,
            "executed_at": result.executed_at.isoformat() if result.executed_at else None,
            "details": result.details or {},
        },
    }

    # 원본 카탈로그 메타
    if result.catalog_dataset_id:
        cat = db.execute(
            select(CatalogDataset).where(CatalogDataset.id == result.catalog_dataset_id)
        ).scalar_one_or_none()
        if cat:
            cls_name = None
            if cat.classification_id is not None:
                c = db.execute(
                    select(DataClassification).where(DataClassification.id == cat.classification_id)
                ).scalar_one_or_none()
                cls_name = c.name if c else None
            grade_code = None
            if cat.grade_id is not None:
                g = db.execute(
                    select(DataGrade).where(DataGrade.id == cat.grade_id)
                ).scalar_one_or_none()
                grade_code = g.grade_code if g else None

            columns = db.execute(
                select(CatalogColumn).where(CatalogColumn.dataset_id == cat.id)
            ).scalars().all()
            payload["dataset"] = {
                "id": str(cat.id),
                "name": cat.dataset_name,
                "name_kr": cat.dataset_name_kr,
                "description": cat.description,
                "classification": cls_name,
                "grade": grade_code,
                "owner_department": cat.owner_department,
                "source_system": cat.source_system,
                "column_count": len(columns),
                "columns_sample": [
                    {"name": c.column_name, "name_kr": c.column_name_kr, "data_type": c.data_type}
                    for c in columns[:20]
                ],
            }

    # 유통 정보
    if result.distribution_dataset_id:
        dist = db.execute(
            select(DistributionDataset).where(DistributionDataset.id == result.distribution_dataset_id)
        ).scalar_one_or_none()
        if dist:
            payload["distribution"] = {
                "id": str(dist.id),
                "distribution_name": dist.distribution_name,
                "is_downloadable": dist.is_downloadable,
                "allowed_formats": dist.allowed_formats,
                "requires_approval": dist.requires_approval,
                "status": dist.status,
            }

    # 규칙 정보
    if result.rule_id:
        rule = db.execute(
            select(QualityRule).where(QualityRule.id == result.rule_id)
        ).scalar_one_or_none()
        if rule:
            payload["rule"] = {
                "id": rule.id,
                "name": rule.rule_name,
                "type": rule.rule_type,
                "severity": rule.severity,
            }

    # 권장 조치 (target_system 별 특화)
    payload["recommendation"] = _build_recommendation(result, target_system)
    return payload


def _build_recommendation(result: QualityCheckResult, target_system: str) -> dict:
    score = float(result.score) if result.score is not None else 0.0
    details = result.details or {}
    missing_kr = details.get("missing_kr_columns") or []
    missing_meta = details.get("missing_meta_fields") or []
    failed_checks = details.get("failed_checks") or []

    rec_type = "LOW_SCORE"
    if missing_kr or "column_name_kr" in str(missing_meta):
        rec_type = "MISSING_METADATA"
    elif failed_checks:
        rec_type = "STANDARD_VIOLATION"

    if target_system == "LLM":
        hint = (
            "이 데이터셋 설명/한글명 보정에 참고하여 생성형 답변의 정확도를 개선하세요."
            if rec_type == "MISSING_METADATA"
            else "품질 미흡 데이터셋 제외 또는 신뢰도 가중치 하향 조정 권장."
        )
    elif target_system == "RAG":
        hint = (
            "한글명/설명이 채워지면 재인덱싱하고 현재는 검색 랭킹을 낮추세요."
            if rec_type == "MISSING_METADATA"
            else "품질 점수(score) 를 검색 re-ranking feature 로 가중 반영하세요."
        )
    else:  # T2SQL
        hint = (
            "컬럼 한글명이 부족하여 자연어→SQL 매핑 신뢰도가 낮습니다. 이 데이터셋의 few-shot 예시 사용을 보류하세요."
            if rec_type == "MISSING_METADATA"
            else "해당 데이터셋 샘플을 T2SQL 학습 예시에서 필터링하세요."
        )

    priority = "HIGH" if score < 60 else ("MEDIUM" if score < 80 else "LOW")
    return {
        "type": rec_type,
        "priority": priority,
        "fix_hint": hint,
        "auto_applicable": rec_type == "MISSING_METADATA",
    }


# ── 큐잉 ───────────────────────────────────────────────────────────────
def enqueue_feedback_for_result(db: Session, result: QualityCheckResult) -> int:
    """하나의 QualityCheckResult 에 대해 PENDING 피드백 3건(LLM/RAG/T2SQL) 생성.

    임계치(QUALITY_AI_FEEDBACK_THRESHOLD) 미만 점수 또는 error_count > 0 인 경우만 생성.
    동일 (source_result_id, target_system) 쌍이 이미 있으면 건너뜀(멱등).
    """
    threshold = float(settings.QUALITY_AI_FEEDBACK_THRESHOLD)
    score = float(result.score) if result.score is not None else 0.0
    error_count = result.error_count or 0
    if score >= threshold and error_count == 0:
        return 0  # 충분히 양호 → 학습 페이로드 생성 안 함

    feedback_type = _determine_feedback_type(result)
    created = 0
    for target in TARGET_SYSTEMS:
        existing = db.execute(
            select(QualityAiFeedback).where(
                QualityAiFeedback.source_result_id == result.id,
                QualityAiFeedback.target_system == target,
                QualityAiFeedback.is_deleted == False,  # noqa: E712
            )
        ).scalar_one_or_none()
        if existing:
            continue
        payload = build_feedback_payload(db, result, target)
        db.add(QualityAiFeedback(
            id=uuid.uuid4(),
            source_result_id=result.id,
            target_system=target,
            feedback_type=feedback_type,
            payload=payload,
            dispatch_status="PENDING",
            created_at=datetime.now(),
        ))
        created += 1
    db.flush()
    logger.info(
        "AI feedback enqueued: result_id=%s score=%.1f created=%d",
        result.id, score, created,
    )
    return created


def _determine_feedback_type(result: QualityCheckResult) -> str:
    score = float(result.score or 0)
    details = result.details or {}
    if (details.get("missing_kr_columns") or details.get("missing_meta_fields")):
        return "MISSING_METADATA"
    if details.get("failed_checks"):
        return "STANDARD_VIOLATION"
    if score < 60:
        return "LOW_SCORE"
    return "FAILURE_PATTERN"


# ── 발송 ──────────────────────────────────────────────────────────────
def dispatch_pending(db: Session, limit: Optional[int] = None) -> dict:
    """PENDING 피드백을 설정된 provider 로 전송.

    Returns: {"sent": N, "failed": M, "skipped": K}
    """
    batch = limit or int(settings.QUALITY_AI_FEEDBACK_BATCH)
    rows = db.execute(
        select(QualityAiFeedback).where(
            QualityAiFeedback.dispatch_status == "PENDING",
            QualityAiFeedback.is_deleted == False,  # noqa: E712
        ).limit(batch)
    ).scalars().all()

    if not rows:
        return {"sent": 0, "failed": 0, "skipped": 0}

    provider = (settings.QUALITY_AI_FEEDBACK_DISPATCH or "STUB").upper()
    sent = failed = skipped = 0
    now = datetime.now()

    # 발송된 원본 result id 를 모아 한번에 업데이트
    touched_result_ids: set[int] = set()

    for row in rows:
        try:
            if provider == "HTTP":
                ok, err = _dispatch_http(db, row)
            else:
                ok, err = _dispatch_stub(db, row)
            if ok:
                row.dispatch_status = "SENT"
                row.dispatched_at = now
                row.dispatch_error = None
                sent += 1
                touched_result_ids.add(row.source_result_id)
            else:
                row.dispatch_status = "FAILED"
                row.dispatch_error = err
                failed += 1
        except Exception as e:
            row.dispatch_status = "FAILED"
            row.dispatch_error = f"{type(e).__name__}: {e}"
            failed += 1
            logger.exception("dispatch_pending error: feedback_id=%s", row.id)

    # 원본 result 의 AI 반영 플래그/가중치 개별 갱신
    for rid in touched_result_ids:
        rr = db.execute(
            select(QualityCheckResult).where(QualityCheckResult.id == rid)
        ).scalar_one_or_none()
        if not rr:
            continue
        rr.ai_feedback_used = True
        rr.ai_feedback_at = now
        # 학습 기여 가중치: 100 - score (낮은 점수가 더 가치있는 학습 신호)
        if rr.score is not None:
            rr.ai_training_score = Decimal(str(max(0.0, min(100.0, 100.0 - float(rr.score)))))
    db.flush()
    logger.info("AI feedback dispatch summary: sent=%d failed=%d skipped=%d", sent, failed, skipped)
    return {"sent": sent, "failed": failed, "skipped": skipped}


def _dispatch_stub(db: Session, row: QualityAiFeedback) -> tuple[bool, Optional[str]]:
    """stdout JSON + OperationAiQueryLog 기록."""
    try:
        logger.info(
            "QUALITY_AI_FEEDBACK_STUB_SEND %s",
            json.dumps(
                {
                    "feedback_id": str(row.id),
                    "target": row.target_system,
                    "type": row.feedback_type,
                    "payload_keys": list((row.payload or {}).keys()),
                    "result_id": row.source_result_id,
                },
                ensure_ascii=False,
            ),
        )
        # 학습 질의 합성: LLM/RAG/T2SQL 중 LLM 만 대표로 로그
        if row.target_system == "LLM":
            payload = row.payload or {}
            ds = (payload.get("dataset") or {})
            query_text = (
                f"[품질피드백] dataset={ds.get('name_kr') or ds.get('name')} "
                f"score={payload.get('quality', {}).get('score')} "
                f"type={row.feedback_type}"
            )
            db.add(OperationAiQueryLog(
                id=uuid.uuid4(),
                user_id=None,
                query_text=query_text,
                query_type="QUALITY_FEEDBACK",
                response_text=None,
                model_name="stub",
                token_count=None,
                response_time_ms=0,
                satisfaction_rating=None,
                queried_at=datetime.now(),
            ))
        return True, None
    except Exception as e:
        return False, str(e)


def _dispatch_http(db: Session, row: QualityAiFeedback) -> tuple[bool, Optional[str]]:
    """OperationAiModelConfig.endpoint_url 로 POST 하는 HTTP 어댑터 (골격)."""
    cfg = db.execute(
        select(OperationAiModelConfig).where(
            OperationAiModelConfig.model_type == "LLM" if row.target_system == "LLM" else OperationAiModelConfig.model_type == row.target_system,
            OperationAiModelConfig.is_active == True,  # noqa: E712
        ).limit(1)
    ).scalar_one_or_none()
    if not cfg or not cfg.endpoint_url:
        return False, f"no active endpoint for target={row.target_system}"
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(cfg.endpoint_url, json={"feedback": row.payload, "type": row.feedback_type})
            resp.raise_for_status()
        return True, None
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
