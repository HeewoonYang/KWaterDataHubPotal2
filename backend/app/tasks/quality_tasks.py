"""품질검증 배치 태스크"""
from app.tasks import celery_app


@celery_app.task(name="quality.execute_check")
def execute_quality_check(rule_id: int | None = None):
    """품질 검증 배치 실행

    - rule_id가 지정되면 해당 규칙만 실행
    - None이면 활성 규칙 전체 실행
    """
    # TODO: 동기 DB 세션으로 품질 규칙 조회 및 실행
    # 1. quality_rule 테이블에서 is_active=True 규칙 조회
    # 2. 각 규칙의 rule_expression을 대상 데이터에 적용
    # 3. 결과를 quality_check_result에 저장
    return {"status": "completed", "rule_id": rule_id}


@celery_app.task(name="quality.compliance_check")
def run_compliance_check():
    """표준 준수 검사 배치

    - 단어/용어/도메인/코드 사전 대비 준수율 계산
    - 결과를 std_compliance_result에 저장
    """
    # TODO: 동기 DB 세션으로 준수율 계산
    return {"status": "completed"}
