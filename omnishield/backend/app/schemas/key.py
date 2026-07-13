from datetime import datetime
from typing import Optional
from uuid import UUID
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    rate_limit: int = Field(default=60, ge=1, le=10000)

class APIKeyResponse(BaseModel):
    id: UUID
    name: str
    rate_limit: int
    status: str
    created_at: datetime
    last_used: Optional[datetime] = None

    class Config:
        from_attributes = True

class APIKeyNewResponse(BaseModel):
    key_details: APIKeyResponse
    raw_key: str
