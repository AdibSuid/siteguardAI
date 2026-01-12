"""
Computer vision module for PPE detection
"""

from .detector import PPEDetector, Detection, DetectionResult, create_detector

__all__ = ['PPEDetector', 'Detection', 'DetectionResult', 'create_detector']
