#!/usr/bin/env python3
"""
ONVIF Camera Discovery and RTSP URL Retrieval Script
Scans network for ONVIF cameras, prompts for credentials, and retrieves RTSP URLs.
"""

import sys
import os
from pathlib import Path
import argparse

# Add project root to path so we can import app modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
import threading
import time
from typing import Dict, List, Optional
import getpass

from app.core.vision.rtsp_onvif import ONVIFDiscovery, RTSPCamera
from loguru import logger


def scan_network_connectivity(network_range: str, timeout: float = 1.0) -> List[str]:
    """
    Scan network for active devices by attempting basic connectivity.

    Args:
        network_range: Network range to scan (e.g., "192.168.1.0/24")
        timeout: Timeout for each connection attempt

    Returns:
        List of IP addresses that responded
    """
    active_ips = []

    try:
        # Parse network range
        base_ip, subnet = network_range.split('/')
        subnet = int(subnet)

        # Calculate network range
        ip_parts = base_ip.split('.')
        base = (int(ip_parts[0]) << 24) | (int(ip_parts[1]) << 16) | (int(ip_parts[2]) << 8) | int(ip_parts[3])
        mask = (0xFFFFFFFF << (32 - subnet)) & 0xFFFFFFFF
        network = base & mask
        broadcast = network | (~mask & 0xFFFFFFFF)

        # Scan IP range (skip network and broadcast addresses)
        for ip_int in range(network + 1, broadcast):
            ip = f"{(ip_int >> 24) & 0xFF}.{(ip_int >> 16) & 0xFF}.{(ip_int >> 8) & 0xFF}.{ip_int & 0xFF}"

            # Try to connect to common camera ports
            for port in [554, 80, 8080]:  # RTSP, HTTP, HTTP-alt
                try:
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout)
                    result = sock.connect_ex((ip, port))
                    sock.close()

                    if result == 0:  # Connection successful
                        if ip not in active_ips:
                            active_ips.append(ip)
                        break  # Found one open port, consider device active

                except Exception:
                    continue

    except Exception as e:
        print(f"❌ Network scan error: {str(e)}")

    return active_ips


def discover_onvif_cameras_improved(username: str = 'admin', password: str = 'admin') -> List[Dict]:
    """
    Discover ONVIF cameras using proper WS-Discovery protocol.

    Args:
        username: Camera username for authentication
        password: Camera password for authentication

    Returns:
        List of discovered camera dictionaries
    """
    try:
        # Import the improved discovery class
        import sys
        import os
        sys.path.insert(0, os.path.dirname(__file__))
        from discovery import ONVIFDiscovery

        discovery = ONVIFDiscovery()
        cameras = discovery.discover_cameras(timeout=10)

        # Convert to the expected format and try to get RTSP URLs
        formatted_cameras = []
        for cam in cameras:
            camera_info = {
                'ip': cam['ip'],
                'port': cam['port'],
                'name': cam['name'],
                'manufacturer': cam.get('manufacturer', 'Unknown'),
                'model': cam.get('model', 'Unknown'),
                'url': cam.get('url', f"http://{cam['ip']}:{cam['port']}/onvif/device_service")
            }

            # Try to get detailed camera info including RTSP URLs
            try:
                print(f"🔍 Getting detailed info for {cam['ip']}:{cam['port']}...")
                detailed_info = discovery.get_camera_info(cam['ip'], cam['port'], username, password)

                if detailed_info and 'stream_uris' in detailed_info and detailed_info['stream_uris']:
                    camera_info['rtsp_url'] = detailed_info['stream_uris'][0]
                    camera_info['manufacturer'] = detailed_info.get('manufacturer', camera_info['manufacturer'])
                    camera_info['model'] = detailed_info.get('model', camera_info['model'])
                    print(f"✅ Got RTSP URL: {camera_info['rtsp_url']}")
                else:
                    print(f"❌ Could not get RTSP URL for {cam['ip']}")
            except Exception as e:
                print(f"❌ Error getting camera info for {cam['ip']}: {str(e)}")

            formatted_cameras.append(camera_info)

        return formatted_cameras

    except Exception as e:
        print(f"❌ Improved discovery failed: {str(e)}")
        print("Falling back to basic network scan...")
        return discover_onvif_cameras_basic()


def discover_onvif_cameras_basic(network_ranges: List[str] = None) -> List[Dict]:
    """
    Basic ONVIF camera discovery using network scanning (fallback method).

    Args:
        network_ranges: List of network ranges to scan

    Returns:
        List of discovered camera dictionaries
    """
    if network_ranges is None:
        network_ranges = [
            "192.168.1.0/24",
            "192.168.0.0/24",
            "10.0.0.0/24",
            "172.16.0.0/24",
        ]

    all_cameras = []

    for network_range in network_ranges:
        print(f"🔍 Scanning network {network_range} for ONVIF cameras...")
        print("This may take a few minutes depending on your network size...\n")

        # First, let's do a basic connectivity scan to see which IPs respond
        print("📡 Checking network connectivity...")
        active_ips = scan_network_connectivity(network_range)
        if active_ips:
            print(f"✅ Found {len(active_ips)} active devices: {', '.join(active_ips[:10])}{'...' if len(active_ips) > 10 else ''}")
        else:
            print("❌ No active devices found on this network range")
        print()

        try:
            discovery = ONVIFDiscovery()
            cameras = discovery.discover_cameras(network_range)

            if cameras:
                print(f"✅ Found {len(cameras)} ONVIF camera(s) on {network_range}:")
                for i, cam in enumerate(cameras, 1):
                    print(f"   {i}. {cam.get('name', 'Unknown')} ({cam.get('ip', 'Unknown IP')})")
                print()
                all_cameras.extend(cameras)
            else:
                print(f"❌ No ONVIF cameras found on {network_range}")
                if active_ips:
                    print("💡 Active devices found but no ONVIF cameras detected.")
                    print("   This might mean cameras are not ONVIF-compliant or discovery is disabled.")
                print()

        except Exception as e:
            print(f"❌ Error scanning {network_range}: {str(e)}\n")

    return all_cameras


# Keep the original function for backward compatibility but use improved method
def discover_onvif_cameras(network_ranges: List[str] = None, username: str = 'admin', password: str = 'admin') -> List[Dict]:
    """
    Discover ONVIF cameras on the network.

    This function now uses improved WS-Discovery protocol for better camera detection.

    Args:
        network_ranges: List of network ranges to scan (for backward compatibility)
        username: Camera username for authentication
        password: Camera password for authentication

    Returns:
        List of discovered camera dictionaries
    """
    print("🎥 Using improved ONVIF discovery with WS-Discovery protocol...")
    return discover_onvif_cameras_improved(username, password)


def setup_logging(verbose: bool = False):
    """Setup basic logging for the script."""
    logger.remove()  # Remove default handler

    level = "DEBUG" if verbose else "INFO"

    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level
    )


def prompt_credentials() -> tuple[str, str]:
    """
    Prompt user for camera credentials.

    Returns:
        Tuple of (username, password)
    """
    print("\n🔐 Camera Credentials Required")
    print("-" * 40)

    username = input("Enter camera username (default: admin): ").strip()
    if not username:
        username = "admin"

    password = getpass.getpass("Enter camera password: ")

    return username, password


def test_camera_credentials(camera: Dict, username: str, password: str) -> Optional[str]:
    """
    Test camera credentials and retrieve RTSP URL.

    Args:
        camera: Camera dictionary from discovery
        username: Camera username
        password: Camera password

    Returns:
        RTSP URL if successful, None if failed
    """
    rtsp_url = camera.get('rtsp_url')
    if not rtsp_url:
        print(f"❌ No RTSP URL available for camera {camera.get('name', 'Unknown')}")
        return None

    print(f"🔍 Testing RTSP connection to: {rtsp_url}")

    try:
        rtsp_camera = RTSPCamera(rtsp_url, username, password)
        connected = rtsp_camera.connect()

        if connected and rtsp_camera.cap and rtsp_camera.cap.isOpened():
            print("✅ RTSP connection successful!")
            rtsp_camera.cap.release()
            return rtsp_url
        else:
            print("❌ RTSP connection failed - invalid credentials or camera offline")
            return None

    except Exception as e:
        print(f"❌ RTSP connection error: {str(e)}")
        return None


def main(verbose: bool = False, network_range: str = None):
    """Main function."""
    setup_logging(verbose)

    print("🎥 ONVIF Camera Discovery and RTSP URL Retrieval")
    print("=" * 55)
    print()

    # Ask user if they want to manually enter camera IPs
    print("Discovery Method:")
    print("-" * 17)
    discovery_method = input("Choose method - (A)uto-discover or (M)anual entry [A]: ").strip().upper()

    cameras = []

    if discovery_method == "M":
        # Manual entry mode
        print("\n📝 Manual Camera Entry Mode")
        print("-" * 30)
        print("Enter camera details. Leave IP blank to finish.")

        while True:
            ip = input("\nCamera IP address: ").strip()
            if not ip:
                break

            username = input("Username (default: admin): ").strip() or "admin"
            password = getpass.getpass("Password: ")
            port = input("RTSP port (default: 554): ").strip() or "554"
            stream_path = input("Stream path (default: /stream): ").strip() or "/stream"

            rtsp_url = f"rtsp://{username}:{password}@{ip}:{port}{stream_path}"

            # Test the RTSP connection
            print(f"\n🔍 Testing RTSP connection to: rtsp://{username}:***@{ip}:{port}{stream_path}")
            try:
                rtsp_camera = RTSPCamera(rtsp_url, username, password)
                connected = rtsp_camera.connect()

                if connected and rtsp_camera.cap and rtsp_camera.cap.isOpened():
                    print("✅ RTSP connection successful!")
                    rtsp_camera.cap.release()

                    cameras.append({
                        'ip': ip,
                        'port': int(port),
                        'name': f"Manual Camera ({ip})",
                        'manufacturer': 'Unknown',
                        'model': 'Unknown',
                        'rtsp_url': rtsp_url,
                        'mac_address': 'Unknown'
                    })
                else:
                    print("❌ RTSP connection failed - check credentials and URL")

            except Exception as e:
                print(f"❌ RTSP connection error: {str(e)}")

    else:
        # Auto-discovery mode
        print("\n🔍 Auto-Discovery Mode")
        print("-" * 22)

        # Check if network range was provided via command line
        if network_range:
            network_ranges = [network_range]
            print(f"🔍 Will scan network range from command line: {network_range}")
        else:
            # Ask user for custom network range
            print("Network Configuration:")
            print("-" * 25)
            custom_range = input("Enter network range to scan (or press Enter for auto-scan): ").strip()

            if custom_range:
                # Use custom range
                network_ranges = [custom_range]
                print(f"🔍 Will scan custom network range: {custom_range}")
            else:
                # Use default ranges
                network_ranges = None  # Will use the default list in discover_onvif_cameras
                print("🔍 Will scan common network ranges automatically:")
                print("   - 192.168.1.0/24 (most common)")
                print("   - 192.168.0.0/24 (alternative)")
                print("   - 10.0.0.0/24 (enterprise)")
                print("   - 172.16.0.0/24 (private)")

        print("\n" + "=" * 55)

        # Prompt for credentials BEFORE discovery (needed for RTSP URL retrieval)
        print("\n🔐 Camera Credentials Required")
        print("-" * 32)
        username = input("Enter camera username (default: admin): ").strip() or "admin"
        password = getpass.getpass("Enter camera password: ")

        # Discover cameras via ONVIF with credentials
        cameras = discover_onvif_cameras(network_ranges, username, password)

    # If no cameras found, offer manual entry as fallback
    if not cameras and discovery_method != "M":
        print("\n❌ No cameras found via auto-discovery.")
        manual_fallback = input("Would you like to manually enter camera details? (y/N): ").strip().lower()
        if manual_fallback == 'y':
            print("\n📝 Manual Camera Entry Mode")
            print("-" * 30)
            print("Enter camera details. Leave IP blank to finish.")

            while True:
                ip = input("\nCamera IP address: ").strip()
                if not ip:
                    break

                username = input("Username (default: admin): ").strip() or "admin"
                password = getpass.getpass("Password: ")
                port = input("RTSP port (default: 554): ").strip() or "554"
                stream_path = input("Stream path (default: /stream): ").strip() or "/stream"

                rtsp_url = f"rtsp://{username}:{password}@{ip}:{port}{stream_path}"

                # Test the RTSP connection
                print(f"\n🔍 Testing RTSP connection to: rtsp://{username}:***@{ip}:{port}{stream_path}")
                try:
                    rtsp_camera = RTSPCamera(rtsp_url, username, password)
                    connected = rtsp_camera.connect()

                    if connected and rtsp_camera.cap and rtsp_camera.cap.isOpened():
                        print("✅ RTSP connection successful!")
                        rtsp_camera.cap.release()

                        cameras.append({
                            'ip': ip,
                            'port': int(port),
                            'name': f"Manual Camera ({ip})",
                            'manufacturer': 'Unknown',
                            'model': 'Unknown',
                            'rtsp_url': rtsp_url,
                            'mac_address': 'Unknown'
                        })
                    else:
                        print("❌ RTSP connection failed - check credentials and URL")

                except Exception as e:
                    print(f"❌ RTSP connection error: {str(e)}")

    if not cameras:
        print("\n❌ No cameras found or configured.")
        print("\nTroubleshooting tips:")
        print("- Check if cameras are powered on and connected to the network")
        print("- Verify camera IP addresses and credentials")
        print("- Try manual entry mode with known camera details")
        print("- Check firewall settings on your computer and network")
        print("- Ensure cameras are not behind additional routers/firewalls")
        return

    print(f"\n✅ Found {len(cameras)} camera(s) total:")
    print()

    # Display discovered cameras
    for i, camera in enumerate(cameras, 1):
        print(f"{i}. {camera.get('name', 'Unknown')} ({camera.get('ip', 'Unknown IP')})")
        print(f"   Port: {camera.get('port', 'Unknown')}")
        print(f"   RTSP URL: {camera.get('rtsp_url', 'Not available')}")
        print()

    # For cameras that already have RTSP URLs (from improved discovery), consider them successful
    cameras_with_rtsp = [c for c in cameras if c.get('rtsp_url') and c.get('rtsp_url') != 'Not available']
    cameras_without_rtsp = [c for c in cameras if not c.get('rtsp_url') or c.get('rtsp_url') == 'Not available']

    successful_cameras = []

    # Add cameras that already have RTSP URLs
    for camera in cameras_with_rtsp:
        successful_cameras.append({
            'name': camera.get('name', 'Unknown'),
            'ip': camera.get('ip', 'Unknown'),
            'rtsp_url': camera['rtsp_url'],
            'username': username,
            'password': password
        })

    # Test cameras that don't have RTSP URLs yet
    if cameras_without_rtsp:
        print(f"\n🔧 Testing credentials for {len(cameras_without_rtsp)} camera(s) without RTSP URLs...")
        print("-" * 60)

        for i, camera in enumerate(cameras_without_rtsp, 1):
            print(f"\n📹 Camera {i}: {camera.get('name', 'Unknown')}")
            rtsp_url = test_camera_credentials(camera, username, password)

            if rtsp_url:
                successful_cameras.append({
                    'name': camera.get('name', 'Unknown'),
                    'ip': camera.get('ip', 'Unknown'),
                    'rtsp_url': rtsp_url,
                    'username': username,
                    'password': password
                })

    # Results
    print(f"\n🎯 Results Summary")
    print("=" * 20)
    print(f"Discovered cameras: {len(cameras)}")
    print(f"Successful connections: {len(successful_cameras)}")

    if successful_cameras:
        print(f"\n✅ Successfully connected to {len(successful_cameras)} camera(s):")
        print("-" * 60)

        for camera in successful_cameras:
            print(f"📹 {camera['name']} ({camera['ip']})")
            print(f"   RTSP URL: {camera['rtsp_url']}")
            print(f"   Username: {camera['username']}")
            print(f"   Password: {'*' * len(camera['password'])}")
            print()

        print("💡 You can now use these RTSP URLs in your SiteGuard AI application!")
        print("   Go to the 'Live Webcam Detection' tab and select 'RTSP Stream'.")
    else:
        print("\n❌ No cameras could be accessed with the provided credentials.")
        print("Troubleshooting tips:")
        print("- Verify username and password are correct")
        print("- Check if cameras require different credentials")
        print("- Ensure cameras are not behind additional firewalls")
        print("- Try accessing camera web interface directly")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ONVIF Camera Discovery and RTSP URL Retrieval")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("-n", "--network", help="Specific network range to scan (e.g., '192.168.0.0/24')")

    args = parser.parse_args()

    try:
        main(verbose=args.verbose, network_range=args.network)
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        if args.verbose:
            logger.exception("Unexpected error in main()")