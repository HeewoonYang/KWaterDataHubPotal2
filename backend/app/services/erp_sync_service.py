"""ERP 인사·조직도 동기화 서비스"""
import re
import uuid
from datetime import datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.org_sync import OrgSyncDetail, OrgSyncLog
from app.models.user import UserAccount, UserRole, UserRoleMap


# ── ERP API 클라이언트 ──

async def fetch_erp_employees() -> list[dict]:
    """ERP HR API에서 직원 목록 가져오기"""
    if not settings.ERP_API_URL or not settings.ERP_API_KEY:
        # 개발용 Mock 데이터
        return _mock_erp_data()

    headers = {"Authorization": f"Bearer {settings.ERP_API_KEY}", "Accept": "application/json"}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{settings.ERP_API_URL}/employees", headers=headers)
        resp.raise_for_status()
        return resp.json().get("data", [])


def _mock_erp_data() -> list[dict]:
    """ERP API 미연동 시 Mock 데이터"""
    return [
        {"employee_no": "10001", "name": "김수자원", "email": "kim@kwater.or.kr", "department_code": "DEPT001", "department_name": "수자원관리부", "position": "부장", "status": "ACTIVE"},
        {"employee_no": "10002", "name": "이데이터", "email": "lee@kwater.or.kr", "department_code": "DEPT002", "department_name": "정보시스템부", "position": "차장", "status": "ACTIVE"},
        {"employee_no": "10003", "name": "박인프라", "email": "park@kwater.or.kr", "department_code": "DEPT003", "department_name": "인프라관리부", "position": "과장", "status": "ACTIVE"},
        {"employee_no": "10004", "name": "최분석", "email": "choi@kwater.or.kr", "department_code": "DEPT002", "department_name": "정보시스템부", "position": "대리", "status": "ACTIVE"},
        {"employee_no": "10005", "name": "정퇴직", "email": "jung@kwater.or.kr", "department_code": "DEPT001", "department_name": "수자원관리부", "position": "과장", "status": "RESIGNED"},
    ]


# ── 데이터 품질 검증 ──

def validate_employee(emp: dict) -> list[str]:
    """직원 데이터 품질 검증 → 오류 목록 반환"""
    errors = []
    if not emp.get("employee_no"):
        errors.append("사번 누락")
    if not emp.get("name"):
        errors.append("이름 누락")
    if emp.get("email") and not re.match(r"^[^@]+@[^@]+\.[^@]+$", emp["email"]):
        errors.append(f"이메일 형식 오류: {emp['email']}")
    if emp.get("employee_no") and not re.match(r"^\d+$", str(emp["employee_no"])):
        errors.append(f"사번 형식 오류: {emp['employee_no']}")
    return errors


# ── 동기화 실행 ──

async def run_sync(
    db: AsyncSession,
    trigger_by: uuid.UUID | None = None,
    sync_type: str = "MANUAL",
    scope: str = "ALL",
    conflict_policy: str | None = None,
    is_dry_run: bool = False,
) -> OrgSyncLog:
    """ERP 동기화 실행 — 가져오기 → 비교 → 반영 → 이력 저장"""
    policy = conflict_policy or settings.ERP_CONFLICT_POLICY

    log = OrgSyncLog(
        id=uuid.uuid4(), sync_type=sync_type, trigger_by=trigger_by,
        scope=scope, conflict_policy=policy, is_dry_run=is_dry_run,
        started_at=datetime.now(), status="RUNNING",
    )
    db.add(log)
    await db.flush()

    try:
        # 1. ERP 데이터 가져오기
        erp_employees = await fetch_erp_employees()
        log.total_records = len(erp_employees)

        # 2. 현재 DB 사용자 조회 (내부 사용자, employee_no 기준)
        db_users = (await db.execute(
            select(UserAccount).where(
                UserAccount.user_type == "INTERNAL",
                UserAccount.is_deleted == False,
            )
        )).scalars().all()
        db_map = {u.employee_no: u for u in db_users if u.employee_no}

        # ERP 사번 Set
        erp_emp_nos = set()
        added = updated = deactivated = errors = skipped = 0

        for emp in erp_employees:
            # 품질 검증
            validation_errors = validate_employee(emp)
            if validation_errors:
                errors += 1
                db.add(OrgSyncDetail(
                    id=uuid.uuid4(), sync_log_id=log.id, action="ERROR",
                    employee_no=emp.get("employee_no", ""), user_name=emp.get("name", ""),
                    error_message="; ".join(validation_errors),
                ))
                continue

            emp_no = str(emp["employee_no"])
            erp_emp_nos.add(emp_no)

            if emp.get("status") == "RESIGNED":
                # 퇴직자 처리
                if emp_no in db_map:
                    existing = db_map[emp_no]
                    if existing.status != "WITHDRAWN":
                        if not is_dry_run:
                            existing.status = "WITHDRAWN"
                            existing.updated_at = datetime.now()
                        deactivated += 1
                        db.add(OrgSyncDetail(
                            id=uuid.uuid4(), sync_log_id=log.id, action="DEACTIVATE",
                            employee_no=emp_no, user_name=emp.get("name", ""),
                            field_name="status", old_value=existing.status, new_value="WITHDRAWN",
                        ))
                continue

            if emp_no in db_map:
                # 기존 사용자 — 변경 비교
                existing = db_map[emp_no]
                changes = _compare_user(existing, emp, policy)
                if changes:
                    updated += 1
                    for field, old_val, new_val in changes:
                        if not is_dry_run:
                            setattr(existing, field, new_val)
                        db.add(OrgSyncDetail(
                            id=uuid.uuid4(), sync_log_id=log.id, action="UPDATE",
                            employee_no=emp_no, user_name=emp.get("name", ""),
                            field_name=field, old_value=str(old_val or ""), new_value=str(new_val or ""),
                        ))
                    if not is_dry_run:
                        existing.updated_at = datetime.now()
                else:
                    skipped += 1
            else:
                # 신규 사용자
                added += 1
                if not is_dry_run:
                    new_user = UserAccount(
                        id=uuid.uuid4(),
                        login_id=emp_no,
                        employee_no=emp_no,
                        name=emp.get("name", ""),
                        email=emp.get("email"),
                        department_code=emp.get("department_code"),
                        department_name=emp.get("department_name"),
                        position=emp.get("position"),
                        user_type="INTERNAL",
                        status="ACTIVE",
                        created_at=datetime.now(),
                    )
                    db.add(new_user)
                    await db.flush()

                    # 기본 역할 부여
                    role = (await db.execute(
                        select(UserRole).where(UserRole.role_code == settings.ERP_DEFAULT_ROLE)
                    )).scalar_one_or_none()
                    if role:
                        db.add(UserRoleMap(
                            id=uuid.uuid4(), user_id=new_user.id, role_id=role.id,
                            granted_at=datetime.now(), status="ACTIVE",
                        ))

                db.add(OrgSyncDetail(
                    id=uuid.uuid4(), sync_log_id=log.id, action="ADD",
                    employee_no=emp_no, user_name=emp.get("name", ""),
                    field_name="전체", new_value=f"신규 등록 ({emp.get('department_name', '')} {emp.get('position', '')})",
                ))

        # 3. ERP에 없는 사용자 비활성화 (선택적)
        # for emp_no, user in db_map.items():
        #     if emp_no not in erp_emp_nos and user.status == "ACTIVE":
        #         pass  # 정책에 따라 처리

        log.added = added
        log.updated = updated
        log.deactivated = deactivated
        log.errors = errors
        log.skipped = skipped
        log.finished_at = datetime.now()
        log.duration_ms = int((log.finished_at - log.started_at).total_seconds() * 1000)
        log.status = "SUCCESS" if errors == 0 else "PARTIAL"

    except Exception as e:
        log.status = "FAILED"
        log.error_message = str(e)[:1000]
        log.finished_at = datetime.now()
        if log.started_at:
            log.duration_ms = int((log.finished_at - log.started_at).total_seconds() * 1000)

    return log


def _compare_user(existing: UserAccount, erp: dict, policy: str) -> list[tuple[str, str, str]]:
    """기존 사용자와 ERP 데이터 비교 → 변경 목록 [(field, old, new)]"""
    changes = []
    field_map = {
        "name": "name",
        "email": "email",
        "department_code": "department_code",
        "department_name": "department_name",
        "position": "position",
    }
    for erp_field, db_field in field_map.items():
        erp_val = erp.get(erp_field)
        db_val = getattr(existing, db_field, None)
        if erp_val and erp_val != db_val:
            if policy == "ERP_FIRST":
                changes.append((db_field, db_val, erp_val))
            elif policy == "HUB_FIRST":
                pass  # 허브 우선이면 변경하지 않음
            else:
                changes.append((db_field, db_val, erp_val))  # MANUAL도 일단 기록
    return changes
