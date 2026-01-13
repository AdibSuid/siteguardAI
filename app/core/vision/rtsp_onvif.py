"""
RTSP and ONVIF Camera Discovery Module
Supports RTSP streaming and ONVIF camera discovery for IP cameras.
"""

import cv2
import requests
import socket
import threading
import time
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, urlunparse
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)


class RTSPCamera:
    """RTSP Camera class for handling RTSP streams."""

    def __init__(self, url: str, username: str = "", password: str = ""):
        self.url = url
        self.username = username
        self.password = password
        self.cap = None
        self.is_connected = False

    def connect(self) -> bool:
        """Connect to RTSP stream."""
        try:
            # Build RTSP URL with credentials if provided
            if self.username and self.password:
                parsed = urlparse(self.url)
                self.auth_url = urlunparse(parsed._replace(
                    netloc=f"{self.username}:{self.password}@{parsed.hostname}:{parsed.port or 554}"
                ))
            else:
                self.auth_url = self.url

            self.cap = cv2.VideoCapture(self.auth_url, cv2.CAP_FFMPEG)
            # Check if cap is actually a VideoCapture object (not a boolean)
            if self.cap is not None and hasattr(self.cap, 'isOpened') and self.cap.isOpened():
                self.is_connected = True
                logger.info(f"✅ Connected to RTSP stream: {self.url}")
                return True
            else:
                logger.error(f"❌ Failed to connect to RTSP stream: {self.url}")
                if self.cap:
                    self.cap.release()
                self.cap = None
                return False
        except Exception as e:
            logger.error(f"❌ RTSP connection error: {e}")
            if self.cap:
                self.cap.release()
            self.cap = None
            return False

    def disconnect(self):
        """Disconnect from RTSP stream."""
        if self.cap:
            self.cap.release()
            self.cap = None
        self.is_connected = False

    def read_frame(self) -> Tuple[bool, Optional['numpy.ndarray']]:
        """Read a frame from the RTSP stream."""
        if not self.is_connected or not self.cap:
            return False, None
        return self.cap.read()

    def is_opened(self) -> bool:
        """Check if RTSP stream is opened."""
        return self.is_connected and self.cap is not None and hasattr(self.cap, 'isOpened') and self.cap.isOpened()


class ONVIFDiscovery:
    """ONVIF camera discovery class."""

    def __init__(self):
        self.discovered_cameras = []
        self.discovery_timeout = 5

    def discover_cameras(self, network_range: str = "192.168.1.0/24") -> List[Dict]:
        """
        Discover ONVIF cameras on the network.

        Args:
            network_range: Network range to scan (e.g., "192.168.1.0/24")

        Returns:
            List of discovered camera dictionaries
        """
        self.discovered_cameras = []

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

            # Scan IP range
            threads = []
            for ip_int in range(network + 1, broadcast):
                ip = f"{(ip_int >> 24) & 0xFF}.{(ip_int >> 16) & 0xFF}.{(ip_int >> 8) & 0xFF}.{ip_int & 0xFF}"
                thread = threading.Thread(target=self._check_onvif_device, args=(ip,))
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=self.discovery_timeout)

        except Exception as e:
            logger.error(f"❌ ONVIF discovery error: {e}")

        return self.discovered_cameras

    def _check_onvif_device(self, ip: str):
        """Check if IP address hosts an ONVIF device."""
        try:
            # Common ONVIF ports
            ports = [80, 8080, 8000, 554]

            for port in ports:
                try:
                    # Try to get ONVIF device information
                    device_url = f"http://{ip}:{port}/onvif/device_service"
                    logger.debug(f"Checking {device_url}")
                    response = requests.get(device_url, timeout=2)

                    if response.status_code == 200:
                        logger.info(f"Found potential ONVIF device at {ip}:{port}")
                        # Try to get device info
                        device_info = self._get_onvif_device_info(ip, port)
                        if device_info:
                            logger.info(f"Successfully discovered camera: {device_info['name']} at {ip}:{port}")
                            self.discovered_cameras.append(device_info)
                            break
                    else:
                        logger.debug(f"No ONVIF service at {ip}:{port} (status: {response.status_code})")

                except requests.RequestException as e:
                    logger.debug(f"Connection failed to {ip}:{port}: {e}")
                    continue

        except Exception as e:
            logger.debug(f"Error checking {ip}: {e}")

    def _get_onvif_device_info(self, ip: str, port: int) -> Optional[Dict]:
        """Get ONVIF device information."""
        try:
            # This is a simplified ONVIF device info retrieval
            # In a full implementation, you'd use the onvif library
            device_info = {
                'ip': ip,
                'port': port,
                'name': f"ONVIF Camera ({ip}:{port})",
                'manufacturer': 'Unknown',
                'model': 'Unknown',
                'rtsp_url': f"rtsp://{ip}:554/live",
                'mac_address': 'Unknown'
            }
            return device_info
        except Exception as e:
            logger.debug(f"Error getting device info for {ip}:{port}: {e}")
            return None

    def test_rtsp_credentials(self, rtsp_url: str, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        Test RTSP credentials and return the working RTSP URL.

        Args:
            rtsp_url: Base RTSP URL
            username: Username to test
            password: Password to test

        Returns:
            Tuple of (success, working_rtsp_url)
        """
        try:
            camera = RTSPCamera(rtsp_url, username, password)
            if camera.connect():
                camera.disconnect()
                return True, camera.auth_url
            else:
                return False, None
        except Exception as e:
            logger.error(f"❌ RTSP credential test error: {e}")
            return False, None


def discover_cameras() -> Dict[str, List]:
    """
    Discover all available cameras (webcam + ONVIF).

    Returns:
        Dictionary with 'webcam' and 'onvif' camera lists
    """
    cameras = {
        'webcam': [],
        'onvif': []
    }

    # Discover webcam devices
    for i in range(5):  # Check first 5 camera indices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cameras['webcam'].append({
                'name': f"Camera {i}",
                'index': i,
                'type': 'webcam'
            })
            cap.release()

    # Discover ONVIF cameras using improved WS-Discovery method
    try:
        # Import the improved discovery class
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

        from scripts.discovery import ONVIFDiscovery

        discovery = ONVIFDiscovery()
        onvif_cameras = discovery.discover_cameras(timeout=10)

        # Convert to the expected format for the Streamlit app
        formatted_cameras = []
        for cam in onvif_cameras:
            formatted_cameras.append({
                'name': cam['name'],
                'ip': cam['ip'],
                'port': cam['port'],
                'type': 'onvif',
                'rtsp_url': cam.get('url', f"rtsp://admin:admin@{cam['ip']}:554/stream1"),  # Default RTSP URL
                'manufacturer': cam.get('manufacturer', 'Unknown'),
                'model': cam.get('model', 'Unknown')
            })

        cameras['onvif'] = formatted_cameras
        logger.info(f"Found {len(formatted_cameras)} ONVIF cameras")

    except Exception as e:
        logger.warning(f"ONVIF discovery failed: {e}")
        # Fallback to empty list
        cameras['onvif'] = []

    return cameras


def create_camera_stream(camera_config: Dict) -> Optional[RTSPCamera]:
    """
    Create a camera stream from configuration.

    Args:
        camera_config: Camera configuration dictionary

    Returns:
        RTSPCamera instance or None
    """
    try:
        if camera_config.get('type') == 'webcam':
            # For webcam, we'll handle it differently in the main loop
            return None
        elif camera_config.get('type') == 'rtsp':
            return RTSPCamera(
                camera_config['rtsp_url'],
                camera_config.get('username', ''),
                camera_config.get('password', '')
            )
        elif camera_config.get('type') == 'onvif':
            # ONVIF cameras typically use RTSP
            return RTSPCamera(
                camera_config['rtsp_url'],
                camera_config.get('username', ''),
                camera_config.get('password', '')
            )
    except Exception as e:
        logger.error(f"❌ Failed to create camera stream: {e}")
        return None

    return None