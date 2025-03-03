"""Add new field to landings aand tags

Revision ID: 911347313098
Revises: f7b71177b0e2
Create Date: 2025-02-16 16:32:14.152609

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '911347313098'
down_revision: Union[str, None] = 'f7b71177b0e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tags',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_tags_id'), 'tags', ['id'], unique=False)
    op.add_column('landing', sa.Column('tag_id', sa.Integer(), nullable=True))
    op.add_column('landing', sa.Column('sales_count', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'landing', 'tags', ['tag_id'], ['id'])
    op.drop_column('landing', 'tag')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('landing', sa.Column('tag', mysql.VARCHAR(length=255), nullable=True))
    op.drop_constraint(None, 'landing', type_='foreignkey')
    op.drop_column('landing', 'sales_count')
    op.drop_column('landing', 'tag_id')
    op.drop_index(op.f('ix_tags_id'), table_name='tags')
    op.drop_table('tags')
    # ### end Alembic commands ###
