"""
Setup script for development environment
"""

import sys
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def setup_environment():
    """Setup development environment."""
    print("=" * 60)
    print("SiteGuard AI - Development Environment Setup")
    print("=" * 60)
    
    # Create necessary directories
    dirs = [
        "data/uploads",
        "data/outputs",
        "logs",
        "models",
        "reports"
    ]
    
    root = Path(__file__).parent.parent
    
    for dir_path in dirs:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {dir_path}")
    
    print("\n" + "=" * 60)
    print("Environment setup complete!")
    print("=" * 60)
    
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Create .env file with API keys")
    print("3. Download YOLO model: python scripts/download_model.py")
    print("4. Run tests: pytest tests/")
    print("5. Start API: python scripts/run_api.py")
    print("6. Start Web: python scripts/run_web.py")


if __name__ == "__main__":
    setup_environment()
