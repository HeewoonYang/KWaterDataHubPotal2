"""포털 카탈로그 API"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user, get_current_user_optional
from app.database import get_db
from app.schemas.common import APIResponse, PageRequest, PageResponse
from app.schemas.portal import CatalogDatasetDetail, CatalogDatasetListItem, CategoryTreeItem, LineageEdgeResponse, LineageGraphResponse, LineageNodeResponse
from app.services import portal_catalog_service
from app.models.catalog import CatalogDataset, CatalogLineage
from app.models.quality import QualityCheckResult

router = APIRouter()


@router.get("/datasets", response_model=PageResponse[CatalogDatasetListItem])
async def list_datasets(
    page: int = 1, page_size: int = 20, search: str | None = None,
    sort_by: str | None = None, sort_order: str = "desc",
    classification_id: int | None = None, grade_id: int | None = None, data_format: str | None = None,
    category: str | None = None, type: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser | None = Depends(get_current_user_optional),
):
    grades = user.data_grades if user else [3]
    params = PageRequest(page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order)
    # type 파라미터를 data_format으로 매핑
    fmt = data_format or (type if type and type != '전체' else None)
    return await portal_catalog_service.get_datasets(db, params, grades, classification_id, grade_id, fmt, category)


@router.get("/datasets/{dataset_id}", response_model=APIResponse[CatalogDatasetDetail])
async def get_dataset(
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser | None = Depends(get_current_user_optional),
):
    grades = user.data_grades if user else [3]
    detail = await portal_catalog_service.get_dataset_detail(db, dataset_id, grades)
    if not detail:
        raise HTTPException(status_code=404, detail="데이터셋을 찾을 수 없습니다")
    return APIResponse(data=detail)


@router.get("/categories", response_model=APIResponse[list[CategoryTreeItem]])
async def get_categories(db: AsyncSession = Depends(get_db)):
    data = await portal_catalog_service.get_categories(db)
    return APIResponse(data=data)


@router.get("/search", response_model=PageResponse[CatalogDatasetListItem])
async def search_datasets(
    keyword: str = "", page: int = 1, page_size: int = 20,
    data_format: str | None = None, grade_id: int | None = None,
    sort_by: str | None = None, sort_order: str = "desc",
    db: AsyncSession = Depends(get_db),
    user: CurrentUser | None = Depends(get_current_user_optional),
):
    grades = user.data_grades if user else [3]
    params = PageRequest(page=page, page_size=page_size, search=keyword, sort_by=sort_by, sort_order=sort_order)
    return await portal_catalog_service.get_datasets(db, params, grades, data_format=data_format, grade_id=grade_id)


@router.get("/lineage", response_model=APIResponse[LineageGraphResponse])
async def get_lineage_graph(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser | None = Depends(get_current_user_optional),
):
    """데이터 리니지 그래프 (노드 + 엣지)"""
    from sqlalchemy import select, func

    # 모든 데이터셋을 노드로
    datasets = (await db.execute(
        select(CatalogDataset).where(CatalogDataset.status == "ACTIVE")
    )).scalars().all()

    # 최신 품질 점수 가져오기
    quality_map: dict = {}
    for ds in datasets:
        qr = (await db.execute(
            select(QualityCheckResult.score)
            .where(QualityCheckResult.dataset_name == ds.dataset_name)
            .order_by(QualityCheckResult.executed_at.desc())
            .limit(1)
        )).scalar_one_or_none()
        if qr is not None:
            quality_map[str(ds.id)] = float(qr)

    nodes = []
    node_ids = set()
    for ds in datasets:
        node_ids.add(str(ds.id))
        nodes.append(LineageNodeResponse(
            id=ds.id, dataset_name=ds.dataset_name, dataset_name_kr=ds.dataset_name_kr,
            node_type="DATASET", source_system=ds.source_system,
            owner_department=ds.owner_department, data_format=ds.data_format,
            row_count=ds.row_count, quality_score=quality_map.get(str(ds.id)),
            status="ACTIVE",
        ))

    # 리니지 엣지
    lineages = (await db.execute(
        select(CatalogLineage).where(CatalogLineage.is_deleted == False)
    )).scalars().all()

    edges = []
    for ln in lineages:
        up_name = None
        down_name = None
        # upstream이 없으면 외부 소스 노드 생성
        if ln.upstream_dataset_id is None:
            ext_id = f"ext-{ln.id}"
            if ext_id not in node_ids:
                node_ids.add(ext_id)
                src_name = (ln.description or ln.pipeline_name or "외부 원천").split("/")[0].replace("원천:", "").strip()
                import uuid as _uuid
                nodes.append(LineageNodeResponse(
                    id=_uuid.UUID(int=hash(ext_id) % (2**128)),
                    dataset_name=src_name, node_type="EXTERNAL", source_system="외부",
                    status="ACTIVE",
                ))
            up_name = ln.description or "외부"
        else:
            up_ds = next((d for d in datasets if d.id == ln.upstream_dataset_id), None)
            up_name = up_ds.dataset_name if up_ds else str(ln.upstream_dataset_id)

        down_ds = next((d for d in datasets if d.id == ln.downstream_dataset_id), None)
        down_name = down_ds.dataset_name if down_ds else str(ln.downstream_dataset_id)

        edges.append(LineageEdgeResponse(
            id=ln.id,
            upstream_id=str(ln.upstream_dataset_id) if ln.upstream_dataset_id else f"ext-{ln.id}",
            downstream_id=str(ln.downstream_dataset_id),
            upstream_name=up_name, downstream_name=down_name,
            lineage_type=ln.lineage_type, pipeline_name=ln.pipeline_name,
            description=ln.description,
        ))

    return APIResponse(data=LineageGraphResponse(nodes=nodes, edges=edges))
