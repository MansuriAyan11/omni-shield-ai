from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, cast, Date

from app.models.log import ModerationLog

class ModerationLogRepository:
    @staticmethod
    async def create_log(
        db: AsyncSession,
        user_id: Optional[str],
        image_hash: str,
        file_name: str,
        decision: str,
        risk_level: str,
        confidence: float,
        detected_labels: List[str],
        bounding_boxes: List[Dict[str, Any]],
        processing_time: float,
        recommended_action: str,
        reason: Optional[str] = None,
        file_url: Optional[str] = None,
        # Enhanced multi-model fields
        model_results: Optional[Dict[str, Any]] = None,
        model_versions: Optional[Dict[str, str]] = None,
        face_count: Optional[int] = None,
        detected_text: Optional[str] = None,
        contains_profanity: Optional[str] = None
    ) -> ModerationLog:
        """Log a moderation scan entry to the database."""
        from uuid import UUID
        user_uuid = UUID(user_id) if user_id and isinstance(user_id, str) else user_id
        
        db_log = ModerationLog(
            user_id=user_uuid,
            image_hash=image_hash,
            file_name=file_name,
            file_url=file_url,
            decision=decision,
            risk_level=risk_level,
            confidence=confidence,
            detected_labels=detected_labels,
            bounding_boxes=bounding_boxes,
            processing_time=processing_time,
            recommended_action=recommended_action,
            reason=reason,
            # Enhanced fields
            model_results=model_results,
            model_versions=model_versions,
            face_count=face_count if face_count is not None else 0,
            detected_text=detected_text,
            contains_profanity=contains_profanity
        )
        db.add(db_log)
        await db.commit()
        await db.refresh(db_log)
        return db_log

    @staticmethod
    async def get_by_id(db: AsyncSession, log_id: str) -> Optional[ModerationLog]:
        """Retrieve a specific moderation log by ID."""
        from uuid import UUID
        log_uuid = UUID(log_id) if isinstance(log_id, str) else log_id
        result = await db.execute(select(ModerationLog).where(ModerationLog.id == log_uuid))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_logs(
        db: AsyncSession,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ModerationLog]:
        """Fetch moderation logs with optional user filtering and pagination."""
        from uuid import UUID
        query = select(ModerationLog)
        if user_id:
            user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
            query = query.where(ModerationLog.user_id == user_uuid)
        
        query = query.order_by(ModerationLog.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_stats(db: AsyncSession, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Aggregate high-level metrics for dashboard telemetry."""
        from uuid import UUID
        from app.models.key import APIKey
        from app.models.video_log import VideoModerationLog
        
        # Setup base queries
        total_query = select(func.count(ModerationLog.id))
        unsafe_query = select(func.count(ModerationLog.id)).where(ModerationLog.decision == "unsafe")
        safe_query = select(func.count(ModerationLog.id)).where(ModerationLog.decision == "safe")
        avg_time_query = select(func.avg(ModerationLog.processing_time))
        
        # Query for active API keys count
        active_keys_query = select(func.count(APIKey.id)).where(APIKey.status == "active")

        # Video moderation metrics
        total_videos_query = select(func.count(VideoModerationLog.id)).where(
            VideoModerationLog.status == "completed"
        )
        flagged_videos_query = select(func.count(VideoModerationLog.id)).where(
            VideoModerationLog.status == "completed",
            VideoModerationLog.overall_status == "unsafe",
        )
        # Avg scan latency = avg(processing_time / total_duration) for videos with duration > 0
        avg_video_latency_query = select(
            func.avg(VideoModerationLog.processing_time / VideoModerationLog.total_duration)
        ).where(
            VideoModerationLog.status == "completed",
            VideoModerationLog.total_duration.isnot(None),
            VideoModerationLog.total_duration > 0,
        )

        if user_id:
            user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
            total_query = total_query.where(ModerationLog.user_id == user_uuid)
            unsafe_query = unsafe_query.where(ModerationLog.user_id == user_uuid)
            safe_query = safe_query.where(ModerationLog.user_id == user_uuid)
            avg_time_query = avg_time_query.where(ModerationLog.user_id == user_uuid)
            active_keys_query = active_keys_query.where(APIKey.user_id == user_uuid)
            total_videos_query = total_videos_query.where(VideoModerationLog.user_id == user_uuid)
            flagged_videos_query = flagged_videos_query.where(VideoModerationLog.user_id == user_uuid)
            avg_video_latency_query = avg_video_latency_query.where(VideoModerationLog.user_id == user_uuid)

        # Run execute tasks
        total_count = (await db.execute(total_query)).scalar() or 0
        unsafe_count = (await db.execute(unsafe_query)).scalar() or 0
        safe_count = (await db.execute(safe_query)).scalar() or 0
        avg_time = (await db.execute(avg_time_query)).scalar() or 0.0
        active_keys_count = (await db.execute(active_keys_query)).scalar() or 0
        total_videos = (await db.execute(total_videos_query)).scalar() or 0
        flagged_videos = (await db.execute(flagged_videos_query)).scalar() or 0
        avg_video_latency = (await db.execute(avg_video_latency_query)).scalar() or 0.0

        # Run a query to group decisions by risk level
        risk_query = select(ModerationLog.risk_level, func.count(ModerationLog.id))
        if user_id:
            risk_query = risk_query.where(ModerationLog.user_id == user_uuid)
        risk_query = risk_query.group_by(ModerationLog.risk_level)
        risk_results = (await db.execute(risk_query)).all()
        risk_breakdown = {risk: count for risk, count in risk_results}

        return {
            "total_requests": total_count,
            "total_scans": total_count,
            "unsafe_count": unsafe_count,
            "unsafe_scans": unsafe_count,
            "safe_count": safe_count,
            "safe_scans": safe_count,
            "avg_processing_time": round(float(avg_time), 4),
            "risk_breakdown": risk_breakdown,
            "active_keys": active_keys_count,
            "total_videos": total_videos,
            "flagged_videos": flagged_videos,
            "avg_video_scan_latency": round(float(avg_video_latency), 4),
        }

    @staticmethod
    async def get_timeseries(
        db: AsyncSession, 
        user_id: Optional[str] = None,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get time series data for analytics charts."""
        from uuid import UUID
        from loguru import logger
        
        try:
            # Calculate the date range
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days - 1)
            
            # For SQLite, we need to use date() function instead of CAST
            # Get all logs within the date range
            query = select(ModerationLog).where(
                ModerationLog.created_at >= datetime.combine(start_date, datetime.min.time())
            )
            
            if user_id:
                user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
                query = query.where(ModerationLog.user_id == user_uuid)
            
            query = query.order_by(ModerationLog.created_at)
            
            result = await db.execute(query)
            logs = result.scalars().all()
            
            logger.info(f"� Found {len(logs)} logs in date range {start_date} to {end_date}")
            
            # Organize data by date in Python (instead of SQL)
            data_by_date = {}
            for log in logs:
                log_date = log.created_at.date()
                date_str = log_date.isoformat()
                
                if date_str not in data_by_date:
                    data_by_date[date_str] = {
                        "date": date_str,
                        "safe_count": 0,
                        "unsafe_count": 0,
                        "total_count": 0
                    }
                
                if log.decision == "safe":
                    data_by_date[date_str]["safe_count"] += 1
                elif log.decision == "unsafe":
                    data_by_date[date_str]["unsafe_count"] += 1
                
                data_by_date[date_str]["total_count"] += 1
            
            logger.info(f"📊 Grouped into {len(data_by_date)} unique dates")
            for date_str, data in data_by_date.items():
                logger.info(f"  {date_str}: safe={data['safe_count']}, unsafe={data['unsafe_count']}, total={data['total_count']}")
            
            # Fill in missing dates with zero counts
            all_dates = []
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.isoformat()
                if date_str not in data_by_date:
                    all_dates.append({
                        "date": date_str,
                        "safe_count": 0,
                        "unsafe_count": 0,
                        "total_count": 0
                    })
                else:
                    all_dates.append(data_by_date[date_str])
                current_date += timedelta(days=1)
            
            logger.info(f"📊 Returning {len(all_dates)} days of data")
            return all_dates
            
        except Exception as e:
            logger.error(f"❌ Error in get_timeseries: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Return empty data structure on error
            all_dates = []
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days - 1)
            current_date = start_date
            while current_date <= end_date:
                all_dates.append({
                    "date": current_date.isoformat(),
                    "safe_count": 0,
                    "unsafe_count": 0,
                    "total_count": 0
                })
                current_date += timedelta(days=1)
            return all_dates
