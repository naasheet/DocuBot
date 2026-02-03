"""Add performance indexes

Revision ID: 2a6b7c8d9e10
Revises: 1b2c3d4e5f6a
Create Date: 2026-02-02 21:40:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "2a6b7c8d9e10"
down_revision = "1b2c3d4e5f6a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_repositories_user_id", "repositories", ["user_id"])
    op.create_index("ix_repositories_full_name", "repositories", ["full_name"])

    op.create_index("ix_documentation_repo_type", "documentation", ["repository_id", "doc_type"])

    op.create_index("ix_repo_cache_repo_type", "repository_cache", ["repository_id", "cache_type"])
    op.create_index("ix_repo_files_repo_path", "repository_files", ["repository_id", "path"])

    op.create_index("ix_chat_sessions_user_id", "chat_sessions", ["user_id"])
    op.create_index("ix_chat_sessions_repo_id", "chat_sessions", ["repository_id"])
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])
    op.create_index("ix_chat_messages_session_created", "chat_messages", ["session_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_chat_messages_session_created", table_name="chat_messages")
    op.drop_index("ix_chat_messages_session_id", table_name="chat_messages")
    op.drop_index("ix_chat_sessions_repo_id", table_name="chat_sessions")
    op.drop_index("ix_chat_sessions_user_id", table_name="chat_sessions")

    op.drop_index("ix_repo_files_repo_path", table_name="repository_files")
    op.drop_index("ix_repo_cache_repo_type", table_name="repository_cache")

    op.drop_index("ix_documentation_repo_type", table_name="documentation")

    op.drop_index("ix_repositories_full_name", table_name="repositories")
    op.drop_index("ix_repositories_user_id", table_name="repositories")
