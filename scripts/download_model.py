"""
Model Download Script
Downloads pre-trained YOLOv8 PPE detection model
"""

import sys
from pathlib import Path
from loguru import logger
import requests
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ultralytics import YOLO


def download_file(url: str, destination: Path) -> bool:
    """
    Download file with progress bar.
    
    Args:
        url: Download URL
        destination: Destination file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(destination, 'wb') as f, tqdm(
            desc=destination.name,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                size = f.write(chunk)
                pbar.update(size)
        
        return True
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False


def download_default_model():
    """Download default YOLOv8n model."""
    logger.info("Downloading default YOLOv8n model...")
    
    try:
        model = YOLO('yolov8n.pt')
        logger.success("YOLOv8n model downloaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        return False


def download_ppe_model():
    """
    Download pre-trained PPE detection model from Roboflow.
    
    Note: This is a placeholder. In production, replace with actual
    trained model URL or use Roboflow API.
    """
    models_dir = Path("data/models")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Checking for custom PPE model...")
    
    # Option 1: Use Roboflow API (requires API key)
    # from roboflow import Roboflow
    # rf = Roboflow(api_key="YOUR_API_KEY")
    # project = rf.workspace().project("ppe-detection")
    # model = project.version(1).model
    
    # Option 2: Download from custom URL (if available)
    # custom_model_url = "https://your-storage.com/yolov8n-ppe.pt"
    # destination = models_dir / "yolov8n-ppe.pt"
    
    # For now, just use the default model
    logger.info("Using default YOLOv8 model (no custom PPE model found)")
    logger.info("To use a custom model:")
    logger.info("1. Train on Roboflow PPE dataset")
    logger.info("2. Export as YOLOv8 format")
    logger.info("3. Place in data/models/ directory")
    
    return download_default_model()


def verify_model(model_path: str = "yolov8n.pt") -> bool:
    """
    Verify model can be loaded.
    
    Args:
        model_path: Path to model file
        
    Returns:
        True if model loads successfully
    """
    try:
        model = YOLO(model_path)
        logger.info(f"Model verified: {model_path}")
        logger.info(f"Model type: {model.task}")
        return True
    except Exception as e:
        logger.error(f"Model verification failed: {e}")
        return False


def main():
    """Main execution."""
    logger.info("=" * 60)
    logger.info("SiteGuard AI - Model Download Script")
    logger.info("=" * 60)
    
    # Create directories
    Path("data/models").mkdir(parents=True, exist_ok=True)
    
    # Download model
    success = download_ppe_model()
    
    if success:
        # Verify model
        if verify_model():
            logger.success("✅ Model setup complete!")
            logger.info("You can now run the application with:")
            logger.info("  streamlit run app/streamlit_app.py")
            logger.info("or")
            logger.info("  uvicorn app.api.main:app --reload")
        else:
            logger.error("❌ Model verification failed")
            sys.exit(1)
    else:
        logger.error("❌ Model download failed")
        sys.exit(1)


if __name__ == "__main__":
    main()