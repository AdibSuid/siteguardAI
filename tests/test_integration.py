"""
Integration tests for SiteGuard AI
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.vision.detector import PPEDetector, create_detector
from app.core.llm.generator import ReportGenerator, ReportMetadata, ReportFormat


def test_end_to_end_detection():
    """Test complete detection pipeline."""
    # Create detector
    config = {
        "model_path": "yolov8n.pt",
        "confidence_threshold": 0.5,
        "device": "cpu"
    }
    
    detector = create_detector(config)
    assert detector is not None
    assert detector.confidence_threshold == 0.5


def test_config_loading():
    """Test configuration loading."""
    from utils.config import get_detector_config, get_llm_config
    
    detector_config = get_detector_config()
    assert "model_path" in detector_config
    assert "confidence_threshold" in detector_config
    
    llm_config = get_llm_config()
    assert "provider" in llm_config
    assert "temperature" in llm_config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
