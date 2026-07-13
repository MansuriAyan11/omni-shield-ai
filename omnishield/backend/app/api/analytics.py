from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.repositories.log_repo import ModerationLogRepository

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch high-level metrics for dashboard telemetry charts."""
    try:
        # If admin, fetch global metrics; otherwise, fetch current user's metrics only
        user_filter = None if current_user.role == "admin" else current_user.id
        stats = await ModerationLogRepository.get_stats(db, user_filter)
        return stats
    except Exception as e:
        logger.error(f"Error fetching telemetry stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics stats"
        )


@router.get("/history")
async def get_scans_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve paginated scanning history for the dashboard audit tables."""
    try:
        user_filter = None if current_user.role == "admin" else current_user.id
        logs = await ModerationLogRepository.list_logs(db, user_filter, limit, offset)
        return logs
    except Exception as e:
        logger.error(f"Error listing moderation logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve logs history"
        )


@router.get("/timeseries")
async def get_timeseries_data(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve time series data for analytics charts."""
    try:
        user_filter = None if current_user.role == "admin" else current_user.id
        timeseries = await ModerationLogRepository.get_timeseries(db, user_filter, days)
        return timeseries
    except Exception as e:
        logger.error(f"Error fetching timeseries data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve timeseries data"
        )
