"""Add github_access_token to users

Revision ID: 1b2c3d4e5f6a
Revises: 9c3f7d8b2a11
Create Date: 2026-02-02 20:50:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1b2c3d4e5f6a"
down_revision = "9c3f7d8b2a11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("github_access_token", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "github_access_token")
