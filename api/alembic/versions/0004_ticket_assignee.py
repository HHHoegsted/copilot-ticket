"""ticket assignee

Revision ID: 0004
Revises: 0003
Create Date: 2025-01-04 00:00:00

"""
import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tickets", sa.Column("assignee_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_tickets_assignee_id_users", "tickets", "users", ["assignee_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_tickets_assignee_id_users", "tickets", type_="foreignkey")
    op.drop_column("tickets", "assignee_id")