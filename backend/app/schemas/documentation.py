from pydantic import BaseModel
from datetime import datetime

class DocumentationBase(BaseModel):
    doc_type: str
    content: str
    version: str | None = None

class DocumentationCreate(DocumentationBase):
    repository_id: int

class Documentation(DocumentationBase):
    id: int
    repository_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
