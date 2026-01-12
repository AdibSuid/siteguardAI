"""
Run the Streamlit web application
"""

import sys
from pathlib import Path
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """Run the Streamlit app."""
    app_path = Path(__file__).parent.parent / "app" / "web" / "streamlit_app.py"
    
    print("Starting SiteGuard AI Web Dashboard...")
    print(f"App path: {app_path}")
    
    subprocess.run([
        "streamlit",
        "run",
        str(app_path),
        "--server.port=8501",
        "--server.address=localhost"
    ])


if __name__ == "__main__":
    main()
