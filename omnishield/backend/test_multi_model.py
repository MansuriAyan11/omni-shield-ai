"""
Test script for multi-model moderation system
Run this to verify all AI models are loading and working correctly
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.multi_model_moderation import (
    get_nsfw_detector,
    get_violence_detector,
    get_weapon_detector,
    get_face_detector,
    get_ocr_reader,
    get_profanity_filter,
    moderate_image_comprehensive
)
from loguru import logger


def test_model_loading():
    """Test that all models can be loaded"""
    print("\n" + "="*60)
    print("TESTING MODEL LOADING")
    print("="*60 + "\n")
    
    models_status = {}
    
    # Test NSFW detector
    try:
        print("📦 Loading NSFW detector (NudeNet)...")
        detector = get_nsfw_detector()
        print("✅ NSFW detector loaded successfully")
        models_status['nsfw'] = True
    except Exception as e:
        print(f"❌ NSFW detector failed: {e}")
        models_status['nsfw'] = False
    
    # Test Violence detector
    try:
        print("\n📦 Loading Violence detector (CLIP)...")
        model, processor = get_violence_detector()
        print("✅ Violence detector loaded successfully")
        models_status['violence'] = True
    except Exception as e:
        print(f"❌ Violence detector failed: {e}")
        models_status['violence'] = False
    
    # Test Weapon detector
    try:
        print("\n📦 Loading Weapon detector (YOLOv8)...")
        detector = get_weapon_detector()
        if detector:
            print("✅ Weapon detector loaded successfully")
            models_status['weapons'] = True
        else:
            print("⚠️  Weapon detector not available (expected on first run)")
            models_status['weapons'] = False
    except Exception as e:
        print(f"❌ Weapon detector failed: {e}")
        models_status['weapons'] = False
    
    # Test Face detector
    try:
        print("\n📦 Loading Face detector (MTCNN)...")
        detector = get_face_detector()
        if detector:
            print("✅ Face detector loaded successfully")
            models_status['faces'] = True
        else:
            print("⚠️  Face detector not available")
            models_status['faces'] = False
    except Exception as e:
        print(f"❌ Face detector failed: {e}")
        models_status['faces'] = False
    
    # Test OCR
    try:
        print("\n📦 Loading OCR (PaddleOCR)...")
        ocr = get_ocr_reader()
        if ocr:
            print("✅ OCR loaded successfully")
            models_status['ocr'] = True
        else:
            print("⚠️  OCR not available")
            models_status['ocr'] = False
    except Exception as e:
        print(f"❌ OCR failed: {e}")
        models_status['ocr'] = False
    
    # Test Profanity filter
    try:
        print("\n📦 Loading Profanity filter...")
        profanity = get_profanity_filter()
        print("✅ Profanity filter loaded successfully")
        models_status['profanity'] = True
    except Exception as e:
        print(f"❌ Profanity filter failed: {e}")
        models_status['profanity'] = False
    
    # Summary
    print("\n" + "="*60)
    print("MODEL LOADING SUMMARY")
    print("="*60)
    loaded = sum(models_status.values())
    total = len(models_status)
    print(f"\n✅ {loaded}/{total} models loaded successfully\n")
    
    for model, status in models_status.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {model.upper()}")
    
    return models_status


def test_image_moderation():
    """Test moderation on sample images if available"""
    print("\n" + "="*60)
    print("TESTING IMAGE MODERATION")
    print("="*60 + "\n")
    
    # Check for test images
    test_images_dir = Path(__file__).parent / "dataset"
    
    if not test_images_dir.exists():
        print("⚠️  No test images found at:", test_images_dir)
        print("   Skipping image moderation test")
        return
    
    safe_images = list((test_images_dir / "safe").glob("*.jpg"))
    unsafe_images = list((test_images_dir / "unsafe").glob("*.jpg"))
    
    if not safe_images and not unsafe_images:
        print("⚠️  No test images found in safe/ or unsafe/ directories")
        return
    
    # Test safe images
    if safe_images:
        print(f"\n📸 Testing {len(safe_images)} SAFE images:\n")
        for img in safe_images[:2]:  # Test max 2
            print(f"Testing: {img.name}")
            result = moderate_image_comprehensive(str(img))
            print(f"  Decision: {result.status}")
            print(f"  Risk: {result.risk_level}")
            print(f"  Confidence: {result.confidence:.2f}")
            print(f"  Time: {result.processing_time:.2f}s")
            print()
    
    # Test unsafe images
    if unsafe_images:
        print(f"\n🚨 Testing {len(unsafe_images)} UNSAFE images:\n")
        for img in unsafe_images[:2]:  # Test max 2
            print(f"Testing: {img.name}")
            result = moderate_image_comprehensive(str(img))
            print(f"  Decision: {result.status}")
            print(f"  Risk: {result.risk_level}")
            print(f"  Confidence: {result.confidence:.2f}")
            print(f"  Labels: {', '.join(result.detected_labels) if result.detected_labels else 'None'}")
            print(f"  Time: {result.processing_time:.2f}s")
            print()


def main():
    """Main test function"""
    print("\n" + "="*60)
    print("OMNISHIELD MULTI-MODEL TEST SUITE")
    print("="*60)
    
    # Test 1: Model Loading
    models_status = test_model_loading()
    
    # Test 2: Image Moderation (if models loaded)
    if any(models_status.values()):
        test_image_moderation()
    else:
        print("\n⚠️  Skipping image moderation test (no models loaded)")
    
    # Final summary
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("\nIf models failed to load, install missing dependencies:")
    print("  pip install torch torchvision transformers")
    print("  pip install paddleocr paddlepaddle")
    print("  pip install facenet-pytorch")
    print("  pip install ultralytics")
    print("\nFor GPU support:")
    print("  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
