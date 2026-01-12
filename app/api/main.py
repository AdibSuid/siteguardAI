"""
SiteGuard AI - FastAPI Backend
RESTful API for PPE detection and incident reporting.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from pathlib import Path
import cv2
import numpy as np
from loguru import logger
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.vision.detector import PPEDetector, create_detector
from app.core.llm.generator import (
    ReportGenerator, 
    ReportMetadata, 
    ReportFormat,
    create_report_generator
)
from utils.config import get_detector_config, get_llm_config


# Initialize FastAPI app
app = FastAPI(
    title="SiteGuard AI API",
    description="RESTful API for automated workplace safety monitoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
detector: Optional[PPEDetector] = None
report_generator: Optional[ReportGenerator] = None


# Pydantic models
class DetectionRequest(BaseModel):
    """Request model for detection."""
    confidence_threshold: float = Field(default=0.5, ge=0.1, le=0.9)
    return_image: bool = Field(default=True)


class ReportRequest(BaseModel):
    """Request model for report generation."""
    location: str = Field(..., min_length=1)
    site_id: Optional[str] = None
    inspector_id: Optional[str] = None
    shift: Optional[str] = None
    weather_conditions: Optional[str] = None
    camera_id: Optional[str] = None
    report_format: str = Field(default="formal")


class DetectionResponse(BaseModel):
    """Response model for detection."""
    success: bool
    image_path: str
    detections: List[Dict]
    violations: List[Dict]
    inference_time_ms: float
    has_violations: bool
    violation_summary: Dict[str, int]
    timestamp: str


class ReportResponse(BaseModel):
    """Response model for report generation."""
    success: bool
    report_id: str
    title: str
    text: str
    violations_count: int
    recommendations: List[str]
    format: str
    generated_at: str
    metadata: Dict


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    models_loaded: bool
    detector_ready: bool
    generator_ready: bool


@app.on_event("startup")
async def startup_event():
    """Initialize models on startup."""
    global detector, report_generator
    
    logger.info("Initializing SiteGuard AI API...")
    
    try:
        # Initialize detector
        detector_config = get_detector_config()
        detector = create_detector(detector_config)
        logger.success("PPE Detector initialized")
        
        # Initialize report generator
        generator_config = get_llm_config()
        report_generator = create_report_generator(generator_config)
        logger.success("Report Generator initialized")
        
        logger.success("SiteGuard AI API ready!")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "SiteGuard AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy" if (detector is not None and report_generator is not None) else "degraded",
        timestamp=datetime.now().isoformat(),
        models_loaded=detector is not None and report_generator is not None,
        detector_ready=detector is not None,
        generator_ready=report_generator is not None
    )


@app.post("/api/v1/detect", response_model=DetectionResponse, tags=["Detection"])
async def detect_violations(
    file: UploadFile = File(...),
    confidence_threshold: float = 0.5
):
    """Detect PPE violations in uploaded image."""
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector not initialized")
    
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Could not decode image")
        
        # Run detection
        results = detector.detect(image)
        
        return DetectionResponse(
            success=True,
            image_path=results.image_path,
            detections=[d.to_dict() for d in results.detections],
            violations=results.violations,
            inference_time_ms=results.inference_time_ms,
            has_violations=results.has_violations,
            violation_summary=results.get_violation_summary(),
            timestamp=results.timestamp
        )
        
    except Exception as e:
        logger.error(f"Detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/generate-report", response_model=ReportResponse, tags=["Reports"])
async def generate_incident_report(
    violations: List[Dict],
    metadata: ReportRequest
):
    """Generate incident report from violations."""
    if report_generator is None:
        raise HTTPException(status_code=503, detail="Report generator not initialized")
    
    try:
        report_metadata = ReportMetadata(
            location=metadata.location,
            timestamp=datetime.now(),
            site_id=metadata.site_id,
            inspector_id=metadata.inspector_id,
            shift=metadata.shift,
            weather_conditions=metadata.weather_conditions,
            camera_id=metadata.camera_id
        )
        
        try:
            report_format = ReportFormat[metadata.report_format.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid report format: {metadata.report_format}")
        
        report = report_generator.generate_report(
            violations=violations,
            metadata=report_metadata,
            format=report_format
        )
        
        return ReportResponse(
            success=True,
            report_id=report.report_id,
            title=report.title,
            text=report.text,
            violations_count=len(report.violations),
            recommendations=report.recommendations,
            format=report.format.value,
            generated_at=report.generated_at.isoformat(),
            metadata={
                "location": report.metadata.location,
                "timestamp": report.metadata.timestamp.isoformat(),
                "site_id": report.metadata.site_id,
                "inspector_id": report.metadata.inspector_id
            }
        )
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/analyze", tags=["Analysis"])
async def analyze_image(
    file: UploadFile = File(...),
    location: str = "Unknown Location",
    confidence_threshold: float = 0.5,
    report_format: str = "formal"
):
    """Complete analysis: detect violations and generate report."""
    if detector is None or report_generator is None:
        raise HTTPException(status_code=503, detail="Models not initialized")
    
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Could not decode image")
        
        results = detector.detect(image)
        
        report = None
        if results.has_violations:
            metadata = ReportMetadata(location=location, timestamp=datetime.now())
            try:
                fmt = ReportFormat[report_format.upper()]
            except KeyError:
                fmt = ReportFormat.FORMAL
            
            report = report_generator.generate_report(
                violations=results.violations,
                metadata=metadata,
                format=fmt
            )
        
        response = {
            "success": True,
            "detection": {
                "detections_count": len(results.detections),
                "violations_count": len(results.violations),
                "has_violations": results.has_violations,
                "inference_time_ms": results.inference_time_ms,
                "violations": results.violations
            }
        }
        
        if report:
            response["report"] = {
                "report_id": report.report_id,
                "title": report.title,
                "text": report.text,
                "recommendations": report.recommendations,
                "generated_at": report.generated_at.isoformat()
            }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
