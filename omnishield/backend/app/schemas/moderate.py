from typing import List, Optional, Any
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

class BoundingBoxSchema(BaseModel):
    label: str
    box: List[int]
    score: float

class ModerationResponseData(BaseModel):
    decision: str = Field(description="'safe' or 'unsafe'")
    risk_level: str = Field(description="'low', 'medium', 'high', or 'critical'")
    confidence: float
    detected_labels: List[str]
    bounding_boxes: List[BoundingBoxSchema]
    processing_time: float
    recommended_action: str = Field(description="'allow', 'quarantine', or 'block'")
    reason: Optional[str] = None
    cached: bool = False

class ModerationResponse(BaseModel):
    success: bool
    message: str
    data: ModerationResponseData

class BatchTaskResponse(BaseModel):
    task_id: str
    status: str
    total_images: int
    message: str
