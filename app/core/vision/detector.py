"""
PPE Detection Module
Uses YOLOv8 for real-time Personal Protective Equipment detection.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import time

from ultralytics import YOLO
from loguru import logger


# PPE Categories
PPE_CLASSES = {
    'hardhat': ['Hardhat', 'Hard Hat', 'Helmet'],
    'vest': ['Safety Vest', 'Vest', 'High-Visibility Vest'],
    'mask': ['Mask', 'Face Mask', 'Respirator'],
    'gloves': ['Gloves', 'Safety Gloves'],
    'goggles': ['Goggles', 'Safety Glasses', 'Eye Protection'],
    'boots': ['Safety Boots', 'Steel Toe Boots'],
    'person': ['Person', 'Worker', 'Human']
}

# Violation Rules: Required PPE for certain detections
VIOLATION_RULES = {
    'no_hardhat': 'Worker detected without hardhat',
    'no_vest': 'Worker detected without safety vest',
    'no_mask': 'Worker detected without face mask',
    'no_gloves': 'Worker detected without gloves',
    'no_goggles': 'Worker detected without eye protection'
}


@dataclass
class Detection:
    """Single detection result."""
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    class_id: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'class_name': self.class_name,
            'confidence': float(self.confidence),
            'bbox': list(self.bbox),
            'class_id': int(self.class_id)
        }


@dataclass
class DetectionResult:
    """Complete detection result for an image."""
    image_path: str
    detections: List[Detection] = field(default_factory=list)
    violations: List[Dict] = field(default_factory=list)
    annotated_image: Optional[np.ndarray] = None
    inference_time_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def has_violations(self) -> bool:
        """Check if any violations detected."""
        return len(self.violations) > 0
    
    @property
    def violation_count(self) -> int:
        """Get total violation count."""
        return len(self.violations)
    
    @property
    def detection_count(self) -> int:
        """Get total detection count."""
        return len(self.detections)
    
    def get_violation_summary(self) -> Dict[str, int]:
        """Get summary of violations by type."""
        summary = {}
        for violation in self.violations:
            vtype = violation.get('type', 'unknown')
            summary[vtype] = summary.get(vtype, 0) + 1
        return summary
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'image_path': self.image_path,
            'detections': [d.to_dict() for d in self.detections],
            'violations': self.violations,
            'has_violations': self.has_violations,
            'violation_count': self.violation_count,
            'detection_count': self.detection_count,
            'violation_summary': self.get_violation_summary(),
            'inference_time_ms': self.inference_time_ms,
            'timestamp': self.timestamp
        }


class PPEDetector:
    """
    PPE Detection Engine using YOLOv8.
    
    Detects personal protective equipment and identifies safety violations.
    """
    
    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence_threshold: float = 0.5,
        device: str = "cpu",
        enable_tracking: bool = False
    ):
        """
        Initialize PPE detector.
        
        Args:
            model_path: Path to YOLOv8 model weights
            confidence_threshold: Minimum confidence for detections
            device: Device to run inference on ('cpu' or 'cuda')
            enable_tracking: Enable object tracking
        """
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.device = device
        self.enable_tracking = enable_tracking
        
        # Metrics tracking
        self.total_inferences = 0
        self.violations_detected = 0
        
        # Load model
        logger.info(f"Loading YOLO model from {model_path}")
        try:
            self.model = YOLO(str(model_path))
            if device == "cuda":
                self.model.to('cuda')
            logger.info(f"Model loaded successfully on {device}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
        
        # Get class names from model
        if hasattr(self.model, 'names'):
            self.class_names = self.model.names
        else:
            # Default COCO classes if custom model not available
            self.class_names = {0: 'person'}
        
        logger.info(f"Detector initialized with {len(self.class_names)} classes")
    
    def detect(
        self,
        image: Union[str, Path, np.ndarray],
        annotate: bool = True,
        check_violations: bool = True
    ) -> DetectionResult:
        """
        Detect PPE in image.
        
        Args:
            image: Image path or numpy array
            annotate: Whether to create annotated image
            check_violations: Whether to check for violations
        
        Returns:
            DetectionResult object
        """
        start_time = time.time()
        
        # Load image if path provided
        if isinstance(image, (str, Path)):
            image_path = str(image)
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image from {image_path}")
        else:
            img = image.copy()
            image_path = "array_input"
        
        # Run inference
        results = self.model.predict(
            img,
            conf=self.confidence_threshold,
            device=self.device,
            verbose=False
        )
        
        # Parse detections
        detections = []
        if len(results) > 0:
            result = results[0]
            
            if hasattr(result, 'boxes') and result.boxes is not None:
                boxes = result.boxes
                
                for i in range(len(boxes)):
                    box = boxes.xyxy[i].cpu().numpy()
                    conf = float(boxes.conf[i].cpu().numpy())
                    cls_id = int(boxes.cls[i].cpu().numpy())
                    
                    cls_name = self.class_names.get(cls_id, f"class_{cls_id}")
                    
                    detection = Detection(
                        class_name=cls_name,
                        confidence=conf,
                        bbox=(int(box[0]), int(box[1]), int(box[2]), int(box[3])),
                        class_id=cls_id
                    )
                    detections.append(detection)
        
        # Check for violations
        violations = []
        if check_violations:
            violations = self._check_violations(detections)
        
        # Create annotated image
        annotated_img = None
        if annotate:
            annotated_img = self._annotate_image(img.copy(), detections, violations)
        
        inference_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Update metrics
        self.total_inferences += 1
        if violations:
            self.violations_detected += len(violations)
        
        return DetectionResult(
            image_path=image_path,
            detections=detections,
            violations=violations,
            annotated_image=annotated_img,
            inference_time_ms=inference_time
        )
    
    def _check_violations(self, detections: List[Detection]) -> List[Dict]:
        """
        Check for PPE violations.
        
        Args:
            detections: List of detections
        
        Returns:
            List of violations
        """
        violations = []
        
        # Count detections by category
        detected_classes = {d.class_name.lower() for d in detections}
        
        # Check for person without PPE
        has_person = any('person' in cls for cls in detected_classes)
        has_hardhat = any(any(h.lower() in cls for h in PPE_CLASSES['hardhat']) 
                         for cls in detected_classes)
        has_vest = any(any(v.lower() in cls for v in PPE_CLASSES['vest']) 
                      for cls in detected_classes)
        
        if has_person:
            if not has_hardhat:
                violations.append({
                    'type': 'no_hardhat',
                    'severity': 'high',
                    'description': VIOLATION_RULES['no_hardhat'],
                    'osha_standard': '1926.100',
                    'confidence': 0.95,
                    'timestamp': datetime.now().isoformat()
                })
            
            if not has_vest:
                violations.append({
                    'type': 'no_vest',
                    'severity': 'high',
                    'description': VIOLATION_RULES['no_vest'],
                    'osha_standard': '1926.201',
                    'confidence': 0.95,
                    'timestamp': datetime.now().isoformat()
                })
        
        return violations
    
    def _annotate_image(
        self,
        image: np.ndarray,
        detections: List[Detection],
        violations: List[Dict]
    ) -> np.ndarray:
        """
        Draw bounding boxes and labels on image.
        
        Args:
            image: Input image
            detections: List of detections
            violations: List of violations
        
        Returns:
            Annotated image
        """
        img = image.copy()
        
        # Define colors
        SAFE_COLOR = (0, 255, 0)  # Green
        VIOLATION_COLOR = (0, 0, 255)  # Red
        TEXT_COLOR = (255, 255, 255)  # White
        
        has_violations = len(violations) > 0
        
        # Draw detections
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            color = VIOLATION_COLOR if has_violations else SAFE_COLOR
            
            # Draw bounding box
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{det.class_name} {det.confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            
            # Background for text
            cv2.rectangle(
                img,
                (x1, y1 - label_size[1] - 10),
                (x1 + label_size[0], y1),
                color,
                -1
            )
            
            # Draw text
            cv2.putText(
                img,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                TEXT_COLOR,
                2
            )
        
        # Add violation warning
        if has_violations:
            warning = f"VIOLATIONS DETECTED: {len(violations)}"
            cv2.putText(
                img,
                warning,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                VIOLATION_COLOR,
                3
            )
        
        return img
    
    def detect_batch(
        self,
        images: List[Union[str, Path, np.ndarray]],
        **kwargs
    ) -> List[DetectionResult]:
        """
        Detect PPE in multiple images.
        
        Args:
            images: List of image paths or arrays
            **kwargs: Additional arguments for detect()
        
        Returns:
            List of DetectionResult objects
        """
        results = []
        for img in images:
            try:
                result = self.detect(img, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing image: {e}")
                # Add empty result
                results.append(DetectionResult(
                    image_path="",
                    detections=[],
                    confidence_threshold=self.confidence_threshold,
                    processing_time=0.0
                ))
        return results
    
    def get_metrics(self) -> Dict[str, int]:
        """Get detection metrics."""
        return {
            "total_inferences": self.total_inferences,
            "violations_detected": self.violations_detected
        }
    
    def reset_metrics(self) -> None:
        """Reset metrics counters."""
        self.total_inferences = 0
        self.violations_detected = 0


def create_detector(config: Optional[Dict] = None) -> PPEDetector:
        
        return results


def create_detector(config: Optional[Dict] = None) -> PPEDetector:
    """
    Factory function to create PPE detector.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        PPEDetector instance
    """
    if config is None:
        config = {}
    
    return PPEDetector(
        model_path=config.get('model_path', 'yolov8n.pt'),
        confidence_threshold=config.get('confidence_threshold', 0.5),
        device=config.get('device', 'cpu'),
        enable_tracking=config.get('enable_tracking', False)
    )
