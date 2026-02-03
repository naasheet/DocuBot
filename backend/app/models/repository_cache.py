from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class RepositoryCache(Base):
    __tablename__ = "repository_cache"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    cache_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    repository = relationship("Repository", back_populates="cache_entries")

    __table_args__ = (
        UniqueConstraint("repository_id", "cache_type", name="uq_repo_cache_type"),
        Index("ix_repo_cache_repo_type", "repository_id", "cache_type"),
    )

    def __repr__(self):
        return f"<RepositoryCache(id={self.id}, repo_id={self.repository_id}, type='{self.cache_type}')>"
