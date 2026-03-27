"""분류체계/OpenMetadata 동기화 태스크"""
from app.tasks import celery_app


@celery_app.task(name="sync.classification")
def sync_classification():
    """데이터관리포털 분류체계 동기화

    - 데이터관리포털 API에서 분류 데이터 조회
    - 허브의 data_classification과 비교
    - 차이점을 classification_sync_log에 기록
    """
    # TODO: 외부 API 연동 및 동기화 로직
    return {"status": "completed"}


@celery_app.task(name="sync.openmetadata_glossary")
def sync_glossary_to_om():
    """표준사전 → OpenMetadata Glossary 동기화

    - std_word, std_term, std_domain 변경분 → OM Glossary push
    """
    # TODO: OpenMetadata SDK 사용하여 Glossary 동기화
    return {"status": "completed"}


@celery_app.task(name="sync.openmetadata_classification")
def sync_classification_to_om():
    """분류체계 → OpenMetadata Classification 동기화

    - data_classification → OM Classification/Tags push
    """
    # TODO: OpenMetadata SDK 사용하여 Classification 동기화
    return {"status": "completed"}
