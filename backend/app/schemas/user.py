from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr = Field(..., examples=["user@example.com"])
    full_name: str | None = Field(None, examples=["John Doe"])

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, examples=["strongpassword123"])

class UserLogin(BaseModel):
    email: EmailStr = Field(..., examples=["user@example.com"])
    password: str = Field(..., min_length=1, examples=["password123"])

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class User(UserBase):
    id: int = Field(..., examples=[1])
    is_active: bool = Field(True, examples=[True])
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
