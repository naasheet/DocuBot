from pydantic import BaseModel
from datetime import datetime

class RepositoryBase(BaseModel):
    name: str
    full_name: str
    description: str | None = None
    url: str

class RepositoryCreate(RepositoryBase):
    github_id: int

class Repository(RepositoryBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
