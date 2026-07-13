import uuid
# pyrefly: ignore [missing-import]
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

# Set up JSON type helper (uses JSONB for PostgreSQL, falls back to standard JSON for other DBs like SQLite)
JSON_TYPE = JSONB().with_variant(JSON, "sqlite")

class ModerationLog(Base):
    __tablename__ = "moderation_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    image_hash = Column(String(64), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(512), nullable=True)
    
    decision = Column(String(50), nullable=False)           # 'safe', 'unsafe', 'review'
    risk_level = Column(String(50), nullable=False)         # 'low', 'medium', 'high', 'critical'
    confidence = Column(Float, nullable=False)
    
    # Store labels as JSON array: e.g. ["FEMALE_BREAST_EXPOSED", "VIOLENCE", "WEAPON"]
    detected_labels = Column(JSON_TYPE, nullable=False, default=list)
    
    # Store bounding boxes as JSON: e.g. [{"label": "...", "box": [...], "score": ...}]
    bounding_boxes = Column(JSON_TYPE, nullable=False, default=list)
    
    processing_time = Column(Float, nullable=False)
    recommended_action = Column(String(50), nullable=False) # 'allow', 'quarantine', 'block'
    reason = Column(String(512), nullable=True)
    
    # Multi-model results (stores detailed results from each AI model)
    model_results = Column(JSON_TYPE, nullable=True, default=dict)  # NEW: {"nsfw": {...}, "violence": {...}}
    model_versions = Column(JSON_TYPE, nullable=True, default=dict)  # NEW: {"nsfw": "nudenet-v3.4.2", ...}
    
    # Face detection metadata
    face_count = Column(Integer, nullable=True, default=0)  # NEW: Number of faces detected
    
    # Text moderation metadata
    detected_text = Column(String(1000), nullable=True)  # NEW: Extracted text from image
    contains_profanity = Column(String(10), nullable=True)  # NEW: 'yes', 'no', null
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="moderation_logs")
