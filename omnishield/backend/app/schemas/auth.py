from datetime import datetime
from typing import Optional
from uuid import UUID
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=200)  # Allow longer passwords, we truncate to 72 in code

class UserRegisterSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=200)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
