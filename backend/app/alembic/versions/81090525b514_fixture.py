"""Fixture

Revision ID: 81090525b514
Revises: 95db47233cd9
Create Date: 2025-02-01 17:24:54.108923

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81090525b514'
down_revision: Union[str, None] = '95db47233cd9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
