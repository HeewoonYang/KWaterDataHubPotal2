"""분류체계/등급 API"""
import math

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.classification import ClassificationSyncLog, DataClassification, DataGrade
from app.models.standard import StdCode, StdDomain, StdTerm, StdWord
from app.schemas.classification import (
    ClassificationCreate, ClassificationResponse, ClassificationTreeNode, ClassificationUpdate,
    DataGradeResponse, DataGradeUpdate, SyncLogResponse,
)
from app.schemas.common import APIResponse, PageResponse

router = APIRouter()


async def _load_std_names(db: AsyncSession, items: list[DataClassification]) -> dict[int, dict]:
    """분류 목록에 연동된 표준사전 표시명을 한 번의 쿼리로 조회"""
    word_ids = {i.std_word_id for i in items if i.std_word_id}
    term_ids = {i.std_term_id for i in items if i.std_term_id}
    domain_ids = {i.std_domain_id for i in items if i.std_domain_id}
    code_ids = {i.std_code_id for i in items if i.std_code_id}

    word_map: dict[int, str] = {}
    term_map: dict[int, str] = {}
    domain_map: dict[int, str] = {}
    code_map: dict[int, str] = {}

    if word_ids:
        rows = (await db.execute(select(StdWord.id, StdWord.word_name).where(StdWord.id.in_(word_ids)))).all()
        word_map = {r[0]: r[1] for r in rows}
    if term_ids:
        rows = (await db.execute(select(StdTerm.id, StdTerm.term_name).where(StdTerm.id.in_(term_ids)))).all()
        term_map = {r[0]: r[1] for r in rows}
    if domain_ids:
        rows = (await db.execute(select(StdDomain.id, StdDomain.domain_name).where(StdDomain.id.in_(domain_ids)))).all()
        domain_map = {r[0]: r[1] for r in rows}
    if code_ids:
        rows = (await db.execute(select(StdCode.id, StdCode.code_group_name).where(StdCode.id.in_(code_ids)))).all()
        code_map = {r[0]: r[1] for r in rows}

    return {
        i.id: {
            "std_word_name": word_map.get(i.std_word_id) if i.std_word_id else None,
            "std_term_name": term_map.get(i.std_term_id) if i.std_term_id else None,
            "std_domain_name": domain_map.get(i.std_domain_id) if i.std_domain_id else None,
            "std_code_name": code_map.get(i.std_code_id) if i.std_code_id else None,
        }
        for i in items
    }


async def _validate_std_refs(db: AsyncSession, body) -> None:
    """표준사전 FK 유효성 검증 (존재 + 미삭제)"""
    checks = [
        (body.std_word_id, StdWord, "단어"),
        (body.std_term_id, StdTerm, "용어"),
        (body.std_domain_id, StdDomain, "도메인"),
        (body.std_code_id, StdCode, "코드"),
    ]
    for fk_id, model_cls, kind in checks:
        if fk_id is None:
            continue
        result = await db.execute(select(model_cls).where(model_cls.id == fk_id, model_cls.is_deleted == False))
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=400, detail=f"표준 {kind}사전(id={fk_id})을 찾을 수 없습니다")


def _to_response(item: DataClassification, names: dict | None = None) -> ClassificationResponse:
    resp = ClassificationResponse.model_validate(item)
    if names:
        resp.std_word_name = names.get("std_word_name")
        resp.std_term_name = names.get("std_term_name")
        resp.std_domain_name = names.get("std_domain_name")
        resp.std_code_name = names.get("std_code_name")
    return resp


def _build_tree(items: list, names_by_id: dict[int, dict], parent_id: int | None = None) -> list[ClassificationTreeNode]:
    """재귀적으로 트리 구조 생성"""
    nodes = []
    for item in items:
        if item.parent_id == parent_id:
            node = ClassificationTreeNode.model_validate(item)
            n = names_by_id.get(item.id) or {}
            node.std_word_name = n.get("std_word_name")
            node.std_term_name = n.get("std_term_name")
            node.std_domain_name = n.get("std_domain_name")
            node.std_code_name = n.get("std_code_name")
            node.children = _build_tree(items, names_by_id, item.id)
            nodes.append(node)
    return nodes


@router.get("", response_model=APIResponse)
async def list_classifications(
    format: str = "flat",  # flat | tree
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DataClassification)
        .where(DataClassification.is_deleted == False)
        .order_by(DataClassification.level, DataClassification.sort_order)
    )
    items = result.scalars().all()
    names_by_id = await _load_std_names(db, items)

    if format == "tree":
        tree = _build_tree(items, names_by_id, None)
        return APIResponse(data=tree)

    data = [_to_response(item, names_by_id.get(item.id)) for item in items]
    return APIResponse(data=data)


# ── 동기화 (/{cls_id}보다 먼저 선언해야 경로 충돌 방지) ──
@router.post("/sync", response_model=APIResponse)
async def trigger_sync(db: AsyncSession = Depends(get_db)):
    # TODO: Celery 태스크로 비동기 동기화 트리거
    return APIResponse(message="Sync triggered")


@router.get("/sync-status", response_model=APIResponse[list[SyncLogResponse]])
async def get_sync_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ClassificationSyncLog).order_by(ClassificationSyncLog.synced_at.desc()).limit(50)
    )
    logs = result.scalars().all()
    return APIResponse(data=logs)


# ── 등급 ──
@router.get("/grades", response_model=APIResponse[list[DataGradeResponse]])
async def list_grades(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DataGrade).order_by(DataGrade.sort_order))
    items = result.scalars().all()
    return APIResponse(data=items)


@router.get("/{cls_id}", response_model=APIResponse[ClassificationResponse])
async def get_classification(cls_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DataClassification).where(DataClassification.id == cls_id, DataClassification.is_deleted == False)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Classification not found")
    names = (await _load_std_names(db, [item])).get(item.id)
    return APIResponse(data=_to_response(item, names))


@router.post("", response_model=APIResponse[ClassificationResponse])
async def create_classification(body: ClassificationCreate, db: AsyncSession = Depends(get_db)):
    await _validate_std_refs(db, body)
    cls = DataClassification(**body.model_dump())
    db.add(cls)
    await db.flush()
    await db.refresh(cls)
    names = (await _load_std_names(db, [cls])).get(cls.id)
    return APIResponse(data=_to_response(cls, names), message="Created")


@router.put("/{cls_id}", response_model=APIResponse[ClassificationResponse])
async def update_classification(cls_id: int, body: ClassificationUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DataClassification).where(DataClassification.id == cls_id, DataClassification.is_deleted == False)
    )
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(status_code=404, detail="Classification not found")
    await _validate_std_refs(db, body)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(cls, key, value)
    await db.flush()
    await db.refresh(cls)
    names = (await _load_std_names(db, [cls])).get(cls.id)
    return APIResponse(data=_to_response(cls, names), message="Updated")


@router.delete("/{cls_id}", response_model=APIResponse)
async def delete_classification(cls_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DataClassification).where(DataClassification.id == cls_id, DataClassification.is_deleted == False)
    )
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(status_code=404, detail="Classification not found")
    cls.is_deleted = True
    await db.flush()
    return APIResponse(message="Deleted")


@router.put("/grades/{grade_id}", response_model=APIResponse[DataGradeResponse])
async def update_grade(grade_id: int, body: DataGradeUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DataGrade).where(DataGrade.id == grade_id))
    grade = result.scalar_one_or_none()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(grade, key, value)
    await db.flush()
    await db.refresh(grade)
    return APIResponse(data=grade, message="Updated")
