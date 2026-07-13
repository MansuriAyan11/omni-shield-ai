import time
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image
from loguru import logger

from app.core.config import settings

# Global lazy-initialized NudeDetector
_detector = None

def get_detector():
    """Lazy-load NudeDetector to prevent slow imports during startup/testing."""
    global _detector
    if _detector is None:
        logger.info("Initializing NudeNet NudeDetector model...")
        from nudenet import NudeDetector
        _detector = NudeDetector()
        logger.info("NudeNet NudeDetector model initialized successfully.")
    return _detector


UNSAFE_LABELS = {
    "FEMALE_BREAST_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "MALE_GENITALIA_COVERED",
    "FEMALE_GENITALIA_EXPOSED",
    "BUTTOCKS_EXPOSED",
    "ANUS_EXPOSED"
}

LABEL_THRESHOLDS = {
    "MALE_GENITALIA_EXPOSED": 0.25,   # Highest priority - never miss
    "MALE_GENITALIA_COVERED": 0.40,   # Borderline male genitalia covered
    "FEMALE_GENITALIA_EXPOSED": 0.25, # Highest priority
    "ANUS_EXPOSED": 0.35,             # Highest priority
    "FEMALE_BREAST_EXPOSED": 0.45,    # Medium priority
    "BUTTOCKS_EXPOSED": 0.45,         # Medium priority
}


def is_closeup(image_path: str) -> bool:
    """Helper to check if the image is a close-up based on dimension aspect-ratio/size."""
    try:
        with Image.open(image_path) as img:
            w, h = img.size
            aspect_ratio = w / h
            is_square_crop = 0.75 <= aspect_ratio <= 1.35
            is_small = (w * h) < (800 * 800)
            return is_square_crop or is_small
    except Exception as e:
        logger.warning(f"Error checking if image is close-up: {e}")
        return False


def create_padded_version(image_path: str, pad_percent: float = 0.4) -> str:
    """Helper to pad close-up images to help NudeNet detect contextual features."""
    with Image.open(image_path) as img:
        img_rgb = img.convert("RGB")
        w, h = img_rgb.size
        pad_x = int(w * pad_percent)
        pad_y = int(h * pad_percent)
        new_w = w + 2 * pad_x
        new_h = h + 2 * pad_y
        padded = Image.new("RGB", (new_w, new_h), (255, 255, 255))
        padded.paste(img_rgb, (pad_x, pad_y))
        suffix = Path(image_path).suffix
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="padded_")
        padded.save(tmp.name)
        tmp.close()
        return tmp.name


def apply_fallback_rules(detections: List[Dict[str, Any]], is_closeup_image: bool) -> Optional[Dict[str, Any]]:
    """Heuristic fallback rules from the original NudeNet integration."""
    labels_found = {item.get("class") for item in detections}
    scores = {item.get("class"): item.get("score", 0) for item in detections}

    has_belly = "BELLY_EXPOSED" in labels_found
    has_face_male = "FACE_MALE" in labels_found
    has_face_female = "FACE_FEMALE" in labels_found
    has_face = has_face_male or has_face_female

    safe_labels = {
        "MALE_GENITALIA_COVERED",
        "FEMALE_GENITALIA_COVERED",
        "MALE_BREAST_COVERED",
        "FEMALE_BREAST_COVERED"
    }
    has_safe_context = bool(labels_found & safe_labels)

    belly_score = scores.get("BELLY_EXPOSED", 0)

    # Rule 1: close-up belly with no face
    if is_closeup_image and has_belly and not has_face and belly_score >= 0.65:
        logger.info("[FALLBACK] Rule 1 matched: close-up belly with no face")
        return {
            "status": "unsafe",
            "confidence": round(belly_score, 4),
            "detected_labels": ["MALE_GENITALIA_COVERED_INFERRED"],
            "bounding_boxes": [],
            "reason": "Close-up exposed lower torso indicating potential nudity."
        }

    # Rule 2: face + belly + no clothing context
    if has_face and has_belly and not has_safe_context and belly_score >= 0.30:
        logger.info(f"[FALLBACK] Rule 2 matched: face + belly + no clothing context (BELLY_EXPOSED score: {belly_score:.4f})")
        return {
            "status": "unsafe",
            "confidence": round(belly_score, 4),
            "detected_labels": ["MALE_GENITALIA_EXPOSED_INFERRED"],
            "bounding_boxes": [],
            "reason": "Exposed body with lack of clothing context."
        }

    return None


def determine_metadata(status: str, detected_labels: List[str], confidence: float) -> tuple[str, str, str]:
    """Map detected categories and scores to Enterprise Risk Levels, Recommended Actions and Reasons."""
    if status == "safe":
        return "low", "allow", "No inappropriate content detected."
    
    # Check for critical explicit content
    critical_labels = {"MALE_GENITALIA_EXPOSED", "FEMALE_GENITALIA_EXPOSED", "ANUS_EXPOSED"}
    high_labels = {"FEMALE_BREAST_EXPOSED", "BUTTOCKS_EXPOSED", "MALE_GENITALIA_COVERED"}
    
    matched_labels = set(detected_labels)
    
    if matched_labels & critical_labels:
        risk_level = "critical"
        recommended_action = "block"
        reason = "Exposed explicit genitalia or anus anatomy detected."
    elif matched_labels & high_labels:
        risk_level = "high"
        recommended_action = "block" if confidence >= 0.60 else "quarantine"
        reason = "Exposed sexual anatomy (breasts or buttocks) detected."
    else:
        risk_level = "medium"
        recommended_action = "quarantine"
        reason = "Potential or inferred nudity detected by heuristic filters."
        
    return risk_level, recommended_action, reason


def moderate_image_file(image_path: str) -> Dict[str, Any]:
    """
    Main entrypoint for image moderation. 
    Runs NudeNet detection, handles aspect-ratio padding on close-ups, 
    merges detections, applies fallbacks, and maps to enterprise metadata.
    """
    start_time = time.time()
    path = Path(image_path)

    if not path.exists():
        return {
            "status": "error",
            "message": f"Image file not found at path: {image_path}",
            "processing_time": round(time.time() - start_time, 4)
        }

    try:
        detector = get_detector()
        raw_detections = detector.detect(str(path))
        
        detected_labels = []
        bounding_boxes = []
        highest_confidence = 0.0

        # Process raw detections
        for item in raw_detections:
            label = item.get("class")
            confidence = item.get("score", 0)
            box = item.get("box", [])

            if label in UNSAFE_LABELS:
                threshold = LABEL_THRESHOLDS.get(label, settings.DEFAULT_THRESHOLD)
                if confidence >= threshold:
                    detected_labels.append(label)
                    highest_confidence = max(highest_confidence, confidence)
                    # Convert box coordinates to integers for Pydantic schema
                    box_coords = [int(coord) for coord in box] if box else []
                    bounding_boxes.append({
                        "label": label,
                        "box": box_coords,
                        "score": round(confidence, 4)
                    })

        closeup = is_closeup(image_path)
        
        # If safe but is a closeup, run padded version to be sure
        if not detected_labels and closeup:
            logger.info(f"Close-up image detected ({path.name}) - running padded detection check.")
            padded_path = None
            try:
                padded_path = create_padded_version(image_path)
                padded_detections = detector.detect(padded_path)
                
                for item in padded_detections:
                    label = item.get("class")
                    confidence = item.get("score", 0)
                    box = item.get("box", [])
                    
                    if label in UNSAFE_LABELS:
                        threshold = LABEL_THRESHOLDS.get(label, settings.DEFAULT_THRESHOLD)
                        if confidence >= threshold:
                            if label not in detected_labels:
                                detected_labels.append(label)
                            highest_confidence = max(highest_confidence, confidence)
                            # Convert box coordinates to integers
                            box_coords = [int(coord) for coord in box] if box else []
                            # Bounding box is relative to padded image, so we add it but note it's padded
                            bounding_boxes.append({
                                "label": f"{label}_PADDED",
                                "box": box_coords,
                                "score": round(confidence, 4)
                            })
            except Exception as e:
                logger.error(f"Padded detection run failed: {e}")
            finally:
                if padded_path and os.path.exists(padded_path):
                    try:
                        os.remove(padded_path)
                    except Exception:
                        pass

        # If still safe, check custom fallback rules
        if not detected_labels:
            fallback = apply_fallback_rules(raw_detections, closeup)
            if fallback:
                status = "unsafe"
                detected_labels = fallback["detected_labels"]
                highest_confidence = fallback["confidence"]
                reason = fallback["reason"]
                risk_level, recommended_action, _ = determine_metadata(status, detected_labels, highest_confidence)
                
                return {
                    "status": "unsafe",
                    "confidence": highest_confidence,
                    "detected_labels": detected_labels,
                    "bounding_boxes": [],
                    "processing_time": round(time.time() - start_time, 4),
                    "risk_level": risk_level,
                    "recommended_action": recommended_action,
                    "reason": reason
                }

        # Format final decision
        status = "unsafe" if detected_labels else "safe"
        confidence = highest_confidence if status == "unsafe" else round(1.0 - highest_confidence, 4)
        
        risk_level, recommended_action, reason = determine_metadata(status, detected_labels, confidence)
        processing_time = round(time.time() - start_time, 4)

        return {
            "status": status,
            "confidence": round(confidence, 4),
            "detected_labels": detected_labels,
            "bounding_boxes": bounding_boxes,
            "processing_time": processing_time,
            "risk_level": risk_level,
            "recommended_action": recommended_action,
            "reason": reason
        }

    except Exception as e:
        logger.exception(f"Unexpected error during image moderation run: {e}")
        return {
            "status": "error",
            "message": str(e),
            "processing_time": round(time.time() - start_time, 4)
        }
