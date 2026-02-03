"""Add reset and login codes to users

Revision ID: 3c4d5e6f7a8b
Revises: 2a6b7c8d9e10
Create Date: 2026-02-03 09:35:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3c4d5e6f7a8b"
down_revision = "2a6b7c8d9e10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("reset_code_hash", sa.String(), nullable=True))
    op.add_column("users", sa.Column("reset_code_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("login_code_hash", sa.String(), nullable=True))
    op.add_column("users", sa.Column("login_code_expires_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "login_code_expires_at")
    op.drop_column("users", "login_code_hash")
    op.drop_column("users", "reset_code_expires_at")
    op.drop_column("users", "reset_code_hash")
