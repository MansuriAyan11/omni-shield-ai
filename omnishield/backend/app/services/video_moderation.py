"""
Asynchronous video moderation pipeline.

Samples frames at 1 FPS using OpenCV, converts BGR -> RGB, persists sampled frames to a
transient secure temp directory, and runs the multi-model image moderation engine concurrently
via asyncio.gather with thread-pool orchestration.
"""

import asyncio
import time
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import cv2
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.repositories.video_log_repo import VideoLogRepository
from app.services.multi_model_moderation import moderate_image_result_dict_async

RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _highest_risk(current: str, candidate: str) -> str:
    if RISK_ORDER.get(candidate, 0) > RISK_ORDER.get(current, 0):
        return candidate
    return current


def _extract_frame_flags(
    frame_result: Dict[str, Any],
    timestamp_seconds: float,
    frame_index: int,
) -> List[Dict[str, Any]]:
    flags: List[Dict[str, Any]] = []
    categories = frame_result.get("categories", {})

    for flag_category, category_result in categories.items():
        if category_result.get("status") != "unsafe":
            continue

        flags.append(
            {
                "timestamp_seconds": round(timestamp_seconds, 3),
                "frame_index": frame_index,
                "flag_category": flag_category,
                "confidence": float(category_result.get("confidence", 0.0)),
                "decision": "unsafe",
                "detected_labels": category_result.get("detected_labels", []),
            }
        )

    if not flags and frame_result.get("status") == "unsafe":
        flags.append(
            {
                "timestamp_seconds": round(timestamp_seconds, 3),
                "frame_index": frame_index,
                "flag_category": "aggregate",
                "confidence": float(frame_result.get("confidence", 0.0)),
                "decision": "unsafe",
                "detected_labels": frame_result.get("detected_labels", []),
            }
        )

    return flags


async def _moderate_single_frame(
    frame_path: Path,
    timestamp_seconds: float,
    frame_index: int,
) -> Tuple[float, int, Dict[str, Any]]:
    """Run multi-model moderation on a single sampled frame."""
    frame_result = await moderate_image_result_dict_async(
        str(frame_path),
        enable_nsfw=settings.ENABLE_NSFW_DETECTION,
        enable_violence=settings.ENABLE_VIOLENCE_DETECTION,
        enable_weapons=settings.ENABLE_WEAPON_DETECTION,
        enable_faces=settings.ENABLE_FACE_DETECTION,
        enable_text=settings.ENABLE_TEXT_MODERATION,
    )
    return timestamp_seconds, frame_index, frame_result


async def process_video_file_async(
    db: AsyncSession,
    video_log_id: UUID,
    file_path: str,
    frame_interval_seconds: Optional[float] = None,
) -> None:
    """
    Process a video file asynchronously using an async DB session.

    Extracts exactly one frame per second of video duration, converts each frame from BGR to
    RGB, runs the comprehensive multi-model image moderation engine concurrently, aggregates
    violations, and persists frame flags and summary telemetry to the database.
    """
    interval = frame_interval_seconds or settings.VIDEO_FRAME_INTERVAL_SECONDS
    path = Path(file_path)
    start_time = time.time()
    frames_sampled = 0
    all_flags: List[Dict[str, Any]] = []

    aggregate_overall_status = "safe"
    aggregate_overall_confidence = 0.0
    aggregate_risk = "low"
    aggregate_action = "allow"
    aggregate_reason = "No policy violations detected across sampled frames"
    max_confidence = 0.0

    await VideoLogRepository.mark_processing(db, video_log_id)

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        await VideoLogRepository.fail_log(db, video_log_id, "Unable to open video file for processing.")
        return

    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        total_duration = (total_frames / fps) if total_frames > 0 and fps > 0 else None

        # Enforce exactly 1 frame per second of duration.
        frame_step = max(1, int(round(fps * interval)))
        frame_index = 0
        moderation_tasks: List[asyncio.Task[Tuple[float, int, Dict[str, Any]]]] = []

        with tempfile.TemporaryDirectory(prefix="video_frame_") as temp_dir:
            temp_dir_path = Path(temp_dir)

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_index += 1
                if frame_index % frame_step != 0:
                    continue

                frames_sampled += 1
                timestamp_seconds = (frame_index - 1) / fps

                # Convert OpenCV BGR frame to RGB colorspace.
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                frame_path = temp_dir_path / f"frame_{frame_index}.jpg"
                if not cv2.imwrite(str(frame_path), rgb_frame):
                    logger.warning(f"Failed to write frame {frame_index} for video {video_log_id}")
                    continue

                # Queue frame for concurrent multi-model moderation.
                moderation_tasks.append(
                    asyncio.create_task(
                        _moderate_single_frame(frame_path, timestamp_seconds, frame_index)
                    )
                )

            # Run all frame moderation tasks concurrently via asyncio.gather.
            logger.info(f"Launching {len(moderation_tasks)} concurrent frame moderation tasks for video {video_log_id}")
            completed_results = await asyncio.gather(*moderation_tasks, return_exceptions=True)

            for result in completed_results:
                if isinstance(result, Exception):
                    logger.error(f"Frame moderation task failed: {result}")
                    continue

                timestamp_seconds, frame_index, frame_result = result

                if frame_result.get("status") == "error":
                    logger.warning(
                        f"Frame moderation error at {timestamp_seconds:.2f}s: "
                        f"{frame_result.get('reason')}"
                    )
                    continue

                frame_flags = _extract_frame_flags(frame_result, timestamp_seconds, frame_index)
                if frame_flags:
                    all_flags.extend(frame_flags)
                    aggregate_overall_status = "unsafe"
                    max_confidence = max(
                        max_confidence,
                        float(frame_result.get("confidence", 0.0)),
                        max(flag["confidence"] for flag in frame_flags),
                    )
                    aggregate_risk = _highest_risk(
                        aggregate_risk,
                        frame_result.get("risk_level", "medium"),
                    )
                    aggregate_action = frame_result.get("recommended_action", "block")
                    aggregate_reason = (
                        f"Unsafe content detected at {frame_flags[0]['timestamp_seconds']:.2f}s"
                    )

        if all_flags:
            await VideoLogRepository.add_frame_flags(db, video_log_id, all_flags)

        if aggregate_overall_status == "safe" and frames_sampled > 0:
            aggregate_overall_confidence = 0.95
        elif aggregate_overall_status == "unsafe":
            aggregate_overall_confidence = max_confidence

        processing_time = round(time.time() - start_time, 4)
        await VideoLogRepository.complete_log(
            db,
            video_log_id,
            total_duration=total_duration,
            overall_status=aggregate_overall_status,
            risk_level=aggregate_risk,
            overall_confidence=round(aggregate_overall_confidence, 4),
            recommended_action=aggregate_action,
            reason=aggregate_reason,
            frames_sampled=frames_sampled,
            frames_flagged=len(all_flags),
            processing_time=processing_time,
        )

        logger.info(
            f"Video moderation complete [{video_log_id}]: "
            f"{aggregate_overall_status} ({frames_sampled} frames sampled, "
            f"{len(all_flags)} flags) in {processing_time:.2f}s"
        )
    except Exception as exc:
        logger.exception(f"Video moderation failed for {video_log_id}: {exc}")
        await VideoLogRepository.fail_log(db, video_log_id, str(exc))
    finally:
        cap.release()
        if path.exists():
            try:
                path.unlink()
            except OSError as cleanup_error:
                logger.error(f"Failed to delete video temp file {path}: {cleanup_error}")


async def run_video_moderation_job(
    video_log_id: str,
    file_path: str,
    frame_interval_seconds: float,
) -> None:
    """Background task entrypoint using an async DB session."""
    async with AsyncSessionLocal() as db:
        try:
            await process_video_file_async(
                db,
                UUID(video_log_id),
                file_path,
                frame_interval_seconds=frame_interval_seconds,
            )
        finally:
            await db.close()
