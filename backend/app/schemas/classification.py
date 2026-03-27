from datetime import datetime

from pydantic import BaseModel


# ── 분류체계 ──
class ClassificationCreate(BaseModel):
    parent_id: int | None = None
    level: int
    name: str
    code: str
    description: str | None = None
    sort_order: int = 0


class ClassificationUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    sort_order: int | None = None
    status: str | None = None


class ClassificationResponse(BaseModel):
    id: int
    parent_id: int | None = None
    level: int
    name: str
    code: str
    description: str | None = None
    dataset_count: int
    sort_order: int
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ClassificationTreeNode(ClassificationResponse):
    children: list["ClassificationTreeNode"] = []


# ── 데이터 등급 ──
class DataGradeResponse(BaseModel):
    id: int
    grade_code: str
    grade_name: str
    description: str | None = None
    access_scope: str | None = None
    dataset_count: int
    anonymize_required: str | None = None
    sort_order: int

    model_config = {"from_attributes": True}


class DataGradeUpdate(BaseModel):
    grade_name: str | None = None
    description: str | None = None
    access_scope: str | None = None
    anonymize_required: str | None = None


# ── 동기화 이력 ──
class SyncLogResponse(BaseModel):
    id: int
    classification_id: int | None = None
    hub_code: str | None = None
    portal_code: str | None = None
    sync_status: str | None = None
    synced_at: datetime | None = None
    details: dict | None = None

    model_config = {"from_attributes": True}
