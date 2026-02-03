from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Repository(Base):
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    github_id = Column(Integer, unique=True, index=True)
    name = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    description = Column(String)
    url = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="repositories")
    chat_sessions = relationship("ChatSession", back_populates="repository", cascade="all, delete-orphan")
    documentation = relationship("Documentation", back_populates="repository", cascade="all, delete-orphan")
    cache_entries = relationship("RepositoryCache", back_populates="repository", cascade="all, delete-orphan")
    files = relationship("RepositoryFile", back_populates="repository", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_repositories_user_id", "user_id"),
        Index("ix_repositories_full_name", "full_name"),
    )

    def __repr__(self):
        return f"<Repository(id={self.id}, full_name='{self.full_name}', is_active={self.is_active})>"
