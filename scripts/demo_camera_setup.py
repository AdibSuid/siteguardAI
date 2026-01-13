#!/usr/bin/env python3
"""
Demo script showing how to manually add the known camera
"""

import sys
from pathlib import Path

# Add project root to path so we can import app modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.vision.rtsp_onvif import RTSPCamera

def demo_manual_camera_entry():
    """Demo of manually adding the known camera."""

    print("🎥 SiteGuard AI - Manual Camera Configuration Demo")
    print("=" * 55)
    print()

    # Known camera details
    cameras = [
        {
            'ip': '192.168.1.102',
            'username': 'orinnano',
            'password': 'orinnano',
            'port': '554',
            'stream_path': '/stream1'
        }
    ]

    print("📋 Cameras to configure:")
    for i, cam in enumerate(cameras, 1):
        print(f"   {i}. IP: {cam['ip']}, Port: {cam['port']}, Stream: {cam['stream_path']}")
    print()

    successful_cameras = []

    for cam in cameras:
        ip = cam['ip']
        username = cam['username']
        password = cam['password']
        port = cam['port']
        stream_path = cam['stream_path']

        rtsp_url = f"rtsp://{username}:{password}@{ip}:{port}{stream_path}"

        print(f"🔍 Testing camera: {ip}")
        print(f"   RTSP URL: rtsp://{username}:***@{ip}:{port}{stream_path}")

        try:
            rtsp_camera = RTSPCamera(rtsp_url, username, password)
            connected = rtsp_camera.connect()

            if connected and rtsp_camera.cap and rtsp_camera.cap.isOpened():
                print("✅ RTSP connection successful!")
                rtsp_camera.cap.release()

                successful_cameras.append({
                    'name': f"Camera ({ip})",
                    'ip': ip,
                    'rtsp_url': rtsp_url,
                    'username': username,
                    'password': password
                })
            else:
                print("❌ RTSP connection failed")

        except Exception as e:
            print(f"❌ RTSP connection error: {str(e)}")

    print(f"\n🎯 Results: {len(successful_cameras)}/{len(cameras)} cameras configured successfully")

    if successful_cameras:
        print("\n✅ Successfully configured cameras:")
        print("-" * 40)

        for camera in successful_cameras:
            print(f"📹 {camera['name']}")
            print(f"   RTSP URL: {camera['rtsp_url']}")
            print(f"   Username: {camera['username']}")
            print(f"   Password: {'*' * len(camera['password'])}")
            print()

        print("💡 You can now use these RTSP URLs in your SiteGuard AI application!")
        print("   1. Start the application: streamlit run app/web/streamlit_app_enhanced.py")
        print("   2. Go to the 'Live Webcam Detection' tab")
        print("   3. Select 'RTSP Stream' from the Camera Type dropdown")
        print("   4. Enter the RTSP URL and credentials")
    else:
        print("\n❌ No cameras could be configured.")

if __name__ == "__main__":
    demo_manual_camera_entry()