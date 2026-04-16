"""enable_postgis_extension

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-16 10:00:00.000000

공간정보(GIS) 수집 파이프라인: PostGIS 확장 활성화 및 spatial_gis 스키마 생성
- postgis/postgis:16-3.4-alpine 이미지에서 확장 제공
- 수집된 공간데이터를 저장할 전용 스키마 생성
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE SCHEMA IF NOT EXISTS spatial_gis")
    op.execute("COMMENT ON SCHEMA spatial_gis IS '공간정보 수집 파이프라인 전용 스키마 (geometry 컬럼 저장소)'")


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS spatial_gis CASCADE")
    op.execute("DROP EXTENSION IF EXISTS postgis")
