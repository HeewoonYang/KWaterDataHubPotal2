"""포털 유통 API"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.database import get_db
from app.schemas.common import APIResponse, PageRequest, PageResponse
from app.schemas.portal import ApiKeyResponse, DistDatasetListItem, DistDownloadItem, DistRequestCreate, DistRequestResponse
from app.services import portal_distribution_service

router = APIRouter()


@router.get("/datasets", response_model=PageResponse[DistDatasetListItem])
async def list_dist_datasets(
    page: int = 1, page_size: int = 20, search: str | None = None,
    classification_id: int | None = None, grade_id: int | None = None, data_format: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    params = PageRequest(page=page, page_size=page_size, search=search)
    return await portal_distribution_service.get_dist_datasets(db, params, user.data_grades, classification_id, grade_id, data_format)


@router.post("/requests", response_model=APIResponse[DistRequestResponse])
async def create_request(
    body: DistRequestCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    result = await portal_distribution_service.create_request(db, user.id, body)
    return APIResponse(data=result, message="신청이 접수되었습니다")


@router.get("/requests", response_model=PageResponse[DistRequestResponse])
async def list_requests(
    page: int = 1, page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    params = PageRequest(page=page, page_size=page_size)
    return await portal_distribution_service.get_user_requests(db, user.id, params)


@router.get("/downloads", response_model=PageResponse[DistDownloadItem])
async def list_downloads(
    page: int = 1, page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    params = PageRequest(page=page, page_size=page_size)
    return await portal_distribution_service.get_user_downloads(db, user.id, params)


@router.get("/download/{dataset_id}")
async def download_file(
    dataset_id: UUID, format: str = "CSV",
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    filename, content, media_type = await portal_distribution_service.generate_download(db, dataset_id, format, user.id)
    if not content:
        raise HTTPException(status_code=404, detail="데이터셋을 찾을 수 없습니다")
    return Response(content=content, media_type=media_type,
                    headers={"Content-Disposition": f"attachment; filename={filename}"})


# ── API 키 관리 ──

@router.post("/requests/{request_id}/api-key", response_model=APIResponse[ApiKeyResponse])
async def issue_api_key(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    try:
        result = await portal_distribution_service.issue_api_key(db, user.id, request_id)
        return APIResponse(data=result, message="API 키가 발급되었습니다")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/requests/{request_id}/api-key", response_model=APIResponse[ApiKeyResponse])
async def get_api_key_info(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    result = await portal_distribution_service.get_api_key_info(db, user.id, request_id)
    if not result:
        raise HTTPException(status_code=404, detail="API 키를 찾을 수 없습니다")
    return APIResponse(data=result)


@router.post("/requests/{request_id}/api-key/regenerate", response_model=APIResponse[ApiKeyResponse])
async def regenerate_api_key(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    result = await portal_distribution_service.regenerate_api_key(db, user.id, request_id)
    return APIResponse(data=result, message="API 키가 재발급되었습니다")


@router.delete("/requests/{request_id}/api-key", response_model=APIResponse)
async def revoke_api_key(
    request_id: UUID, api_key_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    ok = await portal_distribution_service.revoke_api_key(db, user.id, api_key_id)
    if not ok:
        raise HTTPException(status_code=404, detail="API 키를 찾을 수 없습니다")
    return APIResponse(data={"revoked": True}, message="API 키가 폐기되었습니다")
