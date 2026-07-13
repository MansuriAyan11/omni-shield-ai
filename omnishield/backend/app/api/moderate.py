import os
import shutil
import uuid
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_client
from app.models.user import User
from app.services.ai_moderation import moderate_image_file
from app.services.multi_model_moderation import moderate_image_result_dict_async
from app.services.hash_cache import image_cache
from app.repositories.log_repo import ModerationLogRepository
from app.repositories.video_log_repo import VideoLogRepository
from app.schemas.moderate import ModerationResponse, BatchTaskResponse
from app.schemas.video import VideoModerationJobResponse, VideoModerationStatusResponse
from app.services.video_moderation import run_video_moderation_job

router = APIRouter(prefix="/moderate", tags=["Moderation"])

# Directory to save uploads temporarily
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(exist_ok=True)
VIDEO_UPLOAD_DIR = Path(settings.VIDEO_UPLOAD_DIR)
VIDEO_UPLOAD_DIR.mkdir(exist_ok=True)


def validate_image_header(file_chunk: bytes) -> bool:
    """Secure check of image magic numbers to prevent extension spoofing."""
    if file_chunk.startswith(b"\xff\xd8\xff"): # JPEG
        return True
    if file_chunk.startswith(b"\x89PNG\r\n\x1a\n"): # PNG
        return True
    if file_chunk.startswith(b"RIFF") and b"WEBP" in file_chunk[8:16]: # WebP
        return True
    return False


def validate_video_header(file_chunk: bytes) -> bool:
    """Secure check of common video container signatures."""
    if len(file_chunk) < 12:
        return False

    # WebM / Matroska (EBML)
    if file_chunk.startswith(b"\x1a\x45\xdf\xa3"):
        return True

    # AVI (RIFF....AVI)
    if file_chunk.startswith(b"RIFF") and file_chunk[8:12] == b"AVI ":
        return True

    # MP4 / MOV (....ftyp)
    if file_chunk[4:8] == b"ftyp":
        return True

    return False


def _serialize_video_status(log) -> dict:
    return {
        "job_id": log.id,
        "filename": log.filename,
        "status": log.status,
        "overall_status": log.overall_status,
        "risk_level": log.risk_level,
        "overall_confidence": log.confidence,
        "recommended_action": log.recommended_action,
        "reason": log.reason,
        "total_duration": log.total_duration,
        "frames_sampled": log.frames_sampled,
        "frames_flagged": log.frames_flagged,
        "frame_interval_seconds": log.frame_interval_seconds,
        "processing_time": log.processing_time,
        "error_message": log.error_message,
        "created_at": log.created_at,
        "completed_at": log.completed_at,
        "frame_flags": log.frame_flags if hasattr(log, "frame_flags") else [],
    }


@router.post("/video", response_model=VideoModerationJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def moderate_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    frame_interval_seconds: Optional[float] = None,
    current_user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """
    Queue a video for asynchronous multi-model moderation.

    Saves the upload temporarily, creates a pending job record, and returns a job token
    immediately while frame extraction and moderation run in a background task.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File has no name.",
        )

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported video extension {file_ext}. "
                f"Allowed: {sorted(settings.ALLOWED_VIDEO_EXTENSIONS)}"
            ),
        )

    interval = frame_interval_seconds or settings.VIDEO_FRAME_INTERVAL_SECONDS
    if interval <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="frame_interval_seconds must be greater than 0.",
        )

    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = VIDEO_UPLOAD_DIR / unique_filename

    try:
        first_chunk = await file.read(4096)
        if not validate_video_header(first_chunk):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is not a valid MP4, MOV, AVI, WebM, or MKV video.",
            )

        await file.seek(0)
        file_size = 0
        max_bytes = settings.MAX_VIDEO_SIZE_MB * 1024 * 1024

        with open(file_path, "wb") as buffer:
            while chunk := await file.read(8192):
                file_size += len(chunk)
                if file_size > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Video exceeds maximum size of {settings.MAX_VIDEO_SIZE_MB}MB.",
                    )
                buffer.write(chunk)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded video file is empty.",
            )

        video_log = await VideoLogRepository.create_pending_log(
            db=db,
            user_id=current_user.id,
            filename=file.filename,
            frame_interval_seconds=interval,
        )

        background_tasks.add_task(
            run_video_moderation_job,
            str(video_log.id),
            str(file_path),
            interval,
        )

        status_url = f"{settings.API_V1_STR}/moderate/video/{video_log.id}"
        return {
            "job_id": video_log.id,
            "status": video_log.status,
            "filename": file.filename,
            "message": "Video moderation job queued. Poll status_url for progress and results.",
            "status_url": status_url,
        }
    except HTTPException:
        if file_path.exists():
            file_path.unlink(missing_ok=True)
        raise
    except Exception as e:
        if file_path.exists():
            file_path.unlink(missing_ok=True)
        logger.exception(f"Failed to queue video moderation job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue video moderation job: {e}",
        )
    finally:
        await file.close()


@router.get("/video/{job_id}", response_model=VideoModerationStatusResponse)
async def get_video_moderation_status(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Poll the status and aggregated results of a queued video moderation job."""
    video_log = await VideoLogRepository.get_by_id(
        db,
        job_id,
        include_flags=True,
    )

    if not video_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video moderation job not found.",
        )

    if video_log.user_id and video_log.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this video moderation job.",
        )

    return {
        "success": True,
        "message": "Video moderation status retrieved successfully.",
        "data": _serialize_video_status(video_log),
    }


@router.post("/image", response_model=ModerationResponse)
async def moderate_single_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Moderate a single uploaded image.
    Validates type/size, checks cache, runs NudeNet model on cache miss, and logs transaction.
    """
    file_path = None
    
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File has no name."
        )

    # 1. Check file extensions
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension {file_ext}. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )

    # 2. Setup unique local temporary path
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename

    try:
        # 3. Read first chunk and validate MIME type via magic bytes
        first_chunk = await file.read(2048)
        if not validate_image_header(first_chunk):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Spoofed file signature. Uploaded file is not a valid JPEG, PNG, or WebP image."
            )

        # Reset read pointer and copy to temp file, validating file size constraints
        await file.seek(0)
        file_size = 0
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(8192):
                file_size += len(chunk)
                if file_size > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB."
                    )
                buffer.write(chunk)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty."
            )

        # 4. Check cache by SHA256 of temporary file
        cached_result = image_cache.get(str(file_path))
        if cached_result:
            # Reconstruct DB log from cached result
            db_log = await ModerationLogRepository.create_log(
                db=db,
                user_id=current_user.id,
                image_hash=image_cache.calculate_sha256(str(file_path)),
                file_name=file.filename,
                decision=cached_result["status"],
                risk_level=cached_result["risk_level"],
                confidence=cached_result["confidence"],
                detected_labels=cached_result["detected_labels"],
                bounding_boxes=cached_result["bounding_boxes"],
                processing_time=cached_result["processing_time"],
                recommended_action=cached_result["recommended_action"],
                reason=cached_result["reason"]
            )
            
            return {
                "success": True,
                "message": "Moderation result retrieved from cache.",
                "data": {
                    "decision": cached_result["status"],
                    "risk_level": cached_result["risk_level"],
                    "confidence": cached_result["confidence"],
                    "detected_labels": cached_result["detected_labels"],
                    "bounding_boxes": cached_result["bounding_boxes"],
                    "processing_time": cached_result["processing_time"],
                    "recommended_action": cached_result["recommended_action"],
                    "reason": cached_result["reason"],
                    "cached": True
                }
            }

        # 5. Run Real-time NudeNet model detection
        result = moderate_image_file(str(file_path))
        if result.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Inference pipeline error: {result.get('message')}"
            )

        # 6. Save results to cache (for future uploads)
        image_hash = image_cache.calculate_sha256(str(file_path))
        image_cache.set(str(file_path), result)

        # 7. Persist transaction to DB
        db_log = await ModerationLogRepository.create_log(
            db=db,
            user_id=current_user.id,
            image_hash=image_hash,
            file_name=file.filename,
            decision=result["status"],
            risk_level=result["risk_level"],
            confidence=result["confidence"],
            detected_labels=result["detected_labels"],
            bounding_boxes=result["bounding_boxes"],
            processing_time=result["processing_time"],
            recommended_action=result["recommended_action"],
            reason=result["reason"]
        )

        return {
            "success": True,
            "message": "Image moderated successfully.",
            "data": {
                "decision": result["status"],
                "risk_level": result["risk_level"],
                "confidence": result["confidence"],
                "detected_labels": result["detected_labels"],
                "bounding_boxes": result["bounding_boxes"],
                "processing_time": result["processing_time"],
                "recommended_action": result["recommended_action"],
                "reason": result["reason"],
                "cached": False
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error moderating file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}"
        )
    finally:
        await file.close()
        # Clean up local temporary file
        if file_path and file_path.exists():
            try:
                file_path.unlink()
            except Exception as cleanup_error:
                logger.error(f"Failed to delete temp file {file_path}: {cleanup_error}")


@router.post("/batch", response_model=BatchTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def moderate_batch_images(
    urls: List[str],
    current_user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Moderates a batch of image URLs asynchronously.
    Returns a Celery task ID that the client can query.
    """
    if not urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="List of URLs cannot be empty."
        )

    try:
        from app.core.celery_app import celery_app
        # Trigger Celery Task
        task = celery_app.send_task(
            "app.tasks.moderate_batch",
            args=[str(current_user.id), urls]
        )
        
        return {
            "task_id": task.id,
            "status": "PENDING",
            "total_images": len(urls),
            "message": "Batch moderation queued. Query task endpoint for status."
        }
    except Exception as e:
        logger.error(f"Failed to queue batch job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch queueing failed: {e}"
        )


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_client)
):
    """Query the status and results of an asynchronous batch task."""
    try:
        from celery.result import AsyncResult
        res = AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": res.status,
            "result": None
        }
        
        if res.ready():
            response["result"] = res.result
            
        return response
    except Exception as e:
        logger.error(f"Error querying task status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query task status: {e}"
        )


@router.post("/image/comprehensive", response_model=ModerationResponse)
async def moderate_single_image_comprehensive(
    file: UploadFile = File(...),
    enable_nsfw: bool = True,
    enable_violence: bool = True,
    enable_weapons: bool = True,
    enable_faces: bool = True,
    enable_text: bool = True,
    current_user: User = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Comprehensive multi-model image moderation.
    
    Runs all available AI models:
    - NSFW Detection (NudeNet)
    - Violence Detection (CLIP)
    - Weapon Detection (YOLOv8)
    - Face Detection (MTCNN)
    - Text Moderation (PaddleOCR + Profanity)
    
    Query params allow enabling/disabling specific models.
    """
    file_path = None
    
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File has no name."
        )

    # 1. Check file extensions
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension {file_ext}. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )

    # 2. Setup unique local temporary path
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename

    try:
        # 3. Read first chunk and validate MIME type via magic bytes
        first_chunk = await file.read(2048)
        if not validate_image_header(first_chunk):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Spoofed file signature. Uploaded file is not a valid JPEG, PNG, or WebP image."
            )

        # Reset read pointer and copy to temp file
        await file.seek(0)
        file_size = 0
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(8192):
                file_size += len(chunk)
                if file_size > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB."
                    )
                buffer.write(chunk)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty."
            )

        # 4. Check cache (using comprehensive key)
        cache_key_suffix = f"_comprehensive_{enable_nsfw}_{enable_violence}_{enable_weapons}_{enable_faces}_{enable_text}"
        image_hash = image_cache.calculate_sha256(str(file_path))
        comprehensive_cache_key = f"{image_hash}{cache_key_suffix}"
        
        # Note: For simplicity, we're not caching comprehensive results yet
        # Can be added later with more sophisticated cache key strategy
        
        # 5. Run comprehensive multi-model detection (async with parallel execution)
        result = await moderate_image_result_dict_async(
            str(file_path),
            enable_nsfw=enable_nsfw,
            enable_violence=enable_violence,
            enable_weapons=enable_weapons,
            enable_faces=enable_faces,
            enable_text=enable_text
        )
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Inference pipeline error: {result.get('reason')}"
            )

        # 6. Extract additional metadata from comprehensive result
        categories = result.get("categories", {})
        model_versions = result.get("model_versions", {})
        
        # Face count
        face_count = categories.get("faces", {}).get("face_count", 0)
        
        # Text moderation results
        text_result = categories.get("text", {})
        detected_text = text_result.get("detected_text", "")
        contains_profanity = "yes" if text_result.get("contains_profanity") else "no"

        # 7. Persist comprehensive transaction to DB
        db_log = await ModerationLogRepository.create_log(
            db=db,
            user_id=current_user.id,
            image_hash=image_hash,
            file_name=file.filename,
            decision=result["status"],
            risk_level=result["risk_level"],
            confidence=result["confidence"],
            detected_labels=result["detected_labels"],
            bounding_boxes=result["bounding_boxes"],
            processing_time=result["processing_time"],
            recommended_action=result["recommended_action"],
            reason=result["reason"],
            # Enhanced fields
            model_results=categories,
            model_versions=model_versions,
            face_count=face_count,
            detected_text=detected_text if detected_text else None,
            contains_profanity=contains_profanity if detected_text else None
        )

        return {
            "success": True,
            "message": "Comprehensive moderation completed successfully.",
            "data": {
                "decision": result["status"],
                "risk_level": result["risk_level"],
                "confidence": result["confidence"],
                "detected_labels": result["detected_labels"],
                "bounding_boxes": result["bounding_boxes"],
                "processing_time": result["processing_time"],
                "recommended_action": result["recommended_action"],
                "reason": result["reason"],
                "cached": False,
                # Enhanced data
                "categories": categories,
                "model_versions": model_versions,
                "face_count": face_count,
                "detected_text": detected_text,
                "contains_profanity": contains_profanity
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in comprehensive moderation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}"
        )
    finally:
        await file.close()
        # Clean up local temporary file
        if file_path and file_path.exists():
            try:
                file_path.unlink()
            except Exception as cleanup_error:
                logger.error(f"Failed to delete temp file {file_path}: {cleanup_error}")
