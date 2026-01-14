#!/usr/bin/env python3
"""
Deployment Validation Script for SiteGuard AI
Tests key functionality to ensure successful Streamlit Cloud deployment.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")

    try:
        import streamlit as st
        print(f"✅ Streamlit {st.__version__}")

        import cv2
        print(f"✅ OpenCV {cv2.__version__}")

        from ultralytics import YOLO
        print("✅ Ultralytics YOLO")

        import torch
        print(f"✅ PyTorch {torch.__version__}")

        from PIL import Image
        print(f"✅ Pillow {Image.__version__}")

        import numpy as np
        print(f"✅ NumPy {np.__version__}")

        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_model_loading():
    """Test that the YOLO model can be loaded."""
    print("\n🔍 Testing model loading...")

    try:
        from ultralytics import YOLO

        # Test loading the model used in the app
        model_path = "yolo11n.pt"
        if os.path.exists(model_path):
            model = YOLO(model_path)
            print("✅ YOLO11n model loaded successfully")
            return True
        else:
            print(f"❌ Model file not found: {model_path}")
            return False
    except Exception as e:
        print(f"❌ Model loading error: {e}")
        return False

def test_directories():
    """Test that required directories exist."""
    print("\n🔍 Testing directories...")

    required_dirs = ["data/evidence", "data/uploads", "data/outputs"]
    all_exist = True

    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path} - missing")
            all_exist = False

    return all_exist

def test_config():
    """Test configuration loading."""
    print("\n🔍 Testing configuration...")

    try:
        # Add current directory to path for imports
        sys.path.insert(0, str(Path(__file__).parent))

        from utils.config import load_config
        config = load_config()
        print("✅ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🚀 SiteGuard AI - Deployment Validation")
    print("=" * 50)

    tests = [
        ("Imports", test_imports),
        ("Model Loading", test_model_loading),
        ("Directories", test_directories),
        ("Configuration", test_config),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 50)
    print("📊 VALIDATION RESULTS:")

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Ready for deployment!")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - Check issues before deployment")
        return 1

if __name__ == "__main__":
    sys.exit(main())