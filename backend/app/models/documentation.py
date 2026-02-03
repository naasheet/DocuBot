import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class DocType(str, enum.Enum):
    README = "readme"
    API = "api_reference"
    ARCHITECTURE = "architecture"

class Documentation(Base):
    __tablename__ = "documentation"
    
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    doc_type = Column(Enum(DocType), nullable=False)
    content = Column(Text)
    version = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    repository = relationship("Repository", back_populates="documentation")

    __table_args__ = (
        Index("ix_documentation_repo_type", "repository_id", "doc_type"),
    )

    def __repr__(self):
        return f"<Documentation(id={self.id}, type='{self.doc_type}', repo_id={self.repository_id})>"
