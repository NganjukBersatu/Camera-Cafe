"""add order_note to visits

Revision ID: ffd6213ead84
Revises: 2003c4715a4f
Create Date: 2026-06-22 10:08:19.195716

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ffd6213ead84'
down_revision: Union[str, Sequence[str], None] = '2003c4715a4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('visits', sa.Column('order_note', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('visits', 'order_note')
