"""실시간 계측DB API"""
from fastapi import APIRouter

from app.schemas.common import APIResponse
from app.services.portal_measurement_service import portal_measurement_service

router = APIRouter()


@router.get("/summary", response_model=APIResponse)
async def get_summary():
    data = await portal_measurement_service.get_summary()
    return APIResponse(success=True, message="OK", data=data)


@router.get("/regions", response_model=APIResponse)
async def get_regions():
    data = await portal_measurement_service.get_regions()
    return APIResponse(success=True, message="OK", data=data)


@router.get("/offices", response_model=APIResponse)
async def get_offices(region: str = None):
    data = await portal_measurement_service.get_offices(region)
    return APIResponse(success=True, message="OK", data=data)


@router.get("/sites", response_model=APIResponse)
async def get_site_detail(site: str = None):
    data = await portal_measurement_service.get_site_detail(site)
    return APIResponse(success=True, message="OK", data=data)


@router.get("/tags", response_model=APIResponse)
async def get_tags(site: str = None):
    data = await portal_measurement_service.get_tags(site)
    return APIResponse(success=True, message="OK", data=data)
