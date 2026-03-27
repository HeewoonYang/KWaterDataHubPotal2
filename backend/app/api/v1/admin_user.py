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
from app.models.user import (UserAccount, UserDataAccessPolicy, UserRole, UserRoleMap)
from app.models.classification import DataGrade
from app.schemas.admin import AccessPolicyResponse, RoleResponse, UserCreate, UserListResponse
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
    new_user = UserAccount(
        id=uuid.uuid4(), login_id=body.login_id, password_hash=hash_password(body.password),
        name=body.name, email=body.email, user_type=body.user_type, employee_no=body.employee_no,
        department_code=body.department_code, department_name=body.department_name,
        position=body.position, status="ACTIVE", created_at=datetime.now(),
    )
    db.add(new_user)

    role = (await db.execute(select(UserRole).where(UserRole.role_code == body.role_code))).scalar_one_or_none()
    if role:
        db.add(UserRoleMap(id=uuid.uuid4(), user_id=new_user.id, role_id=role.id, granted_by=user.id, granted_at=datetime.now(), status="ACTIVE"))

    await db.flush()
    return APIResponse(data=UserListResponse(
        id=new_user.id, login_id=new_user.login_id, name=new_user.name, email=new_user.email,
        user_type=new_user.user_type, employee_no=new_user.employee_no,
        department_name=new_user.department_name, position=new_user.position,
        status=new_user.status, role_code=body.role_code,
    ), message="사용자가 등록되었습니다")


@router.get("/roles", response_model=APIResponse[list[RoleResponse]])
async def list_roles(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(UserRole).order_by(UserRole.sort_order))).scalars().all()
    items = []
    for r in rows:
        cnt = (await db.execute(select(func.count()).where(UserRoleMap.role_id == r.id, UserRoleMap.status == "ACTIVE"))).scalar() or 0
        items.append(RoleResponse(
            id=r.id, role_code=r.role_code, role_name=r.role_name, description=r.description,
            is_system_role=r.is_system_role, can_access_admin=r.can_access_admin,
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
