"""품질검증 서비스 - 카탈로그/수집/유통 데이터셋에 대한 품질 검증 로직

기존 tasks/quality_tasks.py 의 내부 함수를 서비스 계층으로 옮겨 재사용성을 확보한다.
동기 Session 기반으로 설계하여 Celery 워커(SyncSessionLocal)와 API(async wrapper) 양쪽에서 쓸 수 있다.
"""
from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.catalog import CatalogColumn, CatalogDataset
from app.models.classification import DataClassification, DataGrade
from app.models.distribution import DistributionDataset
from app.models.quality import QualityCheckResult, QualityRule

logger = logging.getLogger(__name__)

# 점수 라벨
SCORE_GOOD = 80.0
SCORE_WARN = 60.0


# ── 카탈로그 완성도 ───────────────────────────────────────────────────
def check_catalog_completeness(
    db: Session, catalog_dataset_id: UUID | str
) -> Optional[QualityCheckResult]:
    """카탈로그 데이터셋의 메타데이터 완성도 검증.

    검사 항목:
    - 컬럼 한글명(column_name_kr) 완성도
    - 데이터셋 메타(한글명/분류/등급/설명/소유부서) 완성도
    """
    dataset = db.execute(
        select(CatalogDataset).where(CatalogDataset.id == str(catalog_dataset_id))
    ).scalar_one_or_none()
    if not dataset:
        return None

    columns = db.execute(
        select(CatalogColumn).where(CatalogColumn.dataset_id == dataset.id)
    ).scalars().all()

    # 컬럼 한글명 완성도
    col_total = max(len(columns), 1)
    col_complete = sum(1 for c in columns if c.column_name_kr)

    # 데이터셋 메타 완성도
    meta_checks = {
        "dataset_name_kr": bool(dataset.dataset_name_kr),
        "description": bool(dataset.description),
        "classification_id": dataset.classification_id is not None,
        "grade_id": dataset.grade_id is not None,
        "owner_department": bool(dataset.owner_department),
    }
    meta_total = len(meta_checks)
    meta_complete = sum(1 for v in meta_checks.values() if v)

    total = col_total + meta_total
    complete = col_complete + meta_complete
    error_count = total - complete
    score = Decimal(str(round((complete / total) * 100, 2)))

    missing_kr_columns = [c.column_name for c in columns if not c.column_name_kr]
    missing_meta = [k for k, v in meta_checks.items() if not v]

    start = datetime.now()
    result = QualityCheckResult(
        rule_id=None,
        dataset_name=dataset.dataset_name,
        check_type="COMPLETENESS",
        total_count=total,
        error_count=error_count,
        score=score,
        executed_at=start,
        execution_time_ms=0,
        details={
            "check": "catalog_metadata_completeness",
            "column_complete": col_complete,
            "column_total": col_total,
            "missing_kr_columns": missing_kr_columns[:20],
            "missing_meta_fields": missing_meta,
        },
        catalog_dataset_id=dataset.id,
    )
    db.add(result)
    db.flush()
    logger.info(
        "catalog COMPLETENESS: dataset=%s score=%s (meta=%d/%d col_kr=%d/%d)",
        dataset.dataset_name, score, meta_complete, meta_total, col_complete, col_total,
    )
    return result


# ── 유통 데이터셋 품질 ────────────────────────────────────────────────
def check_distribution_dataset(
    db: Session, distribution_dataset_id: UUID | str
) -> Optional[QualityCheckResult]:
    """유통 데이터셋 품질 검증.

    검증 항목:
    - 원본 CatalogDataset 연결 및 활성 여부
    - 유통 메타(분류, 등급, 다운로드 포맷, 설명) 누락 여부
    - 유통 등급과 카탈로그 등급 일관성
    - 원본 카탈로그 완성도와의 격차
    """
    dist = db.execute(
        select(DistributionDataset).where(
            DistributionDataset.id == str(distribution_dataset_id),
            DistributionDataset.is_deleted == False,  # noqa: E712
        )
    ).scalar_one_or_none()
    if not dist:
        return None

    catalog = db.execute(
        select(CatalogDataset).where(CatalogDataset.id == dist.dataset_id)
    ).scalar_one_or_none()

    checks: dict[str, bool] = {
        "has_source_catalog": catalog is not None,
        "source_catalog_active": bool(catalog and catalog.status == "ACTIVE" and not catalog.is_deleted),
        "has_classification": dist.classification_id is not None,
        "has_grade": dist.grade_id is not None,
        "has_allowed_formats": bool(dist.allowed_formats),
        "has_description": bool(dist.description),
    }

    # 분류 / 등급 참조 무결성
    if dist.classification_id is not None:
        cls = db.execute(
            select(DataClassification).where(DataClassification.id == dist.classification_id)
        ).scalar_one_or_none()
        checks["classification_resolvable"] = cls is not None
    else:
        checks["classification_resolvable"] = False

    if dist.grade_id is not None:
        gr = db.execute(
            select(DataGrade).where(DataGrade.id == dist.grade_id)
        ).scalar_one_or_none()
        checks["grade_resolvable"] = gr is not None
    else:
        checks["grade_resolvable"] = False

    # 등급 일관성
    if catalog and catalog.grade_id and dist.grade_id:
        checks["grade_consistent_with_catalog"] = catalog.grade_id == dist.grade_id
    else:
        checks["grade_consistent_with_catalog"] = True  # 원본 등급이 없으면 불가판정 제외

    total = len(checks)
    passed = sum(1 for v in checks.values() if v)
    error_count = total - passed
    score = Decimal(str(round((passed / total) * 100, 2)))

    failed_checks = [k for k, v in checks.items() if not v]
    start = datetime.now()
    result = QualityCheckResult(
        rule_id=None,
        dataset_name=dist.distribution_name or (catalog.dataset_name if catalog else None),
        check_type="DISTRIBUTION_VALIDITY",
        total_count=total,
        error_count=error_count,
        score=score,
        executed_at=start,
        execution_time_ms=0,
        details={
            "check": "distribution_quality",
            "failed_checks": failed_checks,
            "passed": passed,
            "total": total,
            "source_catalog_dataset_id": str(catalog.id) if catalog else None,
        },
        catalog_dataset_id=catalog.id if catalog else None,
        distribution_dataset_id=dist.id,
    )
    db.add(result)
    db.flush()
    logger.info(
        "distribution VALIDITY: dist=%s score=%s (passed=%d/%d)",
        dist.distribution_name, score, passed, total,
    )
    return result


# ── 활성 규칙 실행 ────────────────────────────────────────────────────
def execute_active_rules_for_dataset(
    db: Session,
    dataset_name: str,
    catalog_dataset_id: Optional[UUID] = None,
) -> list[QualityCheckResult]:
    """활성화된 QualityRule 들을 해당 데이터셋에 적용.

    현재 구현: COMPLETENESS 규칙만 데이터셋 메타 기반으로 간이 평가.
    rule_expression 을 실제 SQL 로 실행하는 고급 엔진은 후속 과제.
    """
    rules = db.execute(
        select(QualityRule).where(QualityRule.is_active == True)  # noqa: E712
    ).scalars().all()

    results: list[QualityCheckResult] = []
    dataset = None
    if catalog_dataset_id:
        dataset = db.execute(
            select(CatalogDataset).where(CatalogDataset.id == str(catalog_dataset_id))
        ).scalar_one_or_none()

    for rule in rules:
        start = datetime.now()
        total_count = 1
        error_count = 0
        score = Decimal("100.00")
        details: dict = {"rule_name": rule.rule_name, "severity": rule.severity}

        if rule.rule_type == "COMPLETENESS" and dataset is not None:
            meta_checks = [
                dataset.dataset_name_kr,
                dataset.description,
                dataset.classification_id,
                dataset.grade_id,
                dataset.source_system,
            ]
            total_count = len(meta_checks)
            error_count = sum(1 for c in meta_checks if not c)
            score = Decimal(str(round(((total_count - error_count) / total_count) * 100, 2)))
            details["missing_meta"] = error_count

        elapsed = int((datetime.now() - start).total_seconds() * 1000)
        result = QualityCheckResult(
            rule_id=rule.id,
            dataset_name=dataset_name,
            check_type=rule.rule_type,
            total_count=total_count,
            error_count=error_count,
            score=score,
            executed_at=start,
            execution_time_ms=elapsed,
            details=details,
            catalog_dataset_id=catalog_dataset_id,
        )
        db.add(result)
        db.flush()
        results.append(result)
    return results


def get_score_severity(score: float | Decimal) -> str:
    s = float(score)
    if s >= SCORE_GOOD:
        return "GOOD"
    if s >= SCORE_WARN:
        return "WARN"
    return "CRITICAL"
