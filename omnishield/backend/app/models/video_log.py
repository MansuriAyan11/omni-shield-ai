import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.log import JSON_TYPE


class VideoModerationLog(Base):
    __tablename__ = "video_moderation_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    filename = Column(String(255), nullable=False)
    total_duration = Column(Float, nullable=True)
    status = Column(String(50), nullable=False, default="pending", index=True)  # pending, processing, completed, failed

    overall_status = Column(String(50), nullable=True)  # safe, unsafe
    risk_level = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=True)  # overall_confidence
    recommended_action = Column(String(50), nullable=True)
    reason = Column(String(512), nullable=True)

    frames_sampled = Column(Integer, nullable=False, default=0)
    frames_flagged = Column(Integer, nullable=False, default=0)
    frame_interval_seconds = Column(Float, nullable=False, default=1.0)
    processing_time = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    frame_flags = relationship(
        "VideoFrameFlag",
        back_populates="video_log",
        cascade="all, delete-orphan",
        order_by="VideoFrameFlag.timestamp_seconds",
    )
    user = relationship("User", back_populates="video_moderation_logs")


class VideoFrameFlag(Base):
    __tablename__ = "video_frame_flags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_log_id = Column(
        UUID(as_uuid=True),
        ForeignKey("video_moderation_logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    timestamp_seconds = Column(Float, nullable=False)
    frame_index = Column(Integer, nullable=False)
    flag_category = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    decision = Column(String(50), nullable=False, default="unsafe")
    detected_labels = Column(JSON_TYPE, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    video_log = relationship("VideoModerationLog", back_populates="frame_flags")
