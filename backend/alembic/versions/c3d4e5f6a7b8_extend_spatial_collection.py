"""extend_spatial_collection

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-16 10:10:00.000000

공간정보 수집 확장:
- collection_spatial_config 컬럼 추가 (source_system, connection/auth/validation/event/target, schedule FK, last_*)
- collection_spatial_layer (중간 테이블)
- collection_spatial_history (이력 테이블)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- collection_spatial_config 확장 ---
    op.add_column('collection_spatial_config',
                  sa.Column('source_system', sa.String(50), nullable=True,
                            comment='소스시스템 (ARCGIS_REST/GEOSERVER_WFS/GEOSERVER_WMS/GEOJSON_URL/ORACLE_SPATIAL/SHAPEFILE)'))
    op.add_column('collection_spatial_config',
                  sa.Column('connection_config', JSONB(), nullable=True,
                            comment='연결구성 {base_url, service_path, layer_query_params}'))
    op.add_column('collection_spatial_config',
                  sa.Column('auth_config', JSONB(), nullable=True,
                            comment='인증구성 {auth_type: NONE/BASIC/TOKEN, token_enc, username, password_enc}'))
    op.add_column('collection_spatial_config',
                  sa.Column('target_schema', sa.String(100), server_default='spatial_gis', nullable=True,
                            comment='대상PostGIS스키마'))
    op.add_column('collection_spatial_config',
                  sa.Column('target_table', sa.String(200), nullable=True, comment='대상PostGIS테이블명'))
    op.add_column('collection_spatial_config',
                  sa.Column('validation_rules', JSONB(), nullable=True,
                            comment='검증규칙 {required_srid, geometry_types[], check_topology, max_feature_count}'))
    op.add_column('collection_spatial_config',
                  sa.Column('schedule_id', UUID(as_uuid=True), nullable=True, comment='스케줄ID'))
    op.add_column('collection_spatial_config',
                  sa.Column('event_trigger_config', JSONB(), nullable=True,
                            comment='이벤트트리거구성 {enabled, trigger_type: FILE_UPLOAD/KAFKA/API, topic_or_path}'))
    op.add_column('collection_spatial_config',
                  sa.Column('last_collected_at', sa.DateTime(), nullable=True, comment='최근수집시각'))
    op.add_column('collection_spatial_config',
                  sa.Column('last_status', sa.String(20), nullable=True, comment='최근상태 (SUCCESS/FAILED/RUNNING)'))
    op.add_column('collection_spatial_config',
                  sa.Column('feature_count', sa.BigInteger(), server_default='0', nullable=True, comment='최근수집피처수'))
    op.add_column('collection_spatial_config',
                  sa.Column('last_error_message', sa.Text(), nullable=True, comment='최근에러메시지'))

    op.create_foreign_key(
        'fk_collection_spatial_config_schedule',
        'collection_spatial_config', 'collection_schedule',
        ['schedule_id'], ['id'], ondelete='SET NULL'
    )
    op.create_index(
        'ix_collection_spatial_config_not_deleted',
        'collection_spatial_config', ['is_deleted'],
        postgresql_where=sa.text('is_deleted = false')
    )
    op.create_index(
        'ix_collection_spatial_config_schedule',
        'collection_spatial_config', ['schedule_id']
    )

    # --- collection_spatial_layer (중간) ---
    op.create_table(
        'collection_spatial_layer',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, comment='레이어ID'),
        sa.Column('config_id', UUID(as_uuid=True), nullable=False, comment='공간정보수집ID'),
        sa.Column('layer_name', sa.String(200), nullable=False, comment='레이어명'),
        sa.Column('geometry_type', sa.String(50), nullable=True,
                  comment='지오메트리유형 (POINT/LINESTRING/POLYGON/MULTIPOLYGON/GEOMETRY)'),
        sa.Column('srid', sa.Integer(), nullable=True, comment='SRID (EPSG 코드)'),
        sa.Column('attribute_schema', JSONB(), nullable=True, comment='속성스키마 [{name, type, nullable}]'),
        sa.Column('feature_count', sa.BigInteger(), server_default='0', comment='피처수'),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True, comment='최근동기화시각'),
        sa.Column('is_enabled', sa.Boolean(), server_default=sa.true(), comment='활성여부'),
        sa.Column('created_by', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(50), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.false()),
        sa.ForeignKeyConstraint(['config_id'], ['collection_spatial_config.id'], ondelete='CASCADE'),
        comment='공간정보수집레이어',
    )
    op.create_index(
        'uq_collection_spatial_layer',
        'collection_spatial_layer', ['config_id', 'layer_name'], unique=True
    )
    op.create_index(
        'ix_collection_spatial_layer_not_deleted',
        'collection_spatial_layer', ['is_deleted'],
        postgresql_where=sa.text('is_deleted = false')
    )

    # --- collection_spatial_history (이력) ---
    op.create_table(
        'collection_spatial_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, comment='이력ID'),
        sa.Column('config_id', UUID(as_uuid=True), nullable=False, comment='공간정보수집ID'),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), comment='시작시각'),
        sa.Column('ended_at', sa.DateTime(), nullable=True, comment='종료시각'),
        sa.Column('status', sa.String(20), nullable=False,
                  comment='상태 (RUNNING/SUCCESS/FAILED/CANCELLED)'),
        sa.Column('feature_count', sa.BigInteger(), server_default='0', comment='수집피처수'),
        sa.Column('invalid_feature_count', sa.BigInteger(), server_default='0', comment='무효피처수'),
        sa.Column('triggered_by', sa.String(20), nullable=True, comment='트리거유형 (SCHEDULE/EVENT/MANUAL)'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='에러메시지'),
        sa.Column('duration_ms', sa.Integer(), nullable=True, comment='소요시간(ms)'),
        sa.ForeignKeyConstraint(['config_id'], ['collection_spatial_config.id'], ondelete='CASCADE'),
        comment='공간정보수집이력',
    )
    op.create_index(
        'ix_collection_spatial_history_config',
        'collection_spatial_history', ['config_id', 'started_at']
    )


def downgrade() -> None:
    op.drop_index('ix_collection_spatial_history_config', table_name='collection_spatial_history')
    op.drop_table('collection_spatial_history')

    op.drop_index('ix_collection_spatial_layer_not_deleted', table_name='collection_spatial_layer')
    op.drop_index('uq_collection_spatial_layer', table_name='collection_spatial_layer')
    op.drop_table('collection_spatial_layer')

    op.drop_index('ix_collection_spatial_config_schedule', table_name='collection_spatial_config')
    op.drop_index('ix_collection_spatial_config_not_deleted', table_name='collection_spatial_config')
    op.drop_constraint('fk_collection_spatial_config_schedule', 'collection_spatial_config', type_='foreignkey')

    for col in [
        'last_error_message', 'feature_count', 'last_status', 'last_collected_at',
        'event_trigger_config', 'schedule_id', 'validation_rules', 'target_table',
        'target_schema', 'auth_config', 'connection_config', 'source_system',
    ]:
        op.drop_column('collection_spatial_config', col)
