"""Add repository files

Revision ID: 9c3f7d8b2a11
Revises: 6b1d6f48f0d2
Create Date: 2026-02-02 02:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "9c3f7d8b2a11"
down_revision = "6b1d6f48f0d2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "repository_files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repository_id", sa.Integer(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repository_id", "path", name="uq_repo_files_path"),
    )
    op.create_index(op.f("ix_repository_files_id"), "repository_files", ["id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_repository_files_id"), table_name="repository_files")
    op.drop_table("repository_files")
