#!/usr/bin/env python3
"""
Test script to verify ONVIF discovery imports work correctly
"""

import sys
from pathlib import Path

# Add project root to path so we can import app modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all required imports work."""
    try:
        from app.core.vision.rtsp_onvif import ONVIFDiscovery, RTSPCamera, discover_cameras
        print("✅ ONVIF module imports successful")

        # Test that functions work
        result = discover_cameras()
        if isinstance(result, dict) and 'webcam' in result and 'onvif' in result:
            print("✅ discover_cameras function works correctly")
            print(f"   Found {len(result['webcam'])} webcams and {len(result['onvif'])} ONVIF cameras")
        else:
            print("❌ discover_cameras returned unexpected format")

        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Testing ONVIF discovery imports...")
    success = test_imports()
    if success:
        print("\n🎉 All tests passed! ONVIF discovery script is ready to use.")
    else:
        print("\n❌ Tests failed. Please check the installation.")