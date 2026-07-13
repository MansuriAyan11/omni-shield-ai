from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.video_log import VideoFrameFlag, VideoModerationLog


class VideoLogRepository:
    @staticmethod
    async def create_pending_log(
        db: AsyncSession,
        user_id: Optional[UUID],
        filename: str,
        frame_interval_seconds: float,
    ) -> VideoModerationLog:
        log = VideoModerationLog(
            user_id=user_id,
            filename=filename,
            status="pending",
            frame_interval_seconds=frame_interval_seconds,
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        log_id: UUID,
        *,
        include_flags: bool = False,
    ) -> Optional[VideoModerationLog]:
        query = select(VideoModerationLog).where(VideoModerationLog.id == log_id)
        if include_flags:
            query = query.options(selectinload(VideoModerationLog.frame_flags))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def mark_processing(db: AsyncSession, log_id: UUID) -> None:
        log = await db.get(VideoModerationLog, log_id)
        if not log:
            return
        log.status = "processing"
        await db.commit()

    @staticmethod
    async def add_frame_flags(
        db: AsyncSession,
        log_id: UUID,
        flags: List[Dict[str, Any]],
    ) -> None:
        for flag in flags:
            db.add(
                VideoFrameFlag(
                    video_log_id=log_id,
                    timestamp_seconds=flag["timestamp_seconds"],
                    frame_index=flag["frame_index"],
                    flag_category=flag["flag_category"],
                    confidence=flag["confidence"],
                    decision=flag.get("decision", "unsafe"),
                    detected_labels=flag.get("detected_labels", []),
                )
            )
        await db.commit()

    @staticmethod
    async def complete_log(
        db: AsyncSession,
        log_id: UUID,
        *,
        total_duration: Optional[float],
        overall_status: str,
        risk_level: str,
        overall_confidence: float,
        recommended_action: str,
        reason: str,
        frames_sampled: int,
        frames_flagged: int,
        processing_time: float,
    ) -> None:
        log = await db.get(VideoModerationLog, log_id)
        if not log:
            return

        log.status = "completed"
        log.total_duration = total_duration
        log.overall_status = overall_status
        log.risk_level = risk_level
        log.confidence = overall_confidence
        log.recommended_action = recommended_action
        log.reason = reason
        log.frames_sampled = frames_sampled
        log.frames_flagged = frames_flagged
        log.processing_time = processing_time
        log.completed_at = datetime.now(timezone.utc)
        log.error_message = None
        await db.commit()

    @staticmethod
    async def fail_log(db: AsyncSession, log_id: UUID, error_message: str) -> None:
        log = await db.get(VideoModerationLog, log_id)
        if not log:
            return

        log.status = "failed"
        log.error_message = error_message
        log.completed_at = datetime.now(timezone.utc)
        await db.commit()
