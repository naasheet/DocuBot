from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class RepositoryFile(Base):
    __tablename__ = "repository_files"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    path = Column(String, nullable=False)
    language = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    repository = relationship("Repository", back_populates="files")

    __table_args__ = (
        UniqueConstraint("repository_id", "path", name="uq_repo_files_path"),
        Index("ix_repo_files_repo_path", "repository_id", "path"),
    )

    def __repr__(self):
        return f"<RepositoryFile(id={self.id}, repo_id={self.repository_id}, path='{self.path}')>"
