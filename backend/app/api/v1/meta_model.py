"""메타모델 API"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.meta_model import MetaModel, MetaModelAttribute, MetaModelEntity
from app.schemas.common import APIResponse

router = APIRouter()


class MetaModelEntityCreate(BaseModel):
    entity_name: str
    entity_name_kr: str | None = None
    entity_type: str | None = "TABLE"
    owner: str | None = None
    description: str | None = None


class MetaModelAttributeCreate(BaseModel):
    attr_name: str
    attr_name_kr: str | None = None
    term_id: int | None = None
    domain_id: int | None = None
    data_type: str | None = None
    length: int | None = None
    decimal_places: int | None = 0
    is_pk: bool = False
    is_nullable: bool = True
    default_value: str | None = None
    description: str | None = None


class MetaModelCreate(BaseModel):
    model_type: str  # LOGICAL / PHYSICAL
    model_name: str
    system_name: str | None = None
    sub_system: str | None = None
    db_account: str | None = None
    description: str | None = None
    version: str | None = None
    classification_id: int | None = None
    entities: list[MetaModelEntityCreate] = []


class MetaModelAttributeResponse(BaseModel):
    id: int
    attr_name: str
    attr_name_kr: str | None = None
    term_id: int | None = None
    domain_id: int | None = None
    data_type: str | None = None
    length: int | None = None
    decimal_places: int | None = None
    is_pk: bool
    is_nullable: bool
    default_value: str | None = None
    description: str | None = None
    model_config = {"from_attributes": True}


class MetaModelEntityResponse(BaseModel):
    id: int
    entity_name: str
    entity_name_kr: str | None = None
    entity_type: str | None = None
    owner: str | None = None
    description: str | None = None
    attributes: list[MetaModelAttributeResponse] = []
    model_config = {"from_attributes": True}


class MetaModelResponse(BaseModel):
    id: int
    model_type: str
    model_name: str
    system_name: str | None = None
    sub_system: str | None = None
    db_account: str | None = None
    description: str | None = None
    version: str | None = None
    classification_id: int | None = None
    status: str
    entities: list[MetaModelEntityResponse] = []
    model_config = {"from_attributes": True}


@router.get("", response_model=APIResponse[list[MetaModelResponse]])
async def list_models(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MetaModel).where(MetaModel.is_deleted == False).order_by(MetaModel.id.desc())
    )
    items = result.scalars().all()
    return APIResponse(data=items)


@router.get("/{model_id}", response_model=APIResponse[MetaModelResponse])
async def get_model(model_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MetaModel).where(MetaModel.id == model_id, MetaModel.is_deleted == False)
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # 엔터티 및 속성 조회
    entities_result = await db.execute(
        select(MetaModelEntity).where(MetaModelEntity.model_id == model_id).order_by(MetaModelEntity.sort_order)
    )
    entities = entities_result.scalars().all()

    entity_ids = [e.id for e in entities]
    attrs_result = await db.execute(
        select(MetaModelAttribute).where(MetaModelAttribute.entity_id.in_(entity_ids)).order_by(MetaModelAttribute.sort_order)
    )
    attrs = attrs_result.scalars().all()
    attrs_by_entity = {}
    for attr in attrs:
        attrs_by_entity.setdefault(attr.entity_id, []).append(attr)

    response_entities = []
    for entity in entities:
        entity_resp = MetaModelEntityResponse.model_validate(entity)
        entity_resp.attributes = [
            MetaModelAttributeResponse.model_validate(a)
            for a in attrs_by_entity.get(entity.id, [])
        ]
        response_entities.append(entity_resp)

    model_resp = MetaModelResponse.model_validate(model)
    model_resp.entities = response_entities
    return APIResponse(data=model_resp)


@router.post("", response_model=APIResponse[MetaModelResponse])
async def create_model(body: MetaModelCreate, db: AsyncSession = Depends(get_db)):
    model = MetaModel(
        model_type=body.model_type,
        model_name=body.model_name,
        system_name=body.system_name,
        sub_system=body.sub_system,
        db_account=body.db_account,
        description=body.description,
        version=body.version,
        classification_id=body.classification_id,
    )
    db.add(model)
    await db.flush()
    await db.refresh(model)

    for entity_data in body.entities:
        entity = MetaModelEntity(model_id=model.id, **entity_data.model_dump())
        db.add(entity)

    await db.flush()
    return APIResponse(data=model, message="Created")


@router.put("/{model_id}", response_model=APIResponse[MetaModelResponse])
async def update_model(model_id: int, body: MetaModelCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MetaModel).where(MetaModel.id == model_id, MetaModel.is_deleted == False)
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    model.model_type = body.model_type
    model.model_name = body.model_name
    model.system_name = body.system_name
    model.sub_system = body.sub_system
    model.db_account = body.db_account
    model.description = body.description
    model.version = body.version
    model.classification_id = body.classification_id

    await db.flush()
    await db.refresh(model)
    return APIResponse(data=model, message="Updated")
