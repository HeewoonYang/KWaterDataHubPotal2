"""포털 AI 검색 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user_optional
from app.database import get_db
from app.schemas.common import APIResponse
from app.schemas.portal import AiSearchRequest, AiSearchResponse
from app.services import portal_ai_service

router = APIRouter()


@router.post("/search", response_model=APIResponse[AiSearchResponse])
async def ai_search(
    body: AiSearchRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser | None = Depends(get_current_user_optional),
):
    user_id = user.id if user else None
    result = await portal_ai_service.search(db, body.query, user_id)
    return APIResponse(data=result)


@router.get("/suggestions", response_model=APIResponse[list[str]])
async def get_suggestions():
    data = await portal_ai_service.get_suggestions()
    return APIResponse(data=data)
