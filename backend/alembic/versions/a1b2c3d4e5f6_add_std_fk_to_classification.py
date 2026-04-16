"""add_std_fk_to_classification

Revision ID: a1b2c3d4e5f6
Revises: 587f20556e83
Create Date: 2026-04-14 14:00:00.000000

REQ-DHUB-004-002-001: 데이터 분류 ↔ 표준 단어/용어/코드/도메인 연동
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '587f20556e83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('data_classification', sa.Column('std_word_id', sa.Integer(), nullable=True, comment='연동단어ID'))
    op.add_column('data_classification', sa.Column('std_term_id', sa.Integer(), nullable=True, comment='연동용어ID'))
    op.add_column('data_classification', sa.Column('std_domain_id', sa.Integer(), nullable=True, comment='연동도메인ID'))
    op.add_column('data_classification', sa.Column('std_code_id', sa.Integer(), nullable=True, comment='연동코드ID'))

    op.create_foreign_key(
        'fk_data_class_std_word', 'data_classification', 'std_word',
        ['std_word_id'], ['id'], ondelete='SET NULL',
    )
    op.create_foreign_key(
        'fk_data_class_std_term', 'data_classification', 'std_term',
        ['std_term_id'], ['id'], ondelete='SET NULL',
    )
    op.create_foreign_key(
        'fk_data_class_std_domain', 'data_classification', 'std_domain',
        ['std_domain_id'], ['id'], ondelete='SET NULL',
    )
    op.create_foreign_key(
        'fk_data_class_std_code', 'data_classification', 'std_code',
        ['std_code_id'], ['id'], ondelete='SET NULL',
    )

    op.create_index('ix_data_class_std_word', 'data_classification', ['std_word_id'], unique=False)
    op.create_index('ix_data_class_std_term', 'data_classification', ['std_term_id'], unique=False)
    op.create_index('ix_data_class_std_domain', 'data_classification', ['std_domain_id'], unique=False)
    op.create_index('ix_data_class_std_code', 'data_classification', ['std_code_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_data_class_std_code', table_name='data_classification')
    op.drop_index('ix_data_class_std_domain', table_name='data_classification')
    op.drop_index('ix_data_class_std_term', table_name='data_classification')
    op.drop_index('ix_data_class_std_word', table_name='data_classification')
    op.drop_constraint('fk_data_class_std_code', 'data_classification', type_='foreignkey')
    op.drop_constraint('fk_data_class_std_domain', 'data_classification', type_='foreignkey')
    op.drop_constraint('fk_data_class_std_term', 'data_classification', type_='foreignkey')
    op.drop_constraint('fk_data_class_std_word', 'data_classification', type_='foreignkey')
    op.drop_column('data_classification', 'std_code_id')
    op.drop_column('data_classification', 'std_domain_id')
    op.drop_column('data_classification', 'std_term_id')
    op.drop_column('data_classification', 'std_word_id')
