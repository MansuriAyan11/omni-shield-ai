import os
import uuid
import urllib.request
from typing import List, Dict, Any
from pathlib import Path
from loguru import logger

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.log import ModerationLog
from app.services.ai_moderation import moderate_image_file
from app.services.hash_cache import image_cache

@celery_app.task(name="app.tasks.moderate_batch")
def moderate_batch(user_id: str, urls: List[str]) -> List[Dict[str, Any]]:
    """
    Celery background task for batch URL moderation.
    Downloads, checks cache, running scans and persisting transactional logs.
    """
    logger.info(f"Celery Batch task started for user {user_id} with {len(urls)} URLs")
    results = []
    
    # Establish a synchronous DB session for the Celery worker process
    db = SessionLocal()
    
    upload_dir = Path("uploads_batch")
    upload_dir.mkdir(exist_ok=True)
    
    for url in urls:
        # Generate a unique temp file name for each remote download
        temp_file = upload_dir / f"batch_{uuid.uuid4().hex}.jpg"
        try:
            # 1. Download image bytes
            logger.info(f"Downloading remote image: {url}")
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ImageModerator/1.0'}
            )
            with urllib.request.urlopen(req, timeout=10.0) as response:
                with open(temp_file, 'wb') as f:
                    f.write(response.read())
            
            # 2. Check hash cache
            cached_result = image_cache.get(str(temp_file))
            if cached_result:
                logger.info(f"Batch URL cache hit for: {url}")
                results.append({
                    "url": url,
                    "success": True,
                    "cached": True,
                    "decision": cached_result["status"],
                    "risk_level": cached_result["risk_level"],
                    "confidence": cached_result["confidence"],
                    "detected_labels": cached_result["detected_labels"],
                    "bounding_boxes": cached_result["bounding_boxes"],
                    "recommended_action": cached_result["recommended_action"],
                    "reason": cached_result["reason"]
                })
                
                # Insert DB log entry using the sync session
                db_log = ModerationLog(
                    user_id=uuid.UUID(user_id),
                    image_hash=image_cache.calculate_sha256(str(temp_file)),
                    file_name=url.split("/")[-1].split("?")[0] or "batch_image.jpg",
                    file_url=url,
                    decision=cached_result["status"],
                    risk_level=cached_result["risk_level"],
                    confidence=cached_result["confidence"],
                    detected_labels=cached_result["detected_labels"],
                    bounding_boxes=cached_result["bounding_boxes"],
                    processing_time=cached_result["processing_time"],
                    recommended_action=cached_result["recommended_action"],
                    reason=cached_result["reason"]
                )
                db.add(db_log)
                db.commit()
                continue

            # 3. Model Inference on Cache Miss
            logger.info(f"Cache miss. Running moderation scan for: {url}")
            result = moderate_image_file(str(temp_file))
            if result.get("status") == "error":
                results.append({
                    "url": url,
                    "success": False,
                    "message": result.get("message")
                })
                continue
                
            # 4. Cache and Save to database
            image_hash = image_cache.calculate_sha256(str(temp_file))
            image_cache.set(str(temp_file), result)
            
            db_log = ModerationLog(
                user_id=uuid.UUID(user_id),
                image_hash=image_hash,
                file_name=url.split("/")[-1].split("?")[0] or "batch_image.jpg",
                file_url=url,
                decision=result["status"],
                risk_level=result["risk_level"],
                confidence=result["confidence"],
                detected_labels=result["detected_labels"],
                bounding_boxes=result["bounding_boxes"],
                processing_time=result["processing_time"],
                recommended_action=result["recommended_action"],
                reason=result["reason"]
            )
            db.add(db_log)
            db.commit()
            
            results.append({
                "url": url,
                "success": True,
                "cached": False,
                "decision": result["status"],
                "risk_level": result["risk_level"],
                "confidence": result["confidence"],
                "detected_labels": result["detected_labels"],
                "bounding_boxes": result["bounding_boxes"],
                "recommended_action": result["recommended_action"],
                "reason": result["reason"]
            })
            
        except Exception as e:
            logger.error(f"Failed to process batch URL '{url}': {e}")
            results.append({
                "url": url,
                "success": False,
                "message": f"Processing failed: {str(e)}"
            })
        finally:
            # Clean up temp file
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception as cleanup_error:
                    logger.error(f"Failed to delete temp batch file {temp_file}: {cleanup_error}")
                    
    db.close()
    logger.info(f"Celery Batch task completed. Processed {len(urls)} URLs")
    return results
