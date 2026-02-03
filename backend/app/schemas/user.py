from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Literal
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr = Field(..., examples=["user@example.com"])
    full_name: str | None = Field(None, examples=["John"])

class UserCreate(UserBase):
    full_name: str = Field(..., min_length=1, examples=["John"])
    password: str = Field(..., min_length=8, examples=["strongpassword123"])

class UserLogin(BaseModel):
    email: EmailStr = Field(..., examples=["user@example.com"])
    password: str = Field(..., min_length=1, examples=["password123"])

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., examples=["user@example.com"])
    method: Literal["reset", "login"] = Field(..., examples=["reset"])

class ForgotPasswordResponse(BaseModel):
    message: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., examples=["user@example.com"])
    code: str = Field(..., min_length=4, max_length=12, examples=["123456"])
    new_password: str = Field(..., min_length=8, examples=["newstrongpassword123"])

class LoginCodeRequest(BaseModel):
    email: EmailStr = Field(..., examples=["user@example.com"])
    code: str = Field(..., min_length=4, max_length=12, examples=["123456"])

class UserNameUpdate(BaseModel):
    full_name: str = Field(..., min_length=1, examples=["John"])

class User(UserBase):
    id: int = Field(..., examples=[1])
    is_active: bool = Field(True, examples=[True])
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
