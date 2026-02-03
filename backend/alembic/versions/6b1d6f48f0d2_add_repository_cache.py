"""Add repository cache

Revision ID: 6b1d6f48f0d2
Revises: d3ea37fd7e03
Create Date: 2026-02-02 01:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6b1d6f48f0d2"
down_revision = "d3ea37fd7e03"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "repository_cache",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repository_id", sa.Integer(), nullable=False),
        sa.Column("cache_type", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repository_id", "cache_type", name="uq_repo_cache_type"),
    )
    op.create_index(op.f("ix_repository_cache_id"), "repository_cache", ["id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_repository_cache_id"), table_name="repository_cache")
    op.drop_table("repository_cache")
