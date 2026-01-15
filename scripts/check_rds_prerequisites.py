#!/usr/bin/env python3
"""
Check prerequisites for AWS RDS setup
Verifies all required packages and tools are installed
"""

import sys
import subprocess

def check_python_version():
    """Check Python version is 3.10+"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} (need 3.10+)")
        return False

def check_package(package_name, import_name=None):
    """Check if a Python package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"✓ {package_name}")
        return True
    except ImportError:
        print(f"✗ {package_name} (not installed)")
        return False

def check_pip():
    """Check if pip is available"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✓ pip")
            return True
        else:
            print("✗ pip (not available)")
            return False
    except Exception:
        print("✗ pip (not available)")
        return False

def main():
    """Check all prerequisites"""
    print("=" * 60)
    print("AWS RDS Setup - Prerequisites Check")
    print("=" * 60)
    
    print("\n1. Checking Python version...")
    print("-" * 60)
    python_ok = check_python_version()
    
    print("\n2. Checking pip...")
    print("-" * 60)
    pip_ok = check_pip()
    
    print("\n3. Checking required packages...")
    print("-" * 60)
    
    packages = [
        ("psycopg2-binary", "psycopg2"),
        ("sqlalchemy", "sqlalchemy"),
        ("python-dotenv", "dotenv"),
        ("requests", "requests"),
    ]
    
    missing_packages = []
    for package_name, import_name in packages:
        if not check_package(package_name, import_name):
            missing_packages.append(package_name)
    
    print("\n" + "=" * 60)
    
    if python_ok and pip_ok and not missing_packages:
        print("✓ All prerequisites met!")
        print("=" * 60)
        print("\nYou're ready to set up AWS RDS PostgreSQL.")
        print("\nNext steps:")
        print("  1. Read: scripts/RDS_QUICK_START.md")
        print("  2. Run: python scripts/get_public_ip.py")
        print("  3. Create RDS instance in AWS Console")
        print("  4. Run: python scripts/generate_database_url.py")
        print("  5. Run: python scripts/validate_rds_connection.py")
        return 0
    else:
        print("✗ Some prerequisites are missing")
        print("=" * 60)
        
        if not python_ok:
            print("\n⚠ Python 3.10+ required")
            print("  Download from: https://www.python.org/downloads/")
        
        if not pip_ok:
            print("\n⚠ pip is not available")
            print("  Install pip: python -m ensurepip --upgrade")
        
        if missing_packages:
            print("\n⚠ Missing Python packages:")
            print(f"  Install with: pip install {' '.join(missing_packages)}")
            print("\n  Or install all at once:")
            print("  pip install psycopg2-binary sqlalchemy python-dotenv requests")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
