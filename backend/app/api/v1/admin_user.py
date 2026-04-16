"""관리자 - 사용자관리 API"""
import math
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.security import hash_password
from app.database import get_db
from app.models.user import (UserAccessRequest, UserAccount, UserDataAccessPolicy, UserRole, UserRoleMap, UserScreenPermission)
from app.models.system import SysConfig
from app.models.classification import DataGrade
from app.services import recovery_service
from app.schemas.admin import (
    AccessPolicyCreate, AccessPolicyResponse, AccessPolicyUpdate, AccessRequestResponse,
    CommonSettingsResponse, CommonSettingsUpdate,
    CustomCategoryCreate, CustomSettingCreate,
    SecurityRuleCreate, SecurityRuleUpdate,
    RoleCreate, RoleResponse, RoleUpdate, UserCreate, UserListResponse, UserUpdate,
    ScreenPermissionResponse, ScreenPermissionItem, ScreenPermissionBulkUpdate, ScreenCodeResponse,
)
from app.schemas.common import APIResponse, PageRequest, PageResponse

router = APIRouter()


@router.get("/users", response_model=PageResponse[UserListResponse])
async def list_users(
    page: int = 1, page_size: int = 20, search: str | None = None,
    user_type: str | None = None, status: str | None = None,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    query = (
        select(UserAccount, UserRole.role_code)
        .outerjoin(UserRoleMap, (UserRoleMap.user_id == UserAccount.id) & (UserRoleMap.status == "ACTIVE"))
        .outerjoin(UserRole, UserRoleMap.role_id == UserRole.id)
        .where(UserAccount.is_deleted == False)
    )
    if user_type:
        query = query.where(UserAccount.user_type == user_type)
    if status:
        query = query.where(UserAccount.status == status)
    if search:
        kw = f"%{search}%"
        query = query.where(or_(UserAccount.name.ilike(kw), UserAccount.login_id.ilike(kw), UserAccount.email.ilike(kw)))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (page - 1) * page_size
    rows = (await db.execute(query.order_by(UserAccount.created_at.desc()).offset(offset).limit(page_size))).all()

    items = [UserListResponse(
        id=r[0].id, login_id=r[0].login_id, name=r[0].name, email=r[0].email,
        user_type=r[0].user_type, employee_no=r[0].employee_no,
        department_name=r[0].department_name, position=r[0].position,
        status=r[0].status, last_login_at=r[0].last_login_at, role_code=r[1],
    ) for r in rows]

    return PageResponse(items=items, total=total, page=page, page_size=page_size,
                        total_pages=math.ceil(total / page_size) if page_size else 0)


@router.post("/users", response_model=APIResponse[UserListResponse])
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    # send_initial_sms=True 이면 임시 비밀번호는 서버에서 생성, 관리자에게 노출하지 않고 SMS로만 전달
    if body.send_initial_sms:
        if not body.phone:
            raise HTTPException(status_code=400, detail="초기 비밀번호 SMS 발송을 위해 휴대폰번호가 필요합니다")
        # 플레이스홀더 해시 - 실제 비밀번호는 recovery_service.send_initial_password 에서 재설정
        password_hash_value = hash_password("!PLACEHOLDER_WILL_BE_REPLACED!")
    else:
        if not body.password:
            raise HTTPException(status_code=400, detail="비밀번호를 입력하거나 초기 SMS 발송을 활성화하세요")
        password_hash_value = hash_password(body.password)

    department_name = body.department_name or body.org

    new_user = UserAccount(
        id=uuid.uuid4(), login_id=body.login_id, password_hash=password_hash_value,
        name=body.name, email=body.email, phone=body.phone,
        user_type=body.user_type, employee_no=body.employee_no,
        department_code=body.department_code, department_name=department_name,
        position=body.position, status="ACTIVE", created_at=datetime.now(),
        created_by=user.id,
        must_change_password=body.send_initial_sms,
    )
    db.add(new_user)

    role = (await db.execute(select(UserRole).where(UserRole.role_code == body.role_code))).scalar_one_or_none()
    if role:
        db.add(UserRoleMap(id=uuid.uuid4(), user_id=new_user.id, role_id=role.id, granted_by=user.id, granted_at=datetime.now(), status="ACTIVE"))

    await db.flush()

    response_message = "사용자가 등록되었습니다"
    if body.send_initial_sms:
        ok, msg = await recovery_service.send_initial_password(db, new_user.id, issued_by=user.id)
        if not ok:
            # 사용자는 생성되었지만 SMS 실패 - 관리자에게 알림
            response_message = f"사용자는 등록되었으나 SMS 발송에 실패했습니다: {msg}"
        else:
            response_message = "사용자가 등록되고 초기 비밀번호 SMS가 발송되었습니다"

    return APIResponse(data=UserListResponse(
        id=new_user.id, login_id=new_user.login_id, name=new_user.name, email=new_user.email,
        user_type=new_user.user_type, employee_no=new_user.employee_no,
        department_name=new_user.department_name, position=new_user.position,
        status=new_user.status, role_code=body.role_code,
    ), message=response_message)


@router.post("/users/{user_id}/send-initial-password", response_model=APIResponse)
async def send_initial_password(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """외부사용자에게 초기/재발급 비밀번호 SMS 발송.
    호출 시: 임시 비밀번호 재생성 → 해시 저장 → must_change_password=True → 기존 세션 무효화 → SMS 발송.
    평문 비밀번호는 SMS 페이로드 외 어디에도 기록되지 않는다."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="잘못된 사용자 ID 형식")
    ok, msg = await recovery_service.send_initial_password(db, uid, issued_by=user.id)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return APIResponse(message=msg)


@router.get("/users/{user_id}", response_model=APIResponse[UserListResponse])
async def get_user(user_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """사용자 상세 조회"""
    row = (await db.execute(
        select(UserAccount, UserRole.role_code)
        .outerjoin(UserRoleMap, (UserRoleMap.user_id == UserAccount.id) & (UserRoleMap.status == "ACTIVE"))
        .outerjoin(UserRole, UserRoleMap.role_id == UserRole.id)
        .where(UserAccount.id == uuid.UUID(user_id), UserAccount.is_deleted == False)
    )).first()
    if not row:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    u = row[0]
    return APIResponse(data=UserListResponse(
        id=u.id, login_id=u.login_id, name=u.name, email=u.email,
        user_type=u.user_type, employee_no=u.employee_no,
        department_name=u.department_name, position=u.position,
        status=u.status, last_login_at=u.last_login_at, role_code=row[1],
    ))


@router.put("/users/{user_id}", response_model=APIResponse[UserListResponse])
async def update_user(user_id: str, body: UserUpdate, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """사용자 정보 수정"""
    u = (await db.execute(select(UserAccount).where(UserAccount.id == uuid.UUID(user_id), UserAccount.is_deleted == False))).scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    if body.name is not None:
        u.name = body.name
    if body.email is not None:
        u.email = body.email
    if body.department_code is not None:
        u.department_code = body.department_code
    if body.department_name is not None:
        u.department_name = body.department_name
    if body.position is not None:
        u.position = body.position
    if body.status is not None:
        u.status = body.status
    if body.phone is not None:
        u.phone = body.phone
    u.updated_at = datetime.now()
    u.updated_by = user.id

    # 역할 변경
    if body.role_code:
        role = (await db.execute(select(UserRole).where(UserRole.role_code == body.role_code))).scalar_one_or_none()
        if role:
            existing = (await db.execute(
                select(UserRoleMap).where(UserRoleMap.user_id == u.id, UserRoleMap.status == "ACTIVE")
            )).scalar_one_or_none()
            if existing:
                existing.status = "INACTIVE"
            db.add(UserRoleMap(id=uuid.uuid4(), user_id=u.id, role_id=role.id, granted_by=user.id, granted_at=datetime.now(), status="ACTIVE"))

    await db.flush()
    return APIResponse(data=UserListResponse(
        id=u.id, login_id=u.login_id, name=u.name, email=u.email,
        user_type=u.user_type, employee_no=u.employee_no,
        department_name=u.department_name, position=u.position,
        status=u.status, role_code=body.role_code,
    ), message="사용자 정보가 수정되었습니다")


@router.delete("/users/{user_id}", response_model=APIResponse)
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """사용자 삭제 (소프트 삭제)"""
    u = (await db.execute(select(UserAccount).where(UserAccount.id == uuid.UUID(user_id), UserAccount.is_deleted == False))).scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    u.is_deleted = True
    u.status = "WITHDRAWN"
    u.updated_at = datetime.now()
    u.updated_by = user.id
    return APIResponse(message="사용자가 삭제되었습니다")


@router.post("/users/{user_id}/reset-password", response_model=APIResponse)
async def reset_password(user_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """비밀번호 초기화"""
    u = (await db.execute(select(UserAccount).where(UserAccount.id == uuid.UUID(user_id), UserAccount.is_deleted == False))).scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    u.password_hash = hash_password("kwater1234!")
    u.updated_at = datetime.now()
    return APIResponse(message="비밀번호가 초기화되었습니다 (kwater1234!)")


@router.get("/org-tree", response_model=APIResponse[list])
async def get_org_tree(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """조직 트리 조회 - 부서 계층 구조와 소속 사용자 수"""
    # 부서별 사용자 수 집계
    dept_counts = (await db.execute(
        select(UserAccount.department_code, func.count(UserAccount.id))
        .where(UserAccount.is_deleted == False, UserAccount.user_type == "INTERNAL")
        .group_by(UserAccount.department_code)
    )).all()
    count_map = {r[0]: r[1] for r in dept_counts if r[0]}

    # 전체 부서 목록 (중복 제거)
    depts = (await db.execute(
        select(UserAccount.department_code, UserAccount.department_name)
        .where(UserAccount.is_deleted == False, UserAccount.department_code.isnot(None))
        .distinct()
    )).all()

    tree = [
        {"code": r[0], "name": r[1] or r[0], "userCount": count_map.get(r[0], 0)}
        for r in depts
    ]
    return APIResponse(data=tree, message="OK")


@router.post("/org-sync", response_model=APIResponse)
async def run_org_sync(
    dry_run: bool = False,
    scope: str = "ALL",
    conflict_policy: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """ERP 인사정보 동기화 실행 (dry_run=True: 사전점검, False: 실제 동기화)"""
    from app.services import erp_sync_service
    log = await erp_sync_service.run_sync(
        db, trigger_by=user.id, sync_type="MANUAL",
        scope=scope, conflict_policy=conflict_policy, is_dry_run=dry_run,
    )
    await db.commit()
    return APIResponse(data={
        "sync_log_id": str(log.id), "dry_run": dry_run, "status": log.status,
        "total_records": log.total_records, "added": log.added, "updated": log.updated,
        "deactivated": log.deactivated, "errors": log.errors, "skipped": log.skipped,
        "duration_ms": log.duration_ms,
    }, message="동기화 사전 점검 완료" if dry_run else "동기화가 완료되었습니다")


@router.get("/org-sync/history", response_model=PageResponse)
async def get_org_sync_history(
    page: int = 1, page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """조직/사용자 동기화 이력 조회"""
    from app.models.org_sync import OrgSyncLog
    from app.models.user import UserAccount as UA2
    query = (
        select(OrgSyncLog, UA2.name.label("trigger_name"))
        .outerjoin(UA2, OrgSyncLog.trigger_by == UA2.id)
        .order_by(OrgSyncLog.started_at.desc())
    )
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (page - 1) * page_size
    rows = (await db.execute(query.offset(offset).limit(page_size))).all()
    items = [{
        "id": str(r[0].id), "sync_type": r[0].sync_type, "scope": r[0].scope,
        "is_dry_run": r[0].is_dry_run, "conflict_policy": r[0].conflict_policy,
        "started_at": r[0].started_at.strftime("%Y-%m-%d %H:%M:%S") if r[0].started_at else None,
        "finished_at": r[0].finished_at.strftime("%Y-%m-%d %H:%M:%S") if r[0].finished_at else None,
        "duration_ms": r[0].duration_ms, "total_records": r[0].total_records,
        "added": r[0].added, "updated": r[0].updated, "deactivated": r[0].deactivated,
        "errors": r[0].errors, "skipped": r[0].skipped,
        "status": r[0].status, "error_message": r[0].error_message,
        "trigger_name": r[1] or "시스템",
    } for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size,
                        total_pages=math.ceil(total / page_size) if page_size else 0)


@router.get("/org-sync/history/{sync_id}")
async def get_org_sync_detail(
    sync_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """동기화 상세 (변경건 목록)"""
    from app.models.org_sync import OrgSyncDetail
    rows = (await db.execute(
        select(OrgSyncDetail).where(OrgSyncDetail.sync_log_id == uuid.UUID(sync_id))
        .order_by(OrgSyncDetail.action)
    )).scalars().all()
    items = [{
        "id": str(r.id), "action": r.action, "employee_no": r.employee_no,
        "user_name": r.user_name, "field_name": r.field_name,
        "old_value": r.old_value, "new_value": r.new_value, "error_message": r.error_message,
    } for r in rows]
    return APIResponse(data=items)


@router.get("/roles", response_model=APIResponse[list[RoleResponse]])
async def list_roles(role_group: str | None = None, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    query = select(UserRole).order_by(UserRole.sort_order)
    if role_group:
        query = query.where(UserRole.role_group == role_group)
    rows = (await db.execute(query)).scalars().all()
    items = []
    for r in rows:
        cnt = (await db.execute(select(func.count()).where(UserRoleMap.role_id == r.id, UserRoleMap.status == "ACTIVE"))).scalar() or 0
        items.append(RoleResponse(
            id=r.id, role_code=r.role_code, role_name=r.role_name, role_group=r.role_group,
            description=r.description, is_system_role=r.is_system_role, can_access_admin=r.can_access_admin,
            sort_order=r.sort_order, user_count=cnt,
        ))
    return APIResponse(data=items)


@router.get("/access-policies", response_model=APIResponse[list[AccessPolicyResponse]])
async def list_access_policies(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(
        select(UserDataAccessPolicy, UserRole.role_name, DataGrade.grade_name)
        .outerjoin(UserRole, UserDataAccessPolicy.role_id == UserRole.id)
        .outerjoin(DataGrade, UserDataAccessPolicy.data_grade_id == DataGrade.id)
        .where(UserDataAccessPolicy.is_deleted == False)
    )).all()
    return APIResponse(data=[AccessPolicyResponse(
        id=r[0].id, policy_name=r[0].policy_name, role_name=r[1], grade_name=r[2],
        requires_approval=r[0].requires_approval, description=r[0].description,
    ) for r in rows])


# ── 역할 CRUD ──
@router.post("/roles", response_model=APIResponse[RoleResponse])
async def create_role(body: RoleCreate, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    role = UserRole(id=uuid.uuid4(), role_code=body.role_code, role_name=body.role_name,
                    role_group=body.role_group, description=body.description,
                    can_access_admin=body.can_access_admin, is_system_role=False)
    db.add(role)
    await db.flush()
    return APIResponse(data=RoleResponse(id=role.id, role_code=role.role_code, role_name=role.role_name,
                                          role_group=role.role_group, description=role.description,
                                          can_access_admin=role.can_access_admin,
                                          is_system_role=False, user_count=0), message="역할이 등록되었습니다")


@router.put("/roles/{role_id}", response_model=APIResponse[RoleResponse])
async def update_role(role_id: str, body: RoleUpdate, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    role = (await db.execute(select(UserRole).where(UserRole.id == uuid.UUID(role_id)))).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="역할을 찾을 수 없습니다")
    if body.role_name is not None:
        role.role_name = body.role_name
    if body.role_group is not None:
        role.role_group = body.role_group
    if body.description is not None:
        role.description = body.description
    if body.can_access_admin is not None:
        role.can_access_admin = body.can_access_admin
    await db.flush()
    cnt = (await db.execute(select(func.count()).where(UserRoleMap.role_id == role.id, UserRoleMap.status == "ACTIVE"))).scalar() or 0
    return APIResponse(data=RoleResponse(id=role.id, role_code=role.role_code, role_name=role.role_name,
                                          role_group=role.role_group, description=role.description,
                                          can_access_admin=role.can_access_admin,
                                          is_system_role=role.is_system_role, sort_order=role.sort_order,
                                          user_count=cnt), message="역할이 수정되었습니다")


@router.delete("/roles/{role_id}", response_model=APIResponse)
async def delete_role(role_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    role = (await db.execute(select(UserRole).where(UserRole.id == uuid.UUID(role_id)))).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="역할을 찾을 수 없습니다")
    if role.is_system_role:
        raise HTTPException(status_code=400, detail="시스템 역할은 삭제할 수 없습니다")
    await db.delete(role)
    return APIResponse(message="역할이 삭제되었습니다")


# ── 화면별 권한 관리 ──
SCREEN_CODES_MASTER = [
    # 시스템관리
    {"screen_code": "SYS_CLOUD", "screen_name": "클라우드 구성", "screen_group": "시스템관리"},
    {"screen_code": "SYS_DR", "screen_name": "DR/백업 관리", "screen_group": "시스템관리"},
    {"screen_code": "SYS_PKG", "screen_name": "패키지 검증", "screen_group": "시스템관리"},
    {"screen_code": "SYS_INTF", "screen_name": "표준 인터페이스", "screen_group": "시스템관리"},
    {"screen_code": "SYS_INTG", "screen_name": "이기종 통합", "screen_group": "시스템관리"},
    {"screen_code": "SYS_DMZ", "screen_name": "DMZ 연계", "screen_group": "시스템관리"},
    # 사용자관리
    {"screen_code": "USR_LIST", "screen_name": "조직/사용자 관리", "screen_group": "사용자관리"},
    {"screen_code": "USR_EXT", "screen_name": "외부 사용자", "screen_group": "사용자관리"},
    {"screen_code": "USR_SYNC", "screen_name": "조직사용자 동기화", "screen_group": "사용자관리"},
    {"screen_code": "USR_COMMON", "screen_name": "사용자 공통", "screen_group": "사용자관리"},
    {"screen_code": "USR_ROLES", "screen_name": "역할 관리", "screen_group": "사용자관리"},
    {"screen_code": "USR_ACCESS", "screen_name": "데이터 접근제어", "screen_group": "사용자관리"},
    # 데이터표준
    {"screen_code": "STD_COMPLY", "screen_name": "표준 준수 현황", "screen_group": "데이터표준"},
    {"screen_code": "STD_CLASS", "screen_name": "분류/등급 관리", "screen_group": "데이터표준"},
    {"screen_code": "STD_WORD", "screen_name": "단어사전", "screen_group": "데이터표준"},
    {"screen_code": "STD_DOMAIN", "screen_name": "도메인사전", "screen_group": "데이터표준"},
    {"screen_code": "STD_TERM", "screen_name": "용어사전", "screen_group": "데이터표준"},
    {"screen_code": "STD_CODE", "screen_name": "코드사전", "screen_group": "데이터표준"},
    {"screen_code": "STD_GRADE", "screen_name": "등급 관리", "screen_group": "데이터표준"},
    {"screen_code": "STD_QUALITY", "screen_name": "품질 점검", "screen_group": "데이터표준"},
    {"screen_code": "STD_QLINK", "screen_name": "품질 연계", "screen_group": "데이터표준"},
    # 데이터수집
    {"screen_code": "COL_UI", "screen_name": "수집 현황", "screen_group": "데이터수집"},
    {"screen_code": "COL_STRAT", "screen_name": "수집 전략", "screen_group": "데이터수집"},
    {"screen_code": "COL_DB", "screen_name": "DB 연결", "screen_group": "데이터수집"},
    {"screen_code": "COL_EXT", "screen_name": "외부기관 연계", "screen_group": "데이터수집"},
    {"screen_code": "COL_LIGHT", "screen_name": "경량 수집", "screen_group": "데이터수집"},
    {"screen_code": "COL_MIG", "screen_name": "마이그레이션", "screen_group": "데이터수집"},
    {"screen_code": "COL_SPATIAL", "screen_name": "공간데이터 수집", "screen_group": "데이터수집"},
    {"screen_code": "COL_DATASET", "screen_name": "데이터셋 설정", "screen_group": "데이터수집"},
    {"screen_code": "COL_DASH", "screen_name": "수집 대시보드", "screen_group": "데이터수집"},
    {"screen_code": "COL_PROFILE", "screen_name": "데이터 프로파일링", "screen_group": "데이터수집"},
    {"screen_code": "COL_GATE", "screen_name": "품질 게이트", "screen_group": "데이터수집"},
    # 데이터정제
    {"screen_code": "CLS_UI", "screen_name": "정제 현황", "screen_group": "데이터정제"},
    {"screen_code": "CLS_TRANSFORM", "screen_name": "변환 관리", "screen_group": "데이터정제"},
    {"screen_code": "CLS_ANON", "screen_name": "비식별화", "screen_group": "데이터정제"},
    {"screen_code": "CLS_TECH", "screen_name": "기술 검토", "screen_group": "데이터정제"},
    # 데이터저장
    {"screen_code": "STO_MANAGE", "screen_name": "저장소 관리", "screen_group": "데이터저장"},
    {"screen_code": "STO_HIGHSPEED", "screen_name": "고속 DB", "screen_group": "데이터저장"},
    {"screen_code": "STO_UNSTRUCT", "screen_name": "비정형 저장소", "screen_group": "데이터저장"},
    # 데이터유통
    {"screen_code": "DST_UI", "screen_name": "유통 현황", "screen_group": "데이터유통"},
    {"screen_code": "DST_CONFIG", "screen_name": "유통 설정", "screen_group": "데이터유통"},
    {"screen_code": "DST_STD", "screen_name": "유통 표준", "screen_group": "데이터유통"},
    {"screen_code": "DST_FORMAT", "screen_name": "유통 포맷", "screen_group": "데이터유통"},
    {"screen_code": "DST_STATS", "screen_name": "유통 통계", "screen_group": "데이터유통"},
    {"screen_code": "DST_API", "screen_name": "표준 API", "screen_group": "데이터유통"},
    {"screen_code": "DST_FUSION", "screen_name": "융합 모델", "screen_group": "데이터유통"},
    {"screen_code": "DST_MCP", "screen_name": "MCP 연계", "screen_group": "데이터유통"},
    {"screen_code": "DST_USAGE", "screen_name": "사용 현황", "screen_group": "데이터유통"},
    # 운영관리
    {"screen_code": "OPS_STATS", "screen_name": "허브 통계", "screen_group": "운영관리"},
    {"screen_code": "OPS_OPTIMIZE", "screen_name": "최적화", "screen_group": "운영관리"},
    {"screen_code": "OPS_AI", "screen_name": "AI 모니터", "screen_group": "운영관리"},
    {"screen_code": "OPS_APM", "screen_name": "APM 대시보드", "screen_group": "운영관리"},
    {"screen_code": "OPS_INTG_MON", "screen_name": "연계 모니터링", "screen_group": "운영관리"},
    {"screen_code": "OPS_SEC", "screen_name": "보안 모니터링", "screen_group": "운영관리"},
    {"screen_code": "OPS_EVENT", "screen_name": "데이터 이벤트", "screen_group": "운영관리"},
]


@router.get("/screen-codes", response_model=APIResponse[list[ScreenCodeResponse]])
async def list_screen_codes(user: CurrentUser = Depends(get_current_user)):
    """전체 화면코드 마스터 목록"""
    return APIResponse(data=[ScreenCodeResponse(**s) for s in SCREEN_CODES_MASTER])


@router.get("/roles/{role_id}/screen-permissions", response_model=APIResponse[list[ScreenPermissionResponse]])
async def get_role_screen_permissions(role_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """역할의 화면별 권한 조회"""
    rows = (await db.execute(
        select(UserScreenPermission)
        .where(UserScreenPermission.role_id == uuid.UUID(role_id))
        .order_by(UserScreenPermission.screen_group, UserScreenPermission.screen_code)
    )).scalars().all()
    return APIResponse(data=[ScreenPermissionResponse(
        id=r.id, role_id=r.role_id, screen_code=r.screen_code, screen_name=r.screen_name,
        screen_group=r.screen_group, can_create=r.can_create, can_update=r.can_update, can_delete=r.can_delete,
    ) for r in rows])


@router.put("/roles/{role_id}/screen-permissions", response_model=APIResponse)
async def update_role_screen_permissions(
    role_id: str, body: ScreenPermissionBulkUpdate,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """역할의 화면별 권한 일괄 저장 (upsert)"""
    rid = uuid.UUID(role_id)
    role = (await db.execute(select(UserRole).where(UserRole.id == rid))).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="역할을 찾을 수 없습니다")

    for item in body.permissions:
        existing = (await db.execute(
            select(UserScreenPermission)
            .where(UserScreenPermission.role_id == rid, UserScreenPermission.screen_code == item.screen_code)
        )).scalar_one_or_none()
        if existing:
            existing.can_create = item.can_create
            existing.can_update = item.can_update
            existing.can_delete = item.can_delete
            existing.screen_name = item.screen_name or existing.screen_name
            existing.screen_group = item.screen_group or existing.screen_group
            existing.updated_by = user.id
            existing.updated_at = datetime.now()
        else:
            db.add(UserScreenPermission(
                id=uuid.uuid4(), role_id=rid, screen_code=item.screen_code,
                screen_name=item.screen_name, screen_group=item.screen_group,
                can_create=item.can_create, can_update=item.can_update, can_delete=item.can_delete,
                created_by=user.id,
            ))
    await db.flush()
    return APIResponse(message="화면별 권한이 저장되었습니다")


# ── 접근정책 CRUD ──
@router.post("/access-policies", response_model=APIResponse[AccessPolicyResponse])
async def create_access_policy(body: AccessPolicyCreate, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    policy = UserDataAccessPolicy(
        id=uuid.uuid4(), policy_name=body.policy_name, role_id=body.role_id,
        data_grade_id=body.data_grade_id, requires_approval=body.requires_approval,
        description=body.description, created_by=user.id,
    )
    db.add(policy)
    await db.flush()
    return APIResponse(data=AccessPolicyResponse(id=policy.id, policy_name=policy.policy_name,
                                                   requires_approval=policy.requires_approval,
                                                   description=policy.description), message="접근정책이 등록되었습니다")


@router.put("/access-policies/{policy_id}", response_model=APIResponse)
async def update_access_policy(policy_id: str, body: AccessPolicyUpdate, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    policy = (await db.execute(select(UserDataAccessPolicy).where(UserDataAccessPolicy.id == uuid.UUID(policy_id)))).scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="접근정책을 찾을 수 없습니다")
    if body.policy_name is not None:
        policy.policy_name = body.policy_name
    if body.requires_approval is not None:
        policy.requires_approval = body.requires_approval
    if body.description is not None:
        policy.description = body.description
    policy.updated_by = user.id
    policy.updated_at = datetime.now()
    return APIResponse(message="접근정책이 수정되었습니다")


@router.delete("/access-policies/{policy_id}", response_model=APIResponse)
async def delete_access_policy(policy_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    policy = (await db.execute(select(UserDataAccessPolicy).where(UserDataAccessPolicy.id == uuid.UUID(policy_id)))).scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="접근정책을 찾을 수 없습니다")
    policy.is_deleted = True
    return APIResponse(message="접근정책이 삭제되었습니다")


# ── 접근 요청 관리 ──
@router.get("/access-requests", response_model=PageResponse)
async def list_access_requests(
    page: int = 1, page_size: int = 20, status: str | None = None,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    query = (
        select(UserAccessRequest, UserAccount.name.label("requester_name"))
        .outerjoin(UserAccount, UserAccessRequest.requester_id == UserAccount.id)
        .where(UserAccessRequest.is_deleted == False)
    )
    if status:
        query = query.where(UserAccessRequest.status == status)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (page - 1) * page_size
    rows = (await db.execute(query.order_by(UserAccessRequest.created_at.desc()).offset(offset).limit(page_size))).all()
    items = [AccessRequestResponse(
        id=r[0].id, requester_name=r[1], request_type=r[0].target_resource_type,
        requested_grade=r[0].data_grade_code,
        reason=r[0].reason, status=r[0].status, created_at=r[0].created_at, reviewed_at=r[0].reviewed_at,
    ) for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size,
                        total_pages=math.ceil(total / page_size) if page_size else 0)


@router.put("/access-requests/{request_id}/approve", response_model=APIResponse)
async def approve_access_request(request_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    req = (await db.execute(select(UserAccessRequest).where(UserAccessRequest.id == uuid.UUID(request_id)))).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="접근 요청을 찾을 수 없습니다")
    req.status = "APPROVED"
    req.reviewer_id = user.id
    req.reviewed_at = datetime.now()
    return APIResponse(message="접근 요청이 승인되었습니다")


@router.put("/access-requests/{request_id}/reject", response_model=APIResponse)
async def reject_access_request(request_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    req = (await db.execute(select(UserAccessRequest).where(UserAccessRequest.id == uuid.UUID(request_id)))).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="접근 요청을 찾을 수 없습니다")
    req.status = "REJECTED"
    req.reviewer_id = user.id
    req.reviewed_at = datetime.now()
    return APIResponse(message="접근 요청이 반려되었습니다")


# ── 사용자 공통 설정 ──
USER_COMMON_DEFAULTS: dict[str, tuple[str, str, str]] = {
    "user.password.min_length": ("8", "NUMBER", "최소 비밀번호 길이"),
    "user.password.complexity": ("UPPER_LOWER_NUMBER_SPECIAL", "STRING", "비밀번호 복잡도"),
    "user.password.change_cycle_days": ("90", "NUMBER", "비밀번호 변경 주기(일)"),
    "user.password.reuse_limit": ("5", "NUMBER", "비밀번호 재사용 제한 횟수"),
    "user.session.timeout_minutes": ("30", "NUMBER", "세션 타임아웃(분)"),
    "user.session.max_devices": ("3", "NUMBER", "최대 동시 접속 디바이스 수"),
    "user.session.auto_logout": ("true", "BOOLEAN", "자동 로그아웃 활성화"),
    "user.security.login_fail_lock_count": ("5", "NUMBER", "로그인 실패 잠금 횟수"),
    "user.security.login_fail_lock_minutes": ("30", "NUMBER", "로그인 실패 잠금 시간(분)"),
    "user.security.ip_access_control": ("true", "BOOLEAN", "IP 접근 제어 활성화"),
    "user.security.two_factor_auth": ("OPTIONAL", "STRING", "2단계 인증 (REQUIRED/OPTIONAL/DISABLED)"),
    "user.notification.signup_approval": ("EMAIL_PORTAL", "STRING", "가입 승인 알림 방법"),
    "user.notification.password_expiry_days": ("7", "NUMBER", "비밀번호 만료 사전 알림(일)"),
    "user.notification.account_expiry_days": ("14", "NUMBER", "계정 만료 사전 알림(일)"),
}

SETTING_GROUP_PREFIXES = {
    "password_policy": "user.password.",
    "session_management": "user.session.",
    "security_settings": "user.security.",
    "notification_settings": "user.notification.",
}


@router.get("/common-settings", response_model=APIResponse[CommonSettingsResponse])
async def get_common_settings(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """사용자 공통 설정 조회 (없으면 기본값 자동 생성)"""
    rows = (await db.execute(
        select(SysConfig).where(SysConfig.category == "USER_COMMON", SysConfig.is_deleted == False)
    )).scalars().all()

    if not rows:
        for key, (val, typ, desc) in USER_COMMON_DEFAULTS.items():
            db.add(SysConfig(id=uuid.uuid4(), config_key=key, config_value=val,
                             config_type=typ, category="USER_COMMON", description=desc,
                             is_encrypted=False, created_at=datetime.now()))
        await db.flush()
        rows = (await db.execute(
            select(SysConfig).where(SysConfig.category == "USER_COMMON", SysConfig.is_deleted == False)
        )).scalars().all()

    flat = {r.config_key: r.config_value or "" for r in rows}

    grouped: dict = {}
    for group, prefix in SETTING_GROUP_PREFIXES.items():
        grouped[group] = {k: v for k, v in flat.items() if k.startswith(prefix)}

    # 보안 규칙 조회
    rule_rows = (await db.execute(
        select(SysConfig).where(SysConfig.category == "SECURITY_RULE", SysConfig.is_deleted == False)
    )).scalars().all()
    import json as _json
    security_rules = []
    for r in rule_rows:
        try:
            data = _json.loads(r.config_value or "{}")
        except Exception:
            data = {}
        security_rules.append({"id": str(r.id), **data, "created_at": str(r.created_at) if r.created_at else None})

    # 커스텀 카테고리 조회
    custom_rows = (await db.execute(
        select(SysConfig).where(SysConfig.category.like("USER_CUSTOM_%"), SysConfig.is_deleted == False)
    )).scalars().all()
    cat_map: dict[str, dict] = {}
    for r in custom_rows:
        cat = r.category
        if cat not in cat_map:
            cat_key = cat.replace("USER_CUSTOM_", "")
            cat_map[cat] = {"category_key": cat_key, "category_name": cat_key, "items": []}
        if r.config_key.startswith("_meta."):
            if r.config_key == "_meta.category_name":
                cat_map[cat]["category_name"] = r.config_value or cat_map[cat]["category_key"]
        else:
            cat_map[cat]["items"].append({
                "id": str(r.id), "key": r.config_key, "name": r.description or r.config_key,
                "value": r.config_value or "", "type": r.config_type or "STRING",
            })

    grouped["security_rules"] = security_rules
    grouped["custom_categories"] = list(cat_map.values())

    return APIResponse(data=CommonSettingsResponse(**grouped))


@router.put("/common-settings", response_model=APIResponse)
async def update_common_settings(
    body: CommonSettingsUpdate, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """사용자 공통 설정 일괄 수정"""
    for key in body.settings:
        if key not in USER_COMMON_DEFAULTS:
            raise HTTPException(status_code=400, detail=f"허용되지 않는 설정 키: {key}")

    for key, value in body.settings.items():
        row = (await db.execute(
            select(SysConfig).where(SysConfig.config_key == key, SysConfig.category == "USER_COMMON")
        )).scalar_one_or_none()
        if row:
            row.config_value = value
            row.updated_at = datetime.now()
            row.updated_by = user.id
        else:
            default_type = USER_COMMON_DEFAULTS[key][1]
            default_desc = USER_COMMON_DEFAULTS[key][2]
            db.add(SysConfig(id=uuid.uuid4(), config_key=key, config_value=value,
                             config_type=default_type, category="USER_COMMON",
                             description=default_desc, is_encrypted=False, created_at=datetime.now()))

    await db.flush()
    return APIResponse(message="사용자 공통 설정이 저장되었습니다")


# ── 보안 규칙 CRUD ──
SECURITY_RULE_TYPES = ["IP_WHITELIST", "ACCESS_TIME", "PASSWORD_PATTERN", "SESSION_LIMIT"]


@router.post("/security-rules", response_model=APIResponse)
async def create_security_rule(
    body: SecurityRuleCreate, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """보안 규칙 추가"""
    import json as _json
    if body.rule_type not in SECURITY_RULE_TYPES:
        raise HTTPException(status_code=400, detail=f"허용되지 않는 규칙 유형: {body.rule_type}")
    rule_data = _json.dumps({
        "rule_type": body.rule_type, "rule_name": body.rule_name,
        "value": body.value, "is_active": True, "description": body.description or "",
    }, ensure_ascii=False)
    short_id = uuid.uuid4().hex[:12]
    db.add(SysConfig(
        id=uuid.uuid4(), config_key=f"security.rule.{short_id}", config_value=rule_data,
        config_type="JSON", category="SECURITY_RULE", description=body.rule_name,
        is_encrypted=False, created_at=datetime.now(), created_by=user.id,
    ))
    await db.flush()
    return APIResponse(message="보안 규칙이 추가되었습니다")


@router.put("/security-rules/{rule_id}", response_model=APIResponse)
async def update_security_rule(
    rule_id: str, body: SecurityRuleUpdate,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """보안 규칙 수정"""
    import json as _json
    row = (await db.execute(
        select(SysConfig).where(SysConfig.id == uuid.UUID(rule_id), SysConfig.category == "SECURITY_RULE")
    )).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="보안 규칙을 찾을 수 없습니다")
    try:
        data = _json.loads(row.config_value or "{}")
    except Exception:
        data = {}
    if body.rule_name is not None:
        data["rule_name"] = body.rule_name
    if body.value is not None:
        data["value"] = body.value
    if body.is_active is not None:
        data["is_active"] = body.is_active
    if body.description is not None:
        data["description"] = body.description
    row.config_value = _json.dumps(data, ensure_ascii=False)
    row.description = data.get("rule_name", row.description)
    row.updated_at = datetime.now()
    row.updated_by = user.id
    await db.flush()
    return APIResponse(message="보안 규칙이 수정되었습니다")


@router.delete("/security-rules/{rule_id}", response_model=APIResponse)
async def delete_security_rule(
    rule_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """보안 규칙 삭제"""
    row = (await db.execute(
        select(SysConfig).where(SysConfig.id == uuid.UUID(rule_id), SysConfig.category == "SECURITY_RULE")
    )).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="보안 규칙을 찾을 수 없습니다")
    row.is_deleted = True
    row.updated_at = datetime.now()
    return APIResponse(message="보안 규칙이 삭제되었습니다")


# ── 커스텀 카테고리 CRUD ──
@router.post("/custom-categories", response_model=APIResponse)
async def create_custom_category(
    body: CustomCategoryCreate, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """커스텀 설정 카테고리 생성"""
    import re
    cat_key = re.sub(r"[^a-zA-Z0-9가-힣_]", "", body.category_name.replace(" ", "_"))
    if not cat_key:
        raise HTTPException(status_code=400, detail="유효하지 않은 카테고리명입니다")
    category = f"USER_CUSTOM_{cat_key}"
    existing = (await db.execute(
        select(SysConfig).where(SysConfig.category == category, SysConfig.config_key == "_meta.category_name", SysConfig.is_deleted == False)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="이미 존재하는 카테고리입니다")
    db.add(SysConfig(
        id=uuid.uuid4(), config_key="_meta.category_name", config_value=body.category_name,
        config_type="STRING", category=category, description=f"커스텀 카테고리: {body.category_name}",
        is_encrypted=False, created_at=datetime.now(), created_by=user.id,
    ))
    await db.flush()
    return APIResponse(data={"category_key": cat_key}, message="카테고리가 생성되었습니다")


@router.delete("/custom-categories/{category_key}", response_model=APIResponse)
async def delete_custom_category(
    category_key: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """커스텀 설정 카테고리 삭제 (소속 항목 포함)"""
    category = f"USER_CUSTOM_{category_key}"
    rows = (await db.execute(
        select(SysConfig).where(SysConfig.category == category, SysConfig.is_deleted == False)
    )).scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다")
    for r in rows:
        r.is_deleted = True
        r.updated_at = datetime.now()
    await db.flush()
    return APIResponse(message="카테고리가 삭제되었습니다")


@router.post("/custom-settings", response_model=APIResponse)
async def create_custom_setting(
    body: CustomSettingCreate, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """커스텀 카테고리 내 설정 항목 추가"""
    category = f"USER_CUSTOM_{body.category_key}"
    meta = (await db.execute(
        select(SysConfig).where(SysConfig.category == category, SysConfig.config_key == "_meta.category_name", SysConfig.is_deleted == False)
    )).scalar_one_or_none()
    if not meta:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다")
    import re
    setting_key = f"custom.{body.category_key}.{re.sub(r'[^a-zA-Z0-9가-힣_]', '', body.setting_name.replace(' ', '_'))}"
    db.add(SysConfig(
        id=uuid.uuid4(), config_key=setting_key, config_value=body.setting_value,
        config_type=body.setting_type, category=category, description=body.setting_name,
        is_encrypted=False, created_at=datetime.now(), created_by=user.id,
    ))
    await db.flush()
    return APIResponse(message="설정 항목이 추가되었습니다")


@router.delete("/custom-settings/{setting_id}", response_model=APIResponse)
async def delete_custom_setting(
    setting_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """커스텀 카테고리 내 설정 항목 삭제"""
    row = (await db.execute(
        select(SysConfig).where(SysConfig.id == uuid.UUID(setting_id), SysConfig.category.like("USER_CUSTOM_%"))
    )).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="설정 항목을 찾을 수 없습니다")
    row.is_deleted = True
    row.updated_at = datetime.now()
    return APIResponse(message="설정 항목이 삭제되었습니다")
