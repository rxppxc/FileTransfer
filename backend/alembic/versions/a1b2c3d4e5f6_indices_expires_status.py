"""indices expires_at y status en transfers

Revision ID: a1b2c3d4e5f6
Revises: 6e03f9b815bf
Create Date: 2026-06-23 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "6e03f9b815bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_transfers_expires_at", "transfers", ["expires_at"])
    op.create_index("ix_transfers_status",     "transfers", ["status"])


def downgrade() -> None:
    op.drop_index("ix_transfers_expires_at", table_name="transfers")
    op.drop_index("ix_transfers_status",     table_name="transfers")
