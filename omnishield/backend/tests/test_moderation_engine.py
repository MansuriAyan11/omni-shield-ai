import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import os

from app.services.ai_moderation import moderate_image_file

@pytest.fixture
def temp_dummy_image():
    """Create a dummy temporary image file for testing."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    # Write a few bytes so it exists and has non-zero size
    tmp.write(b"dummy image content bytes")
    tmp.close()
    yield tmp.name
    if os.path.exists(tmp.name):
        try:
            os.remove(tmp.name)
        except Exception:
            pass


@patch("app.services.ai_moderation.get_detector")
@patch("app.services.ai_moderation.is_closeup")
def test_moderation_safe_image(mock_closeup, mock_get_detector, temp_dummy_image):
    # Setup mocks
    mock_closeup.return_value = False
    
    mock_detector = MagicMock()
    mock_detector.detect.return_value = [] # No detections
    mock_get_detector.return_value = mock_detector

    # Execute
    result = moderate_image_file(temp_dummy_image)
    
    # Assertions
    assert result["status"] == "safe"
    assert result["risk_level"] == "low"
    assert result["recommended_action"] == "allow"
    assert len(result["detected_labels"]) == 0
    assert len(result["bounding_boxes"]) == 0


@patch("app.services.ai_moderation.get_detector")
@patch("app.services.ai_moderation.is_closeup")
def test_moderation_unsafe_explicit_image(mock_closeup, mock_get_detector, temp_dummy_image):
    # Setup mocks
    mock_closeup.return_value = False
    
    mock_detector = MagicMock()
    # Explicit genitalia detected
    mock_detector.detect.return_value = [
        {"class": "FEMALE_GENITALIA_EXPOSED", "score": 0.89, "box": [100, 100, 200, 200]}
    ]
    mock_get_detector.return_value = mock_detector

    # Execute
    result = moderate_image_file(temp_dummy_image)
    
    # Assertions
    assert result["status"] == "unsafe"
    assert result["risk_level"] == "critical"
    assert result["recommended_action"] == "block"
    assert "FEMALE_GENITALIA_EXPOSED" in result["detected_labels"]
    assert len(result["bounding_boxes"]) == 1
    assert result["bounding_boxes"][0]["label"] == "FEMALE_GENITALIA_EXPOSED"
    assert result["bounding_boxes"][0]["score"] == 0.89


@patch("app.services.ai_moderation.get_detector")
@patch("app.services.ai_moderation.is_closeup")
def test_moderation_suggestive_closeup_fallback(mock_closeup, mock_get_detector, temp_dummy_image):
    # Setup close-up triggers fallback heuristics
    mock_closeup.return_value = True
    
    mock_detector = MagicMock()
    # Close-up belly exposed with no faces present triggers Rule 1 fallback
    mock_detector.detect.return_value = [
        {"class": "BELLY_EXPOSED", "score": 0.75, "box": [50, 50, 150, 150]}
    ]
    mock_get_detector.return_value = mock_detector

    # Execute
    result = moderate_image_file(temp_dummy_image)
    
    # Assertions
    assert result["status"] == "unsafe"
    assert result["risk_level"] == "medium"
    assert result["recommended_action"] == "quarantine"
    assert "MALE_GENITALIA_COVERED_INFERRED" in result["detected_labels"]
