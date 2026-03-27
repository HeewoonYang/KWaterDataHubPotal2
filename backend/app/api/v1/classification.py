"""분류체계/등급 API"""
import math

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.classification import ClassificationSyncLog, DataClassification, DataGrade
from app.schemas.classification import (
    ClassificationCreate, ClassificationResponse, ClassificationTreeNode, ClassificationUpdate,
    DataGradeResponse, DataGradeUpdate, SyncLogResponse,
)
from app.schemas.common import APIResponse, PageResponse

router = APIRouter()


def _build_tree(items: list, parent_id: int | None = None) -> list[dict]:
    """재귀적으로 트리 구조 생성"""
    nodes = []
    for item in items:
        if item.parent_id == parent_id:
            node = ClassificationTreeNode.model_validate(item)
            node.children = _build_tree(items, item.id)
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

    if format == "tree":
        tree = _build_tree(items, None)
        return APIResponse(data=tree)

    data = [ClassificationResponse.model_validate(item) for item in items]
    return APIResponse(data=data)


@router.get("/{cls_id}", response_model=APIResponse[ClassificationResponse])
async def get_classification(cls_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DataClassification).where(DataClassification.id == cls_id, DataClassification.is_deleted == False)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Classification not found")
    return APIResponse(data=item)


@router.post("", response_model=APIResponse[ClassificationResponse])
async def create_classification(body: ClassificationCreate, db: AsyncSession = Depends(get_db)):
    cls = DataClassification(**body.model_dump())
    db.add(cls)
    await db.flush()
    await db.refresh(cls)
    return APIResponse(data=cls, message="Created")


@router.put("/{cls_id}", response_model=APIResponse[ClassificationResponse])
async def update_classification(cls_id: int, body: ClassificationUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DataClassification).where(DataClassification.id == cls_id, DataClassification.is_deleted == False)
    )
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(status_code=404, detail="Classification not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(cls, key, value)
    await db.flush()
    await db.refresh(cls)
    return APIResponse(data=cls, message="Updated")


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


# ── 동기화 ──
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
