from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class VideoModerationJobResponse(BaseModel):
    job_id: UUID
    status: str
    filename: str
    message: str
    status_url: str


class VideoFrameFlagSchema(BaseModel):
    id: UUID
    timestamp_seconds: float
    frame_index: int
    flag_category: str
    confidence: float
    decision: str
    detected_labels: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class VideoModerationStatusData(BaseModel):
    job_id: UUID
    filename: str
    status: str
    overall_status: Optional[str] = None
    risk_level: Optional[str] = None
    overall_confidence: Optional[float] = None
    recommended_action: Optional[str] = None
    reason: Optional[str] = None
    total_duration: Optional[float] = None
    frames_sampled: int = 0
    frames_flagged: int = 0
    frame_interval_seconds: float = 1.0
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    frame_flags: List[VideoFrameFlagSchema] = Field(default_factory=list)


class VideoModerationStatusResponse(BaseModel):
    success: bool
    message: str
    data: VideoModerationStatusData
