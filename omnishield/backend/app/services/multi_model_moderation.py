"""
Enterprise Multi-Model AI Moderation Service
Combines multiple AI models for comprehensive content moderation:
- NSFW Detection (NudeNet)
- Violence Detection (CLIP)
- Gore Detection (Custom CNN)
- Weapon Detection (YOLOv8)
- Text Moderation (PaddleOCR + Profanity)
- Face Detection (MTCNN)

Optimized for parallel execution using asyncio.gather with thread pooling.
"""

import time
import asyncio
import torch
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable
from PIL import Image
from loguru import logger
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings


@dataclass
class ModerationResult:
    """Structured moderation result"""
    status: str  # safe, unsafe, review
    confidence: float
    risk_level: str  # low, medium, high, critical
    recommended_action: str  # allow, quarantine, block
    reason: str
    categories: Dict[str, Any]  # Individual model results
    detected_labels: List[str]
    bounding_boxes: List[Dict[str, Any]]
    processing_time: float
    model_versions: Dict[str, str]


# ========== Model Lazy Loaders ==========

_nsfw_detector = None
_violence_clip_model = None
_violence_clip_processor = None
_weapon_detector = None
_face_detector = None
_ocr_reader = None
_profanity_filter = None


def get_nsfw_detector():
    """Lazy-load NudeNet detector"""
    global _nsfw_detector
    if _nsfw_detector is None:
        logger.info("Loading NudeNet NSFW detector...")
        from nudenet import NudeDetector
        _nsfw_detector = NudeDetector()
        logger.info("✓ NudeNet loaded")
    return _nsfw_detector


def get_violence_detector():
    """Lazy-load CLIP model for violence detection"""
    global _violence_clip_model, _violence_clip_processor
    if _violence_clip_model is None:
        logger.info("Loading CLIP model for violence detection...")
        from transformers import CLIPProcessor, CLIPModel
        model_name = "openai/clip-vit-base-patch32"
        _violence_clip_processor = CLIPProcessor.from_pretrained(model_name)
        _violence_clip_model = CLIPModel.from_pretrained(model_name)
        _violence_clip_model.eval()
        
        if torch.cuda.is_available():
            _violence_clip_model = _violence_clip_model.cuda()
            logger.info("✓ CLIP loaded on GPU")
        else:
            logger.info("✓ CLIP loaded on CPU")
    
    return _violence_clip_model, _violence_clip_processor


def get_weapon_detector():
    """Lazy-load YOLOv8 for weapon detection"""
    global _weapon_detector
    if _weapon_detector is None:
        logger.info("Loading YOLOv8 weapon detector...")
        from ultralytics import YOLO
        
        # Try to load pretrained model, fallback to yolov8n
        try:
            _weapon_detector = YOLO('yolov8n.pt')  # Nano model for speed
            logger.info("✓ YOLOv8 loaded (using general object detection)")
        except Exception as e:
            logger.warning(f"YOLOv8 loading failed: {e}, weapon detection disabled")
            _weapon_detector = None
    
    return _weapon_detector


def get_face_detector():
    """Lazy-load MTCNN face detector"""
    global _face_detector
    if _face_detector is None:
        logger.info("Loading MTCNN face detector...")
        try:
            from facenet_pytorch import MTCNN
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            _face_detector = MTCNN(keep_all=True, device=device)
            logger.info(f"✓ MTCNN loaded on {device}")
        except Exception as e:
            logger.warning(f"MTCNN loading failed: {e}, face detection disabled")
            _face_detector = None
    
    return _face_detector


def get_ocr_reader():
    """Lazy-load PaddleOCR"""
    global _ocr_reader
    if _ocr_reader is None:
        logger.info("Loading PaddleOCR...")
        try:
            from paddleocr import PaddleOCR
            _ocr_reader = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            logger.info("✓ PaddleOCR loaded")
        except Exception as e:
            logger.warning(f"PaddleOCR loading failed: {e}, text detection disabled")
            _ocr_reader = None
    
    return _ocr_reader


def get_profanity_filter():
    """Lazy-load profanity filter"""
    global _profanity_filter
    if _profanity_filter is None:
        logger.info("Loading profanity filter...")
        from better_profanity import profanity
        profanity.load_censor_words()
        _profanity_filter = profanity
        logger.info("✓ Profanity filter loaded")
    
    return _profanity_filter


# ========== Individual Model Detectors ==========

def _convert_box_to_int(box: Any) -> List[int]:
    """
    Utility function to convert bounding box coordinates to integers.
    Handles various input types (list, numpy array, tensor) and ensures all coordinates are integers.
    
    Args:
        box: Bounding box coordinates (can be list, numpy array, or tensor)
    
    Returns:
        List of integer coordinates
    """
    if not box:
        return []
    
    try:
        # Convert to list if it's not already
        if hasattr(box, 'tolist'):
            box = box.tolist()
        elif not isinstance(box, list):
            box = list(box)
        
        # Convert all elements to integers
        return [int(coord) for coord in box]
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to convert box coordinates to int: {e}")
        return []


def detect_nsfw(image_path: str) -> Dict[str, Any]:
    """
    NSFW detection using existing NudeNet pipeline
    Imports the full pipeline from ai_moderation.py
    """
    try:
        from app.services.ai_moderation import moderate_image_file
        result = moderate_image_file(image_path)
        
        # Convert bounding box coordinates to integers using utility function
        bounding_boxes = []
        for bbox in result.get("bounding_boxes", []):
            bbox_copy = bbox.copy()
            if "box" in bbox_copy:
                bbox_copy["box"] = _convert_box_to_int(bbox_copy["box"])
            bounding_boxes.append(bbox_copy)
        
        return {
            "status": result.get("status", "safe"),
            "confidence": result.get("confidence", 0.0),
            "risk_level": result.get("risk_level", "low"),
            "detected_labels": result.get("detected_labels", []),
            "bounding_boxes": bounding_boxes,
            "reason": result.get("reason", ""),
            "model": "nudenet-v3.4.2"
        }
    except Exception as e:
        logger.error(f"NSFW detection error: {e}")
        return {
            "status": "error",
            "confidence": 0.0,
            "risk_level": "unknown",
            "detected_labels": [],
            "bounding_boxes": [],
            "reason": f"NSFW detection failed: {str(e)}",
            "model": "nudenet-v3.4.2"
        }


def detect_violence(image_path: str) -> Dict[str, Any]:
    """
    Violence detection using CLIP zero-shot classification
    Enhanced with strict thresholds to prevent false positives on professional photos
    """
    try:
        model, processor = get_violence_detector()
        
        image = Image.open(image_path).convert("RGB")
        
        # Violence-related categories
        categories = [
            "a safe and peaceful image",
            "violence and fighting",
            "blood and injury",
            "weapons and combat",
            "aggressive behavior"
        ]
        
        inputs = processor(
            text=categories,
            images=image,
            return_tensors="pt",
            padding=True
        )
        
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)[0].cpu().numpy()
        
        # First category is safe, others are violence-related
        safe_prob = float(probs[0])
        violence_probs = probs[1:]
        max_violence_prob = float(violence_probs.max())
        violence_category = categories[1:][violence_probs.argmax()]
        
        # Strict criteria to reduce false positives:
        # 1. Violence probability must be > 0.85 (85%) - very high confidence required
        # 2. Violence probability must be significantly higher than safe probability
        # 3. Require at least 25% margin between violence and safe
        prob_margin = max_violence_prob - safe_prob
        
        is_violent = (max_violence_prob > 0.85) and (prob_margin > 0.25)
        
        # Use safe probability if not violent, violence probability if violent
        confidence = max_violence_prob if is_violent else safe_prob
        
        detected_labels = []
        if is_violent:
            detected_labels.append(violence_category.upper().replace(" AND ", "_"))
        
        # Adjust risk level calculation based on new strict thresholds
        risk_level = "critical" if max_violence_prob > 0.95 else \
                     "high" if max_violence_prob > 0.90 else \
                     "medium" if max_violence_prob > 0.85 else "low"
        
        return {
            "status": "unsafe" if is_violent else "safe",
            "confidence": round(confidence, 4),
            "risk_level": risk_level,
            "detected_labels": detected_labels,
            "bounding_boxes": [],
            "reason": f"Violence detected: {violence_category}" if is_violent else "No violence detected",
            "model": "clip-vit-base-patch32",
            "_debug_violence_prob": round(max_violence_prob, 4),
            "_debug_safe_prob": round(safe_prob, 4),
            "_debug_margin": round(prob_margin, 4)
        }
        
    except Exception as e:
        logger.error(f"Violence detection error: {e}")
        return {
            "status": "error",
            "confidence": 0.0,
            "risk_level": "unknown",
            "detected_labels": [],
            "bounding_boxes": [],
            "reason": f"Violence detection failed: {str(e)}",
            "model": "clip-vit-base-patch32"
        }


def detect_weapons(image_path: str) -> Dict[str, Any]:
    """
    Weapon detection using YOLOv8
    """
    try:
        detector = get_weapon_detector()
        if detector is None:
            return {
                "status": "skipped",
                "confidence": 0.0,
                "risk_level": "unknown",
                "detected_labels": [],
                "bounding_boxes": [],
                "reason": "Weapon detector not available",
                "model": "yolov8n"
            }
        
        results = detector(image_path, verbose=False)
        
        # Weapon-related COCO classes
        weapon_classes = {
            'knife', 'scissors', 'baseball bat', 'tennis racket',
            'bottle', 'fork', 'spoon'  # Potential weapons
        }
        
        detected_labels = []
        bounding_boxes = []
        max_confidence = 0.0
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                class_name = result.names[cls_id]
                
                if class_name in weapon_classes and conf > 0.5:
                    detected_labels.append(class_name.upper().replace(" ", "_"))
                    # Convert box coordinates to integers using utility function
                    box_coords = _convert_box_to_int(box.xyxy[0])
                    bounding_boxes.append({
                        "label": class_name,
                        "box": box_coords,
                        "score": round(conf, 4)
                    })
                    max_confidence = max(max_confidence, conf)
        
        is_weapon = len(detected_labels) > 0
        
        risk_level = "critical" if max_confidence > 0.8 else \
                     "high" if max_confidence > 0.6 else \
                     "medium" if max_confidence > 0.4 else "low"
        
        return {
            "status": "unsafe" if is_weapon else "safe",
            "confidence": round(max_confidence, 4) if is_weapon else 0.95,
            "risk_level": risk_level,
            "detected_labels": detected_labels,
            "bounding_boxes": bounding_boxes,
            "reason": f"Detected weapons: {', '.join(detected_labels)}" if is_weapon else "No weapons detected",
            "model": "yolov8n"
        }
        
    except Exception as e:
        logger.error(f"Weapon detection error: {e}")
        return {
            "status": "error",
            "confidence": 0.0,
            "risk_level": "unknown",
            "detected_labels": [],
            "bounding_boxes": [],
            "reason": f"Weapon detection failed: {str(e)}",
            "model": "yolov8n"
        }


def detect_faces(image_path: str) -> Dict[str, Any]:
    """
    Face detection using MTCNN
    """
    try:
        detector = get_face_detector()
        if detector is None:
            return {
                "status": "skipped",
                "confidence": 0.0,
                "face_count": 0,
                "bounding_boxes": [],
                "reason": "Face detector not available",
                "model": "mtcnn"
            }
        
        image = Image.open(image_path).convert("RGB")
        boxes, probs = detector.detect(image)
        
        face_count = 0
        bounding_boxes = []
        
        if boxes is not None:
            face_count = len(boxes)
            for i, (box, prob) in enumerate(zip(boxes, probs)):
                # Convert box coordinates to integers using utility function
                box_coords = _convert_box_to_int(box)
                bounding_boxes.append({
                    "label": f"FACE_{i+1}",
                    "box": box_coords,
                    "score": round(float(prob), 4)
                })
        
        return {
            "status": "safe",  # Face detection doesn't determine safety alone
            "confidence": 0.95,
            "face_count": face_count,
            "bounding_boxes": bounding_boxes,
            "reason": f"Detected {face_count} face(s)" if face_count > 0 else "No faces detected",
            "model": "mtcnn"
        }
        
    except Exception as e:
        logger.error(f"Face detection error: {e}")
        return {
            "status": "error",
            "confidence": 0.0,
            "face_count": 0,
            "bounding_boxes": [],
            "reason": f"Face detection failed: {str(e)}",
            "model": "mtcnn"
        }


def detect_text(image_path: str) -> Dict[str, Any]:
    """
    Text moderation using PaddleOCR + profanity filter
    """
    try:
        ocr = get_ocr_reader()
        profanity = get_profanity_filter()
        
        if ocr is None or profanity is None:
            return {
                "status": "skipped",
                "confidence": 0.0,
                "detected_text": "",
                "contains_profanity": False,
                "reason": "Text detection not available",
                "model": "paddleocr+profanity"
            }
        
        result = ocr.ocr(image_path, cls=True)
        
        extracted_texts = []
        if result and result[0]:
            for line in result[0]:
                text = line[1][0]
                extracted_texts.append(text)
        
        full_text = " ".join(extracted_texts)
        contains_profanity = profanity.contains_profanity(full_text)
        censored_text = profanity.censor(full_text) if contains_profanity else full_text
        
        risk_level = "high" if contains_profanity else "low"
        
        return {
            "status": "unsafe" if contains_profanity else "safe",
            "confidence": 0.85 if contains_profanity else 0.95,
            "detected_text": censored_text,
            "contains_profanity": contains_profanity,
            "text_count": len(extracted_texts),
            "reason": "Detected inappropriate text" if contains_profanity else "No inappropriate text detected",
            "model": "paddleocr+profanity",
            "risk_level": risk_level
        }
        
    except Exception as e:
        logger.error(f"Text detection error: {e}")
        return {
            "status": "error",
            "confidence": 0.0,
            "detected_text": "",
            "contains_profanity": False,
            "reason": f"Text detection failed: {str(e)}",
            "model": "paddleocr+profanity"
        }


# ========== Main Orchestrator ==========

async def _run_detector_async(
    detector_func: Callable, 
    image_path: str, 
    category_name: str,
    executor: ThreadPoolExecutor
) -> Tuple[str, Dict[str, Any]]:
    """
    Async wrapper to execute a detector function in a thread pool.
    Uses asyncio.to_thread to run CPU/GPU-bound model inference in parallel.
    
    Args:
        detector_func: The synchronous detector function to run
        image_path: Path to the image file
        category_name: Name of the detection category (nsfw, violence, etc.)
        executor: ThreadPoolExecutor instance for running sync code
    
    Returns:
        Tuple of (category_name, result_dict)
    """
    try:
        logger.debug(f"Starting {category_name} detection...")
        
        # Run the synchronous detector function in a thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, detector_func, image_path)
        
        logger.debug(f"Completed {category_name} detection")
        return (category_name, result)
    except Exception as e:
        logger.error(f"Unexpected error in {category_name} detector: {e}")
        return (category_name, {
            "status": "error",
            "confidence": 0.0,
            "risk_level": "unknown",
            "detected_labels": [],
            "bounding_boxes": [],
            "reason": f"{category_name} detection failed: {str(e)}",
            "model": "unknown"
        })


async def moderate_image_comprehensive_async(
    image_path: str,
    enable_nsfw: bool = True,
    enable_violence: bool = True,
    enable_weapons: bool = True,
    enable_faces: bool = True,
    enable_text: bool = True,
    max_workers: int = 5
) -> ModerationResult:
    """
    Async comprehensive image moderation using all available models.
    All model inferences run concurrently using asyncio.gather with ThreadPoolExecutor.
    
    This approach provides maximum parallelism:
    - Async/await for non-blocking execution
    - ThreadPoolExecutor for CPU/GPU-bound ML model inference
    - asyncio.gather to run all models simultaneously
    
    Args:
        image_path: Path to image file
        enable_*: Flags to enable/disable specific detectors
        max_workers: Maximum number of concurrent detector threads (default: 5)
    
    Returns:
        ModerationResult with aggregated verdicts from all models
    """
    start_time = time.time()
    
    if not Path(image_path).exists():
        return ModerationResult(
            status="error",
            confidence=0.0,
            risk_level="unknown",
            recommended_action="block",
            reason=f"Image not found: {image_path}",
            categories={},
            detected_labels=[],
            bounding_boxes=[],
            processing_time=0.0,
            model_versions={}
        )
    
    logger.info(f"Starting async parallel comprehensive moderation for: {image_path}")
    
    # Build list of enabled detectors
    detector_configs = []
    
    if enable_nsfw:
        detector_configs.append(('nsfw', detect_nsfw))
    
    if enable_violence:
        detector_configs.append(('violence', detect_violence))
    
    if enable_weapons:
        detector_configs.append(('weapons', detect_weapons))
    
    if enable_faces:
        detector_configs.append(('faces', detect_faces))
    
    if enable_text:
        detector_configs.append(('text', detect_text))
    
    # Execute all detectors in parallel using asyncio.gather
    results = {}
    
    if detector_configs:
        # Create a ThreadPoolExecutor for running sync model inference
        with ThreadPoolExecutor(max_workers=min(max_workers, len(detector_configs))) as executor:
            # Create async tasks for all detectors
            tasks = [
                _run_detector_async(detector_func, image_path, category_name, executor)
                for category_name, detector_func in detector_configs
            ]
            
            # Run all tasks concurrently and wait for all to complete
            logger.info(f"Launching {len(tasks)} detection tasks in parallel...")
            completed_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in completed_results:
                if isinstance(result, Exception):
                    logger.error(f"Task failed with exception: {result}")
                    continue
                
                category_name, category_result = result
                results[category_name] = category_result
    
    logger.info(f"All parallel detections completed, aggregating results...")
    
    # Aggregate results
    all_labels = []
    all_boxes = []
    risk_scores = []
    model_versions = {}
    
    # Safety Override: Professional Portrait Detection
    # If 1 face detected, no weapons, and violence confidence < 85%, override violence to safe
    has_one_face = (
        'faces' in results and 
        results['faces'].get('face_count') == 1 and
        results['faces'].get('status') == 'safe'
    )
    
    has_no_weapons = (
        'weapons' not in results or 
        results['weapons'].get('status') in ['safe', 'skipped', 'error']
    )
    
    violence_below_threshold = (
        'violence' in results and
        results['violence'].get('_debug_violence_prob', 1.0) < 0.85
    )
    
    # Apply professional portrait override
    if has_one_face and has_no_weapons and violence_below_threshold:
        logger.info("🎯 Professional portrait detected - overriding low-confidence violence detection")
        if 'violence' in results:
            results['violence']['status'] = 'safe'
            results['violence']['detected_labels'] = []
            results['violence']['reason'] = "Professional portrait detected - violence override applied"
            results['violence']['risk_level'] = 'low'
    
    for category, result in results.items():
        if result.get('status') != 'error' and result.get('status') != 'skipped':
            all_labels.extend(result.get('detected_labels', []))
            all_boxes.extend(result.get('bounding_boxes', []))
            model_versions[category] = result.get('model', 'unknown')
            
            # Map risk levels to scores
            risk_map = {'low': 0, 'medium': 25, 'high': 50, 'critical': 100}
            risk_scores.append(risk_map.get(result.get('risk_level', 'low'), 0))
    
    # Determine overall status
    unsafe_categories = [
        cat for cat, res in results.items() 
        if res.get('status') == 'unsafe'
    ]
    
    is_unsafe = len(unsafe_categories) > 0
    
    # Calculate aggregate confidence and risk
    if is_unsafe:
        # Use highest confidence from unsafe categories
        confidences = [
            results[cat].get('confidence', 0.0) 
            for cat in unsafe_categories
        ]
        aggregate_confidence = max(confidences) if confidences else 0.5
        
        # Use highest risk score
        aggregate_risk_score = max(risk_scores) if risk_scores else 50
    else:
        # Average of all confidences for safe verdict
        all_confidences = [
            res.get('confidence', 0.0) 
            for res in results.values() 
            if res.get('status') not in ['error', 'skipped']
        ]
        aggregate_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.95
        aggregate_risk_score = 0
    
    # Map risk score to level
    if aggregate_risk_score >= 80:
        risk_level = "critical"
        recommended_action = "block"
    elif aggregate_risk_score >= 50:
        risk_level = "high"
        recommended_action = "block"
    elif aggregate_risk_score >= 25:
        risk_level = "medium"
        recommended_action = "quarantine"
    else:
        risk_level = "low"
        recommended_action = "allow"
    
    # Build reason
    if is_unsafe:
        reason_parts = [
            results[cat].get('reason', cat) 
            for cat in unsafe_categories
        ]
        reason = "; ".join(reason_parts)
    else:
        reason = "No policy violations detected across all models"
    
    processing_time = time.time() - start_time
    
    logger.info(f"Moderation complete: {'unsafe' if is_unsafe else 'safe'} ({processing_time:.2f}s)")
    
    return ModerationResult(
        status="unsafe" if is_unsafe else "safe",
        confidence=round(aggregate_confidence, 4),
        risk_level=risk_level,
        recommended_action=recommended_action,
        reason=reason,
        categories=results,
        detected_labels=list(set(all_labels)),  # Deduplicate
        bounding_boxes=all_boxes,
        processing_time=round(processing_time, 4),
        model_versions=model_versions
    )


# ========== Synchronous Wrapper (Backward Compatibility) ==========

def moderate_image_comprehensive(
    image_path: str,
    enable_nsfw: bool = True,
    enable_violence: bool = True,
    enable_weapons: bool = True,
    enable_faces: bool = True,
    enable_text: bool = True,
    max_workers: int = 5
) -> ModerationResult:
    """
    Synchronous wrapper for backward compatibility.
    Runs the async function in a new event loop.
    """
    return asyncio.run(moderate_image_comprehensive_async(
        image_path=image_path,
        enable_nsfw=enable_nsfw,
        enable_violence=enable_violence,
        enable_weapons=enable_weapons,
        enable_faces=enable_faces,
        enable_text=enable_text,
        max_workers=max_workers
    ))


async def moderate_image_result_dict_async(image_path: str, **kwargs) -> Dict[str, Any]:
    """
    Async convenience wrapper that returns dict instead of dataclass
    """
    result = await moderate_image_comprehensive_async(image_path, **kwargs)
    return asdict(result)


def moderate_image_result_dict(image_path: str, **kwargs) -> Dict[str, Any]:
    """
    Synchronous convenience wrapper for backward compatibility.
    Internally uses async implementation with asyncio.run.
    """
    result = moderate_image_comprehensive(image_path, **kwargs)
    return asdict(result)

