"""
Unit tests for PPE Detector
"""

import pytest
import numpy as np
import cv2
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.vision.detector import PPEDetector, Detection, DetectionResult


@pytest.fixture
def detector():
    """Create a detector instance for testing."""
    return PPEDetector(
        model_path="yolov8n.pt",
        confidence_threshold=0.5,
        device="cpu"
    )


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    # Create a simple 640x640 RGB image
    image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    return image


class TestDetection:
    """Test Detection dataclass."""
    
    def test_detection_creation(self):
        """Test Detection object creation."""
        det = Detection(
            class_name="Helmet",
            confidence=0.95,
            bbox=(100, 100, 200, 200),
            class_id=0
        )
        
        assert det.class_name == "Helmet"
        assert det.confidence == 0.95
        assert det.bbox == (100, 100, 200, 200)
        assert det.class_id == 0
    
    def test_detection_center(self):
        """Test center calculation."""
        det = Detection(
            class_name="Helmet",
            confidence=0.95,
            bbox=(100, 100, 200, 200),
            class_id=0
        )
        
        assert det.center == (150, 150)
    
    def test_detection_area(self):
        """Test area calculation."""
        det = Detection(
            class_name="Helmet",
            confidence=0.95,
            bbox=(100, 100, 200, 200),
            class_id=0
        )
        
        assert det.area == 10000


class TestDetectionResult:
    """Test DetectionResult dataclass."""
    
    def test_result_creation(self):
        """Test DetectionResult creation."""
        detections = [
            Detection("Helmet", 0.95, (100, 100, 200, 200), 0)
        ]
        
        result = DetectionResult(
            image_path="test.jpg",
            detections=detections,
            inference_time_ms=50.0,
            violations=[]
        )
        
        assert result.image_path == "test.jpg"
        assert len(result.detections) == 1
        assert result.inference_time_ms == 50.0
    
    def test_has_violations(self):
        """Test violation detection."""
        result = DetectionResult(
            image_path="test.jpg",
            detections=[],
            inference_time_ms=50.0,
            violations=[{"type": "no_helmet"}]
        )
        
        assert result.has_violations is True
        
        result.violations = []
        assert result.has_violations is False
    
    def test_violation_summary(self):
        """Test violation summary generation."""
        violations = [
            {"type": "no_helmet"},
            {"type": "no_helmet"},
            {"type": "no_vest"}
        ]
        
        result = DetectionResult(
            image_path="test.jpg",
            detections=[],
            inference_time_ms=50.0,
            violations=violations
        )
        
        summary = result.violation_summary
        assert summary["no_helmet"] == 2
        assert summary["no_vest"] == 1


class TestPPEDetector:
    """Test PPEDetector class."""
    
    def test_detector_initialization(self, detector):
        """Test detector initialization."""
        assert detector is not None
        assert detector.model is not None
        assert detector.confidence_threshold == 0.5
        assert detector.device in ["cpu", "cuda"]
    
    def test_detect_with_image_array(self, detector, sample_image):
        """Test detection with numpy array."""
        result = detector.detect(sample_image)
        
        assert isinstance(result, DetectionResult)
        assert result.image_path == "array_input"
        assert result.inference_time_ms > 0
        assert isinstance(result.detections, list)
    
    def test_calculate_iou(self, detector):
        """Test IoU calculation."""
        box1 = (0, 0, 100, 100)
        box2 = (50, 50, 150, 150)
        
        iou = detector._calculate_iou(box1, box2)
        
        # Intersection: 50x50 = 2500
        # Union: 10000 + 10000 - 2500 = 17500
        # IoU: 2500/17500 ≈ 0.143
        assert 0.14 < iou < 0.15
    
    def test_calculate_iou_no_overlap(self, detector):
        """Test IoU with no overlap."""
        box1 = (0, 0, 100, 100)
        box2 = (200, 200, 300, 300)
        
        iou = detector._calculate_iou(box1, box2)
        assert iou == 0.0
    
    def test_metrics_tracking(self, detector, sample_image):
        """Test metrics tracking."""
        initial_metrics = detector.get_metrics()
        assert initial_metrics["total_inferences"] == 0
        
        detector.detect(sample_image)
        
        updated_metrics = detector.get_metrics()
        assert updated_metrics["total_inferences"] == 1
        assert updated_metrics["total_inference_time"] > 0
    
    def test_reset_metrics(self, detector, sample_image):
        """Test metrics reset."""
        detector.detect(sample_image)
        detector.reset_metrics()
        
        metrics = detector.get_metrics()
        assert metrics["total_inferences"] == 0
        assert metrics["total_inference_time"] == 0.0
        assert metrics["violations_detected"] == 0


class TestBatchProcessing:
    """Test batch processing functionality."""
    
    def test_batch_detect(self, detector):
        """Test batch detection."""
        # Create multiple sample images
        images = [
            np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            for _ in range(3)
        ]
        
        results = detector.detect_batch(images, batch_size=2)
        
        assert len(results) == 3
        assert all(isinstance(r, DetectionResult) for r in results)


@pytest.mark.parametrize("confidence,expected_min", [
    (0.3, 0),
    (0.5, 0),
    (0.7, 0),
    (0.9, 0)
])
def test_confidence_threshold(detector, sample_image, confidence, expected_min):
    """Test different confidence thresholds."""
    result = detector.detect(sample_image, conf_threshold=confidence)
    assert len(result.detections) >= expected_min


def test_invalid_image_path(detector):
    """Test handling of invalid image path."""
    with pytest.raises(ValueError):
        detector.detect("nonexistent_image.jpg")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])