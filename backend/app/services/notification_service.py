"""알림 발송 서비스 (Celery 동기 컨텍스트용)"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import new_uuid
from app.models.catalog import CatalogDataset
from app.models.collection import CollectionJob
from app.models.portal import PortalNotification, PortalNotificationSubscription
from app.models.user import UserAccount, UserRole, UserRoleMap

logger = logging.getLogger(__name__)


def notify_data_registered(
    db: Session,
    dataset: CatalogDataset,
    job: CollectionJob,
) -> int:
    """데이터셋 카탈로그 등록 완료 알림 생성

    Returns:
        생성된 알림 건수
    """
    target_user_ids = _get_notification_targets(db, "DATA_CHANGE", dataset.owner_user_id)
    if not target_user_ids:
        return 0

    title = f"[수집완료] {dataset.dataset_name} 카탈로그 등록"
    message = f"총 {job.success_rows or 0:,}건 수집 완료, 카탈로그에 자동 등록되었습니다."
    link_url = f"/portal/catalog/{dataset.id}"

    count = 0
    for user_id in target_user_ids:
        db.add(PortalNotification(
            id=new_uuid(),
            user_id=user_id,
            notification_type="DATA_CHANGE",
            title=title,
            message=message,
            link_url=link_url,
            is_read=False,
            created_at=datetime.now(),
        ))
        count += 1

    db.flush()
    logger.info("카탈로그 등록 알림 %d건 생성: dataset=%s", count, dataset.dataset_name)
    return count


def notify_quality_result(
    db: Session,
    dataset_name: str,
    score: float,
    catalog_dataset_id: UUID | None = None,
) -> int:
    """품질 검증 결과 알림 생성"""
    target_user_ids = _get_notification_targets(db, "QUALITY")
    if not target_user_ids:
        return 0

    severity = "양호" if score >= 80 else "주의" if score >= 50 else "경고"
    title = f"[품질검증] {dataset_name} - {severity} ({score:.1f}점)"
    message = f"품질 점수: {score:.1f}점 ({severity})"
    link_url = f"/portal/catalog/{catalog_dataset_id}" if catalog_dataset_id else None

    count = 0
    for user_id in target_user_ids:
        db.add(PortalNotification(
            id=new_uuid(),
            user_id=user_id,
            notification_type="QUALITY",
            title=title,
            message=message,
            link_url=link_url,
            is_read=False,
            created_at=datetime.now(),
        ))
        count += 1

    db.flush()
    logger.info("품질 검증 알림 %d건 생성: dataset=%s, score=%.1f", count, dataset_name, score)
    return count


def _get_notification_targets(
    db: Session,
    notification_type: str,
    owner_user_id: UUID | None = None,
) -> list[UUID]:
    """알림 수신 대상 사용자 ID 조회

    ADMIN/MANAGER 역할 + 데이터 소유자 중
    해당 notification_type 구독이 활성화된 사용자
    """
    # ADMIN, MANAGER 역할의 사용자 조회
    admin_manager_ids = db.execute(
        select(UserRoleMap.user_id).join(
            UserRole, UserRoleMap.role_id == UserRole.id
        ).where(
            UserRole.role_code.in_(["ADMIN", "MANAGER"]),
            UserRoleMap.status == "ACTIVE",
        )
    ).scalars().all()

    candidate_ids = set(admin_manager_ids)
    if owner_user_id:
        candidate_ids.add(owner_user_id)

    if not candidate_ids:
        return []

    # 구독 비활성화된 사용자 제외
    disabled_ids = set(db.execute(
        select(PortalNotificationSubscription.user_id).where(
            PortalNotificationSubscription.notification_type == notification_type,
            PortalNotificationSubscription.is_enabled == False,
            PortalNotificationSubscription.user_id.in_(candidate_ids),
        )
    ).scalars().all())

    return [uid for uid in candidate_ids if uid not in disabled_ids]
