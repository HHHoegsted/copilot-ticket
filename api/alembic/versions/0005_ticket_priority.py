"""ticket priority

Revision ID: 0005
Revises: 0004
Create Date: 2025-01-05 00:00:00

"""
import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tickets",
        sa.Column("priority", sa.String(length=16), nullable=False, server_default="normal"),
    )


def downgrade() -> None:
    op.drop_column("tickets", "priority")