"""
SiteGuard AI - Enhanced Streamlit Web Application
Interactive dashboard for PPE detection with Live Webcam, Analytics, and Dark Mode
"""

import sys
from pathlib import Path
import streamlit as st
import cv2
import numpy as np
from PIL import Image
from datetime import datetime, timedelta
import json
import io
import time
from collections import defaultdict
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Debug logging
print("🔍 Starting SiteGuard AI application...")
print(f"Python version: {sys.version}")
print(f"Current working directory: {Path.cwd()}")

from app.core.vision.detector import PPEDetector, create_detector
from app.core.llm.generator import ReportGenerator, ReportMetadata, ReportFormat, create_report_generator
from app.core.notification import create_telegram_notifier
from app.core.vision.rtsp_onvif import RTSPCamera, ONVIFDiscovery
from utils.config import load_config
from loguru import logger

print("✅ Imports completed successfully")


# Working ONVIF Discovery Implementation
from onvif import ONVIFCamera
from zeep.exceptions import Fault
import socket
import threading
import time
import uuid
import re
import concurrent.futures
from typing import List, Dict, Optional

class WorkingONVIFDiscovery:
    """ONVIF camera discovery and management with WS-Discovery"""

    COMMON_ONVIF_PORTS = [2020, 80, 8080, 8000, 8899, 10080]

    def __init__(self):
        self.discovered_cameras = []
        self.discovery_lock = threading.Lock()

    def discover_cameras(self, timeout=5):
        """
        Discover ONVIF cameras on local network

        Args:
            timeout: Discovery timeout in seconds

        Returns:
            list: List of discovered camera dictionaries
        """
        print(f"[*] Starting ONVIF camera discovery (timeout: {timeout}s)...")

        self.discovered_cameras = []

        # Try WS-Discovery first
        discovery_thread = threading.Thread(
            target=self._ws_discovery,
            args=(timeout,),
            daemon=True
        )
        discovery_thread.start()
        discovery_thread.join(timeout + 1)

        # If WS-Discovery failed, use network scan
        if len(self.discovered_cameras) == 0:
            print("[*] WS-Discovery failed, attempting network scan...")
            scanned_cameras = self._scan_local_network()
            with self.discovery_lock:
                self.discovered_cameras.extend(scanned_cameras)

        print(f"[+] Found {len(self.discovered_cameras)} camera(s)")
        return self.discovered_cameras

    def _ws_discovery(self, timeout):
        """Perform WS-Discovery on local network"""
        import xml.etree.ElementTree as ET

        # WS-Discovery probe message
        probe_msg = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" '
            'xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing">'
            '<s:Header>'
            '<a:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</a:Action>'
            '<a:MessageID>uuid:' + str(uuid.uuid4()) + '</a:MessageID>'
            '<a:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</a:To>'
            '</s:Header>'
            '<s:Body>'
            '<Probe xmlns="http://schemas.xmlsoap.org/ws/2005/04/discovery">'
            '<d:Types xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery" '
            'xmlns:dp0="http://www.onvif.org/ver10/network/wsdl">dp0:NetworkVideoTransmitter</d:Types>'
            '</Probe>'
            '</s:Body>'
            '</s:Envelope>'
        ).encode('utf-8')

        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(timeout)

        # Multicast address for WS-Discovery
        multicast_addr = ('239.255.255.250', 3702)

        try:
            # Send probe
            sock.sendto(probe_msg, multicast_addr)

            # Also try broadcast
            try:
                sock.sendto(probe_msg, ('255.255.255.255', 3702))
            except:
                pass

            # Receive responses
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    data, addr = sock.recvfrom(65536)
                    self._parse_probe_match(data, addr[0])
                except socket.timeout:
                    break
                except Exception as e:
                    pass

        finally:
            sock.close()

    def _parse_probe_match(self, data, ip):
        """Parse WS-Discovery probe match response"""
        try:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(data.decode('utf-8'))

            # Extract XAddrs (camera URLs)
            namespaces = {
                'soap': 'http://www.w3.org/2003/05/soap-envelope',
                'd': 'http://schemas.xmlsoap.org/ws/2005/04/discovery'
            }

            xaddrs = root.find('.//d:XAddrs', namespaces)
            if xaddrs is not None and xaddrs.text:
                urls = xaddrs.text.split()
                url = urls[0] if urls else None

                # Extract port from URL
                port = 80
                if url:
                    port_match = re.search(r':(\d+)/', url)
                    if port_match:
                        port = int(port_match.group(1))

                with self.discovery_lock:
                    # Check if already discovered
                    if not any(cam['ip'] == ip for cam in self.discovered_cameras):
                        self.discovered_cameras.append({
                            'ip': ip,
                            'port': port,
                            'url': url or f'http://{ip}:{port}/onvif/device_service',
                            'name': f"Camera {ip}",
                            'manufacturer': 'Unknown',
                            'model': 'Unknown'
                        })

        except Exception as e:
            pass

    def _scan_local_network(self) -> List[Dict]:
        """Scan local network for ONVIF devices on common ports"""
        cameras = []

        try:
            # Get local IP and subnet
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()

            # Calculate network range (assuming /24)
            ip_parts = local_ip.split('.')
            network_prefix = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"

            # Specific camera IPs to check first
            camera_ips = [
                ('192.168.1.102', 2020),
                ('192.168.1.103', 2020),
                ('192.168.1.113', 8080),
                ('192.168.1.133', 2020)
            ]

            print(f"[*] Checking known camera addresses...")
            for ip, port in camera_ips:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1.0)
                    result = sock.connect_ex((ip, port))
                    sock.close()
                    if result == 0:
                        cameras.append({
                            'ip': ip,
                            'port': port,
                            'url': f'http://{ip}:{port}/onvif/device_service',
                            'name': f'Camera {ip}',
                            'manufacturer': 'Unknown',
                            'model': 'Unknown'
                        })
                        print(f"[+] Found camera at {ip}:{port}")
                except:
                    pass

            # If fewer than 4 cameras found, do a full network scan
            if len(cameras) < 4:
                print(f"[*] Scanning {network_prefix}.1-254 on common ports...")

                def check_onvif(ip, port):
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(0.5)
                        result = sock.connect_ex((ip, port))
                        sock.close()
                        if result == 0:
                            return (ip, port)
                    except:
                        pass
                    return None

                with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                    futures = []
                    for i in range(1, 255):
                        ip = f"{network_prefix}.{i}"
                        # Skip already found IPs
                        if any(c['ip'] == ip for c in cameras):
                            continue
                        for port in self.COMMON_ONVIF_PORTS:
                            futures.append(executor.submit(check_onvif, ip, port))

                    for future in concurrent.futures.as_completed(futures):
                        result = future.result()
                        if result:
                            ip, port = result
                            if (ip, port) not in [(c['ip'], c['port']) for c in cameras]:
                                # Only add if port is 2020, 8080, or 8000 (common camera ports)
                                if port in [2020, 8080, 8000]:
                                    cameras.append({
                                        'ip': ip,
                                        'port': port,
                                        'url': f'http://{ip}:{port}/onvif/device_service',
                                        'name': f'Camera {ip}',
                                        'manufacturer': 'Unknown',
                                        'model': 'Unknown'
                                    })
                                    print(f"[+] Found camera at {ip}:{port}")

        except Exception as e:
            print(f"[!] Network scan error: {e}")

        return cameras

    def get_camera_info(self, ip, port=80, user='admin', password='admin'):
        """
        Get detailed camera information via ONVIF

        Args:
            ip: Camera IP address
            port: ONVIF port
            user: Username
            password: Password

        Returns:
            dict: Camera information or error dict on failure
        """
        try:
            # Get WSDL directory from onvif package
            import os
            import onvif
            onvif_dir = os.path.dirname(onvif.__file__)
            wsdl_dir = os.path.join(onvif_dir, 'wsdl')

            print(f"[ONVIF] Connecting to {ip}:{port} with user '{user}'")

            # Create ONVIF camera connection with WSDL files
            if os.path.exists(wsdl_dir):
                print(f"[ONVIF] Using WSDL directory: {wsdl_dir}")
                camera = ONVIFCamera(ip, port, user, password, wsdl_dir=wsdl_dir)
            else:
                print(f"[ONVIF] WSDL not found, trying without WSDL")
                camera = ONVIFCamera(ip, port, user, password)

            # Get device information
            device_service = camera.create_devicemgmt_service()
            device_info = device_service.GetDeviceInformation()

            # Get media profiles
            media_service = camera.create_media_service()
            profiles = media_service.GetProfiles()

            # Get stream URIs with credentials embedded
            stream_uris = []
            profile_details = []

            for profile in profiles:
                try:
                    stream_setup = {
                        'Stream': 'RTP-Unicast',
                        'Transport': {'Protocol': 'RTSP'}
                    }
                    uri = media_service.GetStreamUri({
                        'StreamSetup': stream_setup,
                        'ProfileToken': profile.token
                    })

                    rtsp_url = str(uri.Uri)

                    # Extract suffix and build complete URL with credentials
                    suffix = self._extract_rtsp_suffix(rtsp_url)
                    complete_url = self._build_rtsp_url(ip, user, password, suffix)

                    stream_uris.append(complete_url)

                    profile_info = {
                        'name': str(profile.Name),
                        'token': str(profile.token),
                        'rtsp_url': rtsp_url,
                        'rtsp_suffix': suffix,
                        'complete_url': complete_url
                    }

                    # Try to get resolution
                    try:
                        if hasattr(profile, 'VideoEncoderConfiguration'):
                            video_config = profile.VideoEncoderConfiguration
                            if hasattr(video_config, 'Resolution'):
                                profile_info['resolution'] = {
                                    'width': video_config.Resolution.Width,
                                    'height': video_config.Resolution.Height
                                }
                    except:
                        pass

                    profile_details.append(profile_info)
                except Exception as e:
                    print(f"Failed to get stream URI for profile {profile.token}: {e}")
                    pass

            return {
                'ip': ip,
                'port': port,
                'manufacturer': str(device_info.Manufacturer),
                'model': str(device_info.Model),
                'firmware': str(device_info.FirmwareVersion),
                'serial': str(device_info.SerialNumber),
                'stream_uris': stream_uris,
                'profiles': profile_details
            }

        except Fault as fault:
            # Handle ONVIF SOAP faults
            fault_code = getattr(fault, 'code', '')
            fault_string = getattr(fault, 'message', str(fault))
            print(f"[ONVIF Fault] {fault_code}: {fault_string}")

            # Check for authentication errors
            if 'NotAuthorized' in fault_code or 'NotAuthorized' in fault_string or 'Sender' in fault_code:
                return {
                    'error': 'auth',
                    'message': 'Authentication failed. Please check username and password.',
                    'details': f"{fault_code}: {fault_string}"
                }
            else:
                return {
                    'error': 'onvif_fault',
                    'message': f'ONVIF error: {fault_string}',
                    'details': f"{fault_code}: {fault_string}"
                }
        except Exception as e:
            print(f"[ONVIF] Failed: {e}")
            print(f"[ONVIF] Trying fallback method with common RTSP paths")

            # Try common RTSP URLs as fallback
            return self._try_common_rtsp_urls(ip, user, password)

    def _try_common_rtsp_urls(self, ip, username, password):
        """
        Try common RTSP URL patterns when ONVIF fails

        Args:
            ip: Camera IP address
            username: Username
            password: Password

        Returns:
            dict: Camera info with working RTSP URL or error
        """
        import cv2

        # Common RTSP URL patterns for various camera brands
        common_paths = [
            '/stream1',           # Generic
            '/Streaming/Channels/101',  # Hikvision
            '/cam/realmonitor?channel=1&subtype=0',  # Dahua
            '/live/ch00_0',       # TP-Link
            '/h264Preview_01_main',  # Foscam
            '/video.mp4',         # Generic MP4
            '/media/video1',      # Axis
            '/live.sdp',          # Generic SDP
            '/videoMain',         # Generic
            '/11',                # Some Chinese cameras
            '/1',                 # Simple path
        ]

        print(f"[RTSP Fallback] Testing common RTSP paths for {ip}")

        for path in common_paths:
            for rtsp_port in [554, 8554]:  # Try common RTSP ports
                rtsp_url = f"rtsp://{username}:{password}@{ip}:{rtsp_port}{path}"
                print(f"[RTSP Fallback] Testing: rtsp://{username}:***@{ip}:{rtsp_port}{path}")

                try:
                    cap = cv2.VideoCapture(rtsp_url)
                    # Check if cap is actually a VideoCapture object (not a boolean)
                    if cap is not None and hasattr(cap, 'isOpened'):
                        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 3000)  # 3 second timeout
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                        if cap.isOpened():
                            ret, frame = cap.read()
                            cap.release()

                            if ret and frame is not None:
                                print(f"[RTSP Fallback] Success! Working URL found: {path} on port {rtsp_port}")
                                return {
                                    'ip': ip,
                                    'port': rtsp_port,
                                    'manufacturer': 'Unknown',
                                    'model': 'Unknown (fallback method)',
                                    'firmware': 'Unknown',
                                    'serial': 'Unknown',
                                    'stream_uris': [rtsp_url],
                                    'profiles': [{
                                        'name': 'Main Stream',
                                        'rtsp_url': rtsp_url,
                                        'complete_url': rtsp_url
                                    }]
                                }
                        cap.release()
                    else:
                        # cap is not a valid VideoCapture object
                        pass
                except Exception as e:
                    pass

        # If all attempts failed
        print(f"[RTSP Fallback] All common paths failed for {ip}")
        return {
            'error': 'auth',
            'message': 'Could not find working RTSP stream. Please verify credentials.',
            'details': 'Tried ONVIF and common RTSP paths without success'
        }

    def _extract_rtsp_suffix(self, rtsp_url):
        """Extract the suffix/path from full RTSP URL"""
        import re

        # Remove credentials if present
        url = re.sub(r'rtsp://[^@]+@', 'rtsp://', rtsp_url)

        # Extract path after IP:PORT
        match = re.search(r'rtsp://[^/]+/(.+)', url)
        if match:
            return match.group(1)

        # Return original URL if pattern not matched
        return rtsp_url

    def _build_rtsp_url(self, ip, username, password, suffix, port=554):
        """Build complete RTSP URL with credentials"""
        import re

        # Handle suffix that might already contain port
        if suffix.startswith('rtsp://'):
            # Extract port if present in suffix
            port_match = re.search(r':(\d+)/', suffix)
            if port_match:
                port = int(port_match.group(1))
            # Extract just the path
            suffix = self._extract_rtsp_suffix(suffix)

        # Ensure suffix starts with /
        if not suffix.startswith('/'):
            suffix = '/' + suffix

        # Build URL with credentials
        return f"rtsp://{username}:{password}@{ip}:{port}{suffix}"


# Page configuration
st.set_page_config(
    page_title="SiteGuard AI - Safety Monitoring Pro",
    page_icon="🦺",
    layout="wide",
    initial_sidebar_state="expanded"
)


def get_custom_css(dark_mode=False):
    """Generate custom CSS based on theme."""
    if dark_mode:
        return """
<style>
    /* Dark Industrial Mode Styling - Professional Dark Theme */
    .main {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0f0f0f 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #e0e0e0;
        min-height: 100vh;
    }
    .main-header {
        font-size: 3.2rem;
        font-weight: 900;
        background: linear-gradient(120deg, #00d4ff 0%, #0099cc 50%, #0066cc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 2rem 0;
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
        text-shadow: 0 2px 4px rgba(0,0,0,0.8);
        letter-spacing: -0.02em;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a4e 50%, #1a1a3e 100%);
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid #00d4ff;
        box-shadow: 0 8px 32px rgba(0,212,255,0.15);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        color: #e0e0e0;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #00d4ff, #0099cc, #0066cc);
        box-shadow: 0 0 10px rgba(0,212,255,0.5);
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 40px rgba(0,212,255,0.25);
        border-color: #33e0ff;
    }
    .violation-alert {
        background: linear-gradient(135deg, #2d1b1b 0%, #4a1c1c 100%);
        padding: 2rem;
        border-radius: 12px;
        border-left: 6px solid #ff6b6b;
        margin: 1.5rem 0;
        box-shadow: 0 6px 20px rgba(255,107,107,0.3);
        color: #ffcccc;
        position: relative;
        border: 1px solid rgba(255,107,107,0.3);
    }
    .violation-alert::before {
        content: '🚨';
        position: absolute;
        top: 1rem;
        right: 1rem;
        font-size: 1.5rem;
        opacity: 0.8;
    }
    .success-alert {
        background: linear-gradient(135deg, #1b2d1b 0%, #2d4a2d 100%);
        padding: 2rem;
        border-radius: 12px;
        border-left: 6px solid #51cf66;
        margin: 1.5rem 0;
        box-shadow: 0 6px 20px rgba(81,207,102,0.3);
        color: #ccffcc;
        position: relative;
        border: 1px solid rgba(81,207,102,0.3);
    }
    .success-alert::before {
        content: '✅';
        position: absolute;
        top: 1rem;
        right: 1rem;
        font-size: 1.5rem;
        opacity: 0.8;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #0066cc 0%, #0099cc 50%, #00d4ff 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        font-weight: 700;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(0,102,204,0.4);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        position: relative;
        overflow: hidden;
    }
    .stButton>button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }
    .stButton>button:hover::before {
        left: 100%;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #0099cc 0%, #00d4ff 50%, #33e0ff 100%);
        box-shadow: 0 6px 20px rgba(0,102,204,0.6);
        transform: translateY(-2px);
    }
    .stat-box {
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a4e 100%);
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #00d4ff;
        box-shadow: 0 4px 16px rgba(0,212,255,0.15);
        position: relative;
        color: #e0e0e0;
    }
    .stat-box::before {
        content: '';
        position: absolute;
        top: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 60%;
        height: 2px;
        background: linear-gradient(90deg, transparent, #00d4ff, transparent);
        box-shadow: 0 0 8px rgba(0,212,255,0.6);
    }
    .webcam-frame {
        border: 3px solid #00d4ff;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,212,255,0.3);
        background: rgba(0,212,255,0.05);
        position: relative;
    }
    .webcam-frame::before {
        content: '';
        position: absolute;
        top: -3px;
        left: -3px;
        right: -3px;
        bottom: -3px;
        background: linear-gradient(45deg, #00d4ff, #0099cc, #0066cc, #00d4ff);
        border-radius: 12px;
        z-index: -1;
        opacity: 0.3;
        animation: borderGlow 2s ease-in-out infinite alternate;
    }
    @keyframes borderGlow {
        from { opacity: 0.3; }
        to { opacity: 0.6; }
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
        border-bottom: 1px solid #00d4ff;
        padding: 1rem;
        border-radius: 12px 12px 0 0;
    }
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a4e 100%);
        border-radius: 8px 8px 0 0;
        border: 1px solid #00d4ff;
        border-bottom: none;
        color: #00d4ff;
        font-weight: 600;
        padding: 1rem 1.5rem;
        transition: all 0.3s ease;
        position: relative;
        box-shadow: 0 2px 8px rgba(0,212,255,0.1);
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #2a2a4e 0%, #3a3a6e 100%);
        color: #33e0ff;
        box-shadow: 0 4px 12px rgba(0,212,255,0.2);
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #0066cc 0%, #0099cc 100%);
        color: white;
        box-shadow: 0 4px 16px rgba(0,102,204,0.4);
        border-color: #33e0ff;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"]::before {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #00d4ff, #33e0ff, #00d4ff);
        box-shadow: 0 0 10px rgba(0,212,255,0.8);
    }
    .stMetric {
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a4e 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #00d4ff;
        box-shadow: 0 4px 16px rgba(0,212,255,0.15);
        color: #e0e0e0;
    }
    .stMetric label {
        color: #00d4ff !important;
        font-weight: 600;
    }
    .stMetric .metric-value {
        color: #ffffff !important;
        font-weight: 700;
        font-size: 1.8rem;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #0066cc, #00d4ff, #33e0ff);
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0,212,255,0.5);
    }
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0,212,255,0.15);
        border: 1px solid #00d4ff;
    }
    .stDataFrame > div {
        border-radius: 10px;
    }
    .stDataFrame th {
        background: linear-gradient(135deg, #0066cc 0%, #0099cc 100%);
        color: white;
        font-weight: 600;
        border: none;
    }
    .stDataFrame td {
        border: none;
        color: #e0e0e0;
    }
    .stDataFrame tbody tr:nth-child(even) {
        background: rgba(0,212,255,0.05);
    }
    .stDataFrame tbody tr:hover {
        background: rgba(0,212,255,0.1);
    }
    .stSelectbox, .stMultiselect, .stTextInput, .stNumberInput {
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a4e 100%);
        border: 1px solid #00d4ff;
        border-radius: 8px;
        color: #e0e0e0;
    }
    .stSelectbox:hover, .stMultiselect:hover, .stTextInput:hover, .stNumberInput:hover {
        border-color: #33e0ff;
        box-shadow: 0 0 8px rgba(0,212,255,0.3);
    }
    .stSidebar {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
        border-right: 1px solid #00d4ff;
    }
    .stSidebar .stMarkdown h1, .stSidebar .stMarkdown h2, .stSidebar .stMarkdown h3 {
        color: #00d4ff;
    }
    .stExpander {
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a4e 100%);
        border: 1px solid #00d4ff;
        border-radius: 8px;
        color: #e0e0e0;
    }
    .stExpander:hover {
        border-color: #33e0ff;
        box-shadow: 0 0 8px rgba(0,212,255,0.2);
    }
    .stAlert {
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a4e 100%);
        border: 1px solid #00d4ff;
        border-radius: 8px;
        color: #e0e0e0;
    }
    /* Custom scrollbar for dark mode */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0a0a0a;
    }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #0066cc, #00d4ff);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #0099cc, #33e0ff);
    }
    /* Ensure all text is readable in dark mode */
    .stMarkdown, .stText, p, span, div {
        color: #e0e0e0 !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #00d4ff !important;
    }
    /* Override any bright backgrounds */
    .stTextInput input, .stNumberInput input, .stSelectbox select, .stMultiselect select {
        background-color: #1e1e2e !important;
        color: #e0e0e0 !important;
        border: 1px solid #00d4ff !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus, .stMultiselect select:focus {
        border-color: #33e0ff !important;
        box-shadow: 0 0 8px rgba(0,212,255,0.3) !important;
    }
</style>
"""
    else:
        return """
<style>
    /* Light Industrial Mode Styling */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        min-height: 100vh;
    }
    .main-header {
        font-size: 3.2rem;
        font-weight: 900;
        background: linear-gradient(120deg, #0066cc 0%, #0099cc 50%, #00d4ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 2rem 0;
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        letter-spacing: -0.02em;
    }
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 2rem;
        border-radius: 12px;
        border: 2px solid #e3f2fd;
        border-left: 6px solid #0066cc;
        box-shadow: 0 8px 32px rgba(0,102,204,0.1);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #0066cc, #0099cc, #00d4ff);
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 40px rgba(0,102,204,0.2);
        border-color: #0066cc;
    }
    .violation-alert {
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
        padding: 2rem;
        border-radius: 12px;
        border-left: 6px solid #d32f2f;
        margin: 1.5rem 0;
        box-shadow: 0 6px 20px rgba(211,47,47,0.15);
        position: relative;
    }
    .violation-alert::before {
        content: '🚨';
        position: absolute;
        top: 1rem;
        right: 1rem;
        font-size: 1.5rem;
    }
    .success-alert {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        padding: 2rem;
        border-radius: 12px;
        border-left: 6px solid #388e3c;
        margin: 1.5rem 0;
        box-shadow: 0 6px 20px rgba(56,142,60,0.15);
        position: relative;
    }
    .success-alert::before {
        content: '✅';
        position: absolute;
        top: 1rem;
        right: 1rem;
        font-size: 1.5rem;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #0066cc 0%, #0099cc 50%, #00d4ff 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        font-weight: 700;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(0,102,204,0.3);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #0052a3 0%, #007acc 50%, #00c8ff 100%);
        box-shadow: 0 6px 20px rgba(0,102,204,0.5);
        transform: translateY(-2px);
    }
    .stat-box {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        border: 2px solid #e3f2fd;
        box-shadow: 0 4px 16px rgba(0,102,204,0.1);
        position: relative;
    }
    .stat-box::before {
        content: '';
        position: absolute;
        top: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 60%;
        height: 3px;
        background: linear-gradient(90deg, transparent, #0066cc, transparent);
    }
    .webcam-frame {
        border: 3px solid #0066cc;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,102,204,0.2);
        background: rgba(0,102,204,0.02);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1rem;
        border-radius: 12px 12px 0 0;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 8px 8px 0 0;
        border: 2px solid #e3f2fd;
        border-bottom: none;
        color: #0066cc;
        font-weight: 600;
        padding: 1rem 1.5rem;
        transition: all 0.3s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #f8f9fa;
        border-color: #0066cc;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #0066cc 0%, #0099cc 100%);
        color: white;
        box-shadow: 0 4px 16px rgba(0,102,204,0.3);
        border-color: #0066cc;
    }
    .stMetric {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #e3f2fd;
        box-shadow: 0 4px 16px rgba(0,102,204,0.1);
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #0066cc, #00d4ff);
        border-radius: 10px;
    }
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0,102,204,0.1);
    }
    .stDataFrame > div {
        border-radius: 10px;
    }
</style>
"""


def init_session_state():
    """Initialize session state variables."""
    defaults = {
        'detector': None,
        'report_generator': None,
        'notifier': None,
        'results': None,
        'report': None,
        'video_results': None,
        'dark_mode': True,
        'history': [],  # Store detection history
        'total_detections': 0,
        'total_violations': 0,
        'webcam_active': False,
        'webcam_results': [],
        'webcam_stats': {
            'frames_processed': 0,
            'total_detections': 0,
            'total_violations': 0,
            'avg_time': 0,
            'avg_fps': 0,
            'processing_times': []
        },
        'telegram_bot_token': '',
        'telegram_channel_id': '',
        'show_welcome': True,  # Show welcome screen for first-time users
        'system_initialized': False  # Track if system has been initialized
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def load_models(config):
    """Load detection and report generation models."""
    try:
        with st.spinner("🔄 Loading AI models..."):
            # Load detector
            if st.session_state.detector is None:
                try:
                    detector_config = {
                        "model_path": config.get('detector.model_path', "yolo11n.pt"),
                        "confidence_threshold": config.get('detector.confidence_threshold', 0.5),
                        "device": config.get('detector.device', "cpu")
                    }
                    st.session_state.detector = create_detector(detector_config)
                except Exception as e:
                    st.error(f"❌ Failed to load PPE detection model: {e}")
                    st.info("💡 Please ensure the model file exists and try again.")
                    st.session_state.detector = None

            # Load report generator (optional if API key not available)
            if st.session_state.report_generator is None:
                try:
                    report_config = {
                        "provider": config.get('llm.provider', 'ollama'),
                        "temperature": config.get('llm.temperature', 0.3)
                    }
                    if config.get('llm.provider') == "ollama":
                        report_config["model"] = config.get('llm.model', "llama3")
                    st.session_state.report_generator = create_report_generator(report_config)
                except ValueError as e:
                    st.warning(f"⚠️ Report generator not available: {e}")
                    st.info("💡 Detection will still work. Add API key for report generation.")
                    st.session_state.report_generator = None

            # Load Telegram notifier from config
            if st.session_state.notifier is None:
                from app.core.notification import create_telegram_notifier
                st.session_state.notifier = create_telegram_notifier(config)
                if st.session_state.notifier:
                    st.info("📱 Telegram notifications enabled from config")
                else:
                    st.info("📱 Telegram notifications not configured (check config.yaml)")

        st.success("✅ System ready!")
        st.session_state.system_initialized = True
        return True
    except Exception as e:
        st.error(f"❌ Error loading models: {e}")
        logger.error(f"Model loading failed: {e}")
        return False


def create_analytics_charts():
    """Create analytics dashboard with charts."""
    st.header("📊 Analytics Dashboard")

    # Generate sample data if no history
    if len(st.session_state.history) == 0:
        st.info("📈 No detection history yet. Analyze some images to see statistics!")
        return

    # Prepare data
    timestamps = [h.get('timestamp', datetime.now()) for h in st.session_state.history]
    violations = [len(h.get('violations', [])) for h in st.session_state.history]
    detection_times = [h.get('inference_time_ms', 0) for h in st.session_state.history]

    # Violation types count
    violation_types = defaultdict(int)
    for h in st.session_state.history:
        for v in h.get('violations', []):
            vtype = v.get('type', 'unknown')
            violation_types[vtype] += 1

    # Row 1: Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_analyses = len(st.session_state.history)
        st.metric("🔍 Total Analyses", total_analyses,
                 delta=f"+{total_analyses}" if total_analyses > 0 else None)
    with col2:
        total_viol = sum(violations)
        st.metric("⚠️ Total Violations", total_viol,
                 delta=f"+{total_viol}" if total_viol > 0 else None,
                 delta_color="inverse")
    with col3:
        avg_time = np.mean(detection_times) if detection_times else 0
        st.metric("⚡ Avg Detection Time", f"{avg_time:.1f}ms")
    with col4:
        compliance_rate = ((total_analyses - sum(1 for v in violations if v > 0)) / total_analyses * 100) if total_analyses > 0 else 100
        st.metric("✅ Compliance Rate", f"{compliance_rate:.1f}%",
                 delta=f"{compliance_rate-50:.1f}%" if compliance_rate > 50 else None)

    st.markdown("---")

    # Row 2: Charts
    col_left, col_right = st.columns(2)

    with col_left:
        # Violation Trend Line Chart
        st.subheader("📈 Violation Trend Over Time")
        if len(timestamps) > 1:
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=list(range(len(violations))),
                y=violations,
                mode='lines+markers',
                name='Violations',
                line=dict(color='#f44336', width=3),
                marker=dict(size=8, color='#d32f2f'),
                fill='tozeroy',
                fillcolor='rgba(244, 67, 54, 0.2)'
            ))
            fig_trend.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_title="Analysis #",
                yaxis_title="Violations",
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=12)
            )
            st.plotly_chart(fig_trend, width="stretch")
        else:
            st.info("Need more data points for trend analysis")

    with col_right:
        # Violation Types Pie Chart
        st.subheader("🎯 Violation Types Distribution")
        if violation_types:
            labels = [k.replace('_', ' ').title() for k in violation_types.keys()]
            values = list(violation_types.values())

            fig_pie = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker=dict(colors=px.colors.sequential.RdBu),
                textinfo='label+percent',
                textfont=dict(size=12)
            )])
            fig_pie.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                showlegend=True,
                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_pie, width="stretch")
        else:
            st.success("✅ No violations detected!")

    # Row 3: Performance Chart
    st.subheader("⚡ Detection Performance")
    col_perf1, col_perf2 = st.columns(2)

    with col_perf1:
        # Detection Time Bar Chart
        if detection_times:
            fig_perf = go.Figure()
            fig_perf.add_trace(go.Bar(
                x=list(range(len(detection_times))),
                y=detection_times,
                marker=dict(
                    color=detection_times,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="ms")
                ),
                text=[f"{t:.1f}ms" for t in detection_times],
                textposition='outside'
            ))
            fig_perf.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_title="Analysis #",
                yaxis_title="Time (ms)",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=11)
            )
            st.plotly_chart(fig_perf, width="stretch")

    with col_perf2:
        # Compliance Gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=compliance_rate,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Compliance Rate", 'font': {'size': 20}},
            delta={'reference': 80, 'increasing': {'color': "#4caf50"}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#00d4ff"},
                'bar': {'color': "#00d4ff"},
                'bgcolor': "#1e1e2e" if st.session_state.dark_mode else "white",
                'borderwidth': 2,
                'bordercolor': "#00d4ff",
                'steps': [
                    {'range': [0, 50], 'color': '#4a1c1c' if st.session_state.dark_mode else '#ffcdd2'},
                    {'range': [50, 80], 'color': '#2a2a1a' if st.session_state.dark_mode else '#fff9c4'},
                    {'range': [80, 100], 'color': '#1b2d1b' if st.session_state.dark_mode else '#c8e6c9'}
                ],
                'threshold': {
                    'line': {'color': "#ff6b6b", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_gauge.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=60, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12)
        )
        st.plotly_chart(fig_gauge, width="stretch")


def show_welcome_screen():
    """Display welcome screen for first-time users with step-by-step guide."""
    st.markdown('<h1 class="main-header">🦺 Welcome to SiteGuard AI Pro</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #00d4ff; font-size: 1.3rem; margin-bottom: 2rem;">Your AI-Powered Industrial Safety & Compliance Monitor</p>', unsafe_allow_html=True)
    
    # Quick Start Guide
    st.markdown("""
    <div class="metric-card" style="margin-bottom: 2rem;">
        <h2 style="color: #00d4ff; margin-bottom: 1rem;">🚀 Quick Start Guide</h2>
        <p style="font-size: 1.1rem; line-height: 1.8;">
            Follow these simple steps to start monitoring workplace safety:
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Step-by-step instructions
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("""
        <div class="stat-box" style="margin-bottom: 1rem;">
            <h1 style="color: #00d4ff; font-size: 3rem; margin: 0;">1</h1>
            <h3 style="margin-top: 0.5rem;">Initialize System</h3>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div style="padding: 1.5rem; background: rgba(0,212,255,0.1); border-radius: 8px; border-left: 4px solid #00d4ff; margin-bottom: 1rem;">
            <h4 style="margin-top: 0; color: #00d4ff;">First, initialize the AI system</h4>
            <p>Click the <strong>"🚀 Initialize System"</strong> button in the sidebar (left panel) to load the AI detection models.</p>
            <p style="margin-bottom: 0;"><em>This only needs to be done once when you start the application.</em></p>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("""
        <div class="stat-box" style="margin-bottom: 1rem;">
            <h1 style="color: #00d4ff; font-size: 3rem; margin: 0;">2</h1>
            <h3 style="margin-top: 0.5rem;">Choose Analysis Mode</h3>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div style="padding: 1.5rem; background: rgba(0,212,255,0.1); border-radius: 8px; border-left: 4px solid #00d4ff; margin-bottom: 1rem;">
            <h4 style="margin-top: 0; color: #00d4ff;">Select your preferred analysis method</h4>
            <ul style="margin-bottom: 0;">
                <li><strong>📸 Image Analysis</strong> - Upload photos for instant PPE detection</li>
                <li><strong>🎥 Video Analysis</strong> - Process recorded CCTV footage</li>
                <li><strong>📹 Live Webcam</strong> - Real-time monitoring with your webcam</li>
                <li><strong>🔍 RTSP Cameras</strong> - Connect to IP/ONVIF cameras</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("""
        <div class="stat-box" style="margin-bottom: 1rem;">
            <h1 style="color: #00d4ff; font-size: 3rem; margin: 0;">3</h1>
            <h3 style="margin-top: 0.5rem;">Analyze & Review</h3>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div style="padding: 1.5rem; background: rgba(0,212,255,0.1); border-radius: 8px; border-left: 4px solid #00d4ff; margin-bottom: 1rem;">
            <h4 style="margin-top: 0; color: #00d4ff;">Get instant safety insights</h4>
            <p>The AI will automatically detect:</p>
            <ul>
                <li>✅ Workers wearing proper PPE (helmets, vests, etc.)</li>
                <li>⚠️ Safety violations and missing equipment</li>
                <li>📊 Compliance statistics and trends</li>
            </ul>
            <p style="margin-bottom: 0;"><em>Generate OSHA-compliant reports with one click!</em></p>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("""
        <div class="stat-box" style="margin-bottom: 2rem;">
            <h1 style="color: #00d4ff; font-size: 3rem; margin: 0;">4</h1>
            <h3 style="margin-top: 0.5rem;">View Analytics</h3>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div style="padding: 1.5rem; background: rgba(0,212,255,0.1); border-radius: 8px; border-left: 4px solid #00d4ff; margin-bottom: 2rem;">
            <h4 style="margin-top: 0; color: #00d4ff;">Track safety performance over time</h4>
            <p>Visit the <strong>📊 Analytics Dashboard</strong> tab to see:</p>
            <ul style="margin-bottom: 0;">
                <li>📈 Violation trends and patterns</li>
                <li>🎯 Compliance rates and statistics</li>
                <li>⚡ System performance metrics</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Features Overview
    st.markdown("---")
    st.markdown("""
    <div class="metric-card">
        <h2 style="color: #00d4ff; margin-bottom: 1rem;">✨ Key Features</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        st.markdown("""
        <div class="stat-box" style="height: 200px;">
            <h2 style="font-size: 2.5rem; margin: 0;">🤖</h2>
            <h4 style="color: #00d4ff;">AI-Powered Detection</h4>
            <p style="font-size: 0.9rem;">Advanced YOLO model detects PPE violations with high accuracy</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_f2:
        st.markdown("""
        <div class="stat-box" style="height: 200px;">
            <h2 style="font-size: 2.5rem; margin: 0;">📄</h2>
            <h4 style="color: #00d4ff;">OSHA Reports</h4>
            <p style="font-size: 0.9rem;">Generate professional compliance reports automatically</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_f3:
        st.markdown("""
        <div class="stat-box" style="height: 200px;">
            <h2 style="font-size: 2.5rem; margin: 0;">🎥</h2>
            <h4 style="color: #00d4ff;">Real-Time Monitoring</h4>
            <p style="font-size: 0.9rem;">Live webcam and RTSP camera support for continuous surveillance</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_f4, col_f5, col_f6 = st.columns(3)
    
    with col_f4:
        st.markdown("""
        <div class="stat-box" style="height: 200px;">
            <h2 style="font-size: 2.5rem; margin: 0;">📊</h2>
            <h4 style="color: #00d4ff;">Analytics Dashboard</h4>
            <p style="font-size: 0.9rem;">Track trends, compliance rates, and performance metrics</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_f5:
        st.markdown("""
        <div class="stat-box" style="height: 200px;">
            <h2 style="font-size: 2.5rem; margin: 0;">📱</h2>
            <h4 style="color: #00d4ff;">Telegram Alerts</h4>
            <p style="font-size: 0.9rem;">Instant notifications when violations are detected</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_f6:
        st.markdown("""
        <div class="stat-box" style="height: 200px;">
            <h2 style="font-size: 2.5rem; margin: 0;">🌙</h2>
            <h4 style="color: #00d4ff;">Dark Mode</h4>
            <p style="font-size: 0.9rem;">Professional dark theme for comfortable viewing</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Call to action
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col_cta1, col_cta2, col_cta3 = st.columns([1, 2, 1])
    
    with col_cta2:
        if st.button("🚀 Get Started - Initialize System Now", type="primary", use_container_width=True):
            st.session_state.show_welcome = False
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("📖 Skip Welcome - Go to Dashboard", use_container_width=True):
            st.session_state.show_welcome = False
            st.rerun()
    
    # Tips section
    st.markdown("---")
    st.markdown("""
    <div style="padding: 1.5rem; background: rgba(0,212,255,0.05); border-radius: 8px; border: 1px solid rgba(0,212,255,0.3);">
        <h3 style="color: #00d4ff; margin-top: 0;">💡 Pro Tips</h3>
        <ul>
            <li><strong>Best Image Quality:</strong> Use clear, well-lit photos for accurate detection</li>
            <li><strong>Video Processing:</strong> Skip frames (process every 5-10 frames) for faster analysis</li>
            <li><strong>Real-Time Mode:</strong> Adjust FPS and confidence thresholds for optimal performance</li>
            <li><strong>Reports:</strong> Configure LLM provider in sidebar for automatic report generation</li>
            <li><strong>Notifications:</strong> Set up Telegram bot in config.yaml for instant alerts</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


def create_analytics_charts():
    """Create analytics dashboard with charts."""
    st.header("📊 Analytics Dashboard")

    # Generate sample data if no history
    if len(st.session_state.history) == 0:
        st.info("📈 No detection history yet. Analyze some images to see statistics!")
        return

    # Prepare data
    timestamps = [h.get('timestamp', datetime.now()) for h in st.session_state.history]
    violations = [len(h.get('violations', [])) for h in st.session_state.history]
    detection_times = [h.get('inference_time_ms', 0) for h in st.session_state.history]

    # Violation types count
    violation_types = defaultdict(int)
    for h in st.session_state.history:
        for v in h.get('violations', []):
            vtype = v.get('type', 'unknown')
            violation_types[vtype] += 1

    # Row 1: Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_analyses = len(st.session_state.history)
        st.metric("🔍 Total Analyses", total_analyses,
                 delta=f"+{total_analyses}" if total_analyses > 0 else None)
    with col2:
        total_viol = sum(violations)
        st.metric("⚠️ Total Violations", total_viol,
                 delta=f"+{total_viol}" if total_viol > 0 else None,
                 delta_color="inverse")
    with col3:
        avg_time = np.mean(detection_times) if detection_times else 0
        st.metric("⚡ Avg Detection Time", f"{avg_time:.1f}ms")
    with col4:
        compliance_rate = ((total_analyses - sum(1 for v in violations if v > 0)) / total_analyses * 100) if total_analyses > 0 else 100
        st.metric("✅ Compliance Rate", f"{compliance_rate:.1f}%",
                 delta=f"{compliance_rate-50:.1f}%" if compliance_rate > 50 else None)

    st.markdown("---")

    # Row 2: Charts
    col_left, col_right = st.columns(2)

    with col_left:
        # Violation Trend Line Chart
        st.subheader("📈 Violation Trend Over Time")
        if len(timestamps) > 1:
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=list(range(len(violations))),
                y=violations,
                mode='lines+markers',
                name='Violations',
                line=dict(color='#f44336', width=3),
                marker=dict(size=8, color='#d32f2f'),
                fill='tozeroy',
                fillcolor='rgba(244, 67, 54, 0.2)'
            ))
            fig_trend.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_title="Analysis #",
                yaxis_title="Violations",
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=12)
            )
            st.plotly_chart(fig_trend, width="stretch")
        else:
            st.info("Need more data points for trend analysis")

    with col_right:
        # Violation Types Pie Chart
        st.subheader("🎯 Violation Types Distribution")
        if violation_types:
            labels = [k.replace('_', ' ').title() for k in violation_types.keys()]
            values = list(violation_types.values())

            fig_pie = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker=dict(colors=px.colors.sequential.RdBu),
                textinfo='label+percent',
                textfont=dict(size=12)
            )])
            fig_pie.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                showlegend=True,
                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_pie, width="stretch")
        else:
            st.success("✅ No violations detected!")

    # Row 3: Performance Chart
    st.subheader("⚡ Detection Performance")
    col_perf1, col_perf2 = st.columns(2)

    with col_perf1:
        # Detection Time Bar Chart
        if detection_times:
            fig_perf = go.Figure()
            fig_perf.add_trace(go.Bar(
                x=list(range(len(detection_times))),
                y=detection_times,
                marker=dict(
                    color=detection_times,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="ms")
                ),
                text=[f"{t:.1f}ms" for t in detection_times],
                textposition='outside'
            ))
            fig_perf.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_title="Analysis #",
                yaxis_title="Time (ms)",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=11)
            )
            st.plotly_chart(fig_perf, width="stretch")

    with col_perf2:
        # Compliance Gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=compliance_rate,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Compliance Rate", 'font': {'size': 20}},
            delta={'reference': 80, 'increasing': {'color': "#4caf50"}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#00d4ff"},
                'bar': {'color': "#00d4ff"},
                'bgcolor': "#1e1e2e" if st.session_state.dark_mode else "white",
                'borderwidth': 2,
                'bordercolor': "#00d4ff",
                'steps': [
                    {'range': [0, 50], 'color': '#4a1c1c' if st.session_state.dark_mode else '#ffcdd2'},
                    {'range': [50, 80], 'color': '#2a2a1a' if st.session_state.dark_mode else '#fff9c4'},
                    {'range': [80, 100], 'color': '#1b2d1b' if st.session_state.dark_mode else '#c8e6c9'}
                ],
                'threshold': {
                    'line': {'color': "#ff6b6b", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_gauge.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=60, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12)
        )
        st.plotly_chart(fig_gauge, width="stretch")


def webcam_detection_page():
    """Live webcam detection page with true real-time video processing."""
    st.header("📹 Webcam Detection")

    st.markdown("""
    <div class="metric-card">
    <h3>🎥 Real-Time Webcam Processing</h3>
    <p>Continuous webcam stream analysis with frame-by-frame PPE detection</p>
    </div>
    """, unsafe_allow_html=True)

    # Stream control
    col_control, col_status = st.columns([1, 2])

    with col_control:
        stream_active = st.checkbox("🎬 Start Webcam Stream", value=False, key="webcam_stream")
        if stream_active:
            st.success("🔴 LIVE - Real-Time Processing")
        else:
            st.info("⏸️ STOPPED")

        # Stream settings
        st.markdown("### ⚙️ Stream Settings")
        fps_target = st.slider("Target FPS", 1, 30, 10, 1,
                              help="Target frames per second for processing")
        confidence_display = st.slider("Display Confidence", 0.1, 1.0, 0.5, 0.1,
                                     help="Minimum confidence to display detections")

        # Webcam selection
        st.markdown("### 📹 Webcam Device")

        # Simple webcam detection
        camera_devices = []
        for i in range(5):  # Check first 5 camera indices
            cap = cv2.VideoCapture(i)
            if cap is not None and hasattr(cap, 'isOpened') and cap.isOpened():
                camera_devices.append(f"Camera {i}")
                cap.release()

        camera_source = None
        selected_camera = None  # Initialize to avoid UnboundLocalError
        if camera_devices:
            selected_camera = st.selectbox("Select Webcam Device", camera_devices, index=0)
            camera_source = int(selected_camera.split()[-1])
            st.success(f"✅ Selected: {selected_camera}")
        else:
            st.warning("⚠️ No webcams detected")
            camera_source = None

    with col_status:
        if stream_active:
            st.markdown("### 📊 Live Stats")
            live_detections = st.empty()
            live_violations = st.empty()
            live_fps = st.empty()
            live_status = st.empty()
        else:
            st.markdown("### 📊 Session Stats")
            if 'webcam_stats' in st.session_state:
                stats = st.session_state.webcam_stats
                st.metric("📹 Frames Processed", stats.get('frames_processed', 0))
                st.metric("👤 Total Detections", stats.get('total_detections', 0))
                st.metric("⚠️ Total Violations", stats.get('total_violations', 0))
                st.metric("🎯 Avg FPS", f"{stats.get('avg_fps', 0):.1f}")

    # Video feed display
    col_feed, col_results = st.columns([2, 1])

    with col_feed:
        st.markdown("### 📺 Live Video Feed")

        # Placeholder for video feed
        video_placeholder = st.empty()

        # Real-time processing
        if stream_active and 'webcam_stats' in st.session_state and camera_source is not None:
            try:
                # Set camera type for processing
                selected_camera_type = "Webcam"

                # Initialize webcam
                cap = cv2.VideoCapture(camera_source)
                camera_info = f"Webcam {camera_source}"

                if cap is None or not cap.isOpened():
                    st.error(f"❌ Cannot open {camera_info}")
                    stream_active = False
                else:
                    # Set camera properties for better performance
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    if selected_camera_type == "Webcam":
                        cap.set(cv2.CAP_PROP_FPS, fps_target)

                    st.info(f"📹 {camera_info} opened successfully")

                    # Processing loop
                    frame_count = 0
                    start_time = time.time()
                    processing_times = []
                    last_frame_time = time.time()

                    while stream_active and cap.isOpened():
                        ret, frame = cap.read()
                        if not ret:
                            st.error(f"❌ Failed to read frame from {camera_info}")
                            break

                        frame_count += 1
                        frame_start = time.time()

                        # Process frame
                        if st.session_state.detector:
                            try:
                                results = st.session_state.detector.detect(frame, annotate=True)

                                # Filter detections by confidence for display
                                filtered_detections = [
                                    d for d in results.detections
                                    if d.confidence >= confidence_display
                                ]

                                # Create display frame with annotations
                                display_frame = frame.copy()

                                # Draw detections
                                for detection in filtered_detections:
                                    bbox = detection.bbox
                                    x1, y1, x2, y2 = map(int, bbox)

                                    # Color based on class
                                    if 'person' in detection.class_name.lower():
                                        color = (255, 0, 0)  # Blue for person
                                    elif any(ppe in detection.class_name.lower() for ppe in ['hardhat', 'helmet']):
                                        color = (0, 255, 0)  # Green for PPE
                                    elif any(ppe in detection.class_name.lower() for ppe in ['vest', 'safety']):
                                        color = (0, 255, 255)  # Yellow for vest
                                    else:
                                        color = (255, 255, 255)  # White for others

                                    # Draw bounding box
                                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)

                                    # Draw label
                                    label = f"{detection.class_name}: {detection.confidence:.2f}"
                                    cv2.putText(display_frame, label, (x1, y1-10),
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                                # Draw violation alerts
                                if results.has_violations:
                                    cv2.putText(display_frame, "VIOLATION DETECTED!",
                                              (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

                                # Convert to RGB for Streamlit
                                display_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)

                                # Display frame
                                video_placeholder.image(display_rgb, channels="RGB", width=640)

                                # Update stats
                                stats = st.session_state.webcam_stats
                                stats['frames_processed'] = frame_count
                                stats['total_detections'] += len(results.detections)
                                stats['total_violations'] += len(results.violations)

                                # Calculate FPS
                                elapsed = time.time() - start_time
                                if elapsed > 0:
                                    current_fps = frame_count / elapsed
                                    stats['avg_fps'] = current_fps

                                # Update live metrics
                                live_detections.metric("👤 Detections",
                                                     len([d for d in results.detections if 'person' in d.class_name.lower()]))
                                live_violations.metric("⚠️ Violations", len(results.violations))
                                live_fps.metric("🎯 FPS", f"{current_fps:.1f}")
                                live_status.success(f"Frame {frame_count} processed")

                                # Send Telegram notification if violations detected
                                if results.has_violations and st.session_state.notifier:
                                    try:
                                        st.session_state.notifier.send_violation_alert(
                                            violations=results.violations,
                                            location=st.session_state.get('location', 'Industrial Site'),
                                            site_id=st.session_state.get('site_id'),
                                            timestamp=datetime.now().isoformat()
                                        )
                                    except Exception as e:
                                        logger.error(f"Failed to send Telegram notification: {e}")

                                # Add to history (sample every 10 frames to avoid overflow)
                                if frame_count % 10 == 0:
                                    st.session_state.history.append({
                                        'timestamp': datetime.now(),
                                        'violations': results.violations,
                                        'detections': len(results.detections),
                                        'inference_time_ms': (time.time() - frame_start) * 1000
                                    })

                                frame_end = time.time()
                                processing_times.append(frame_end - frame_start)

                                # Keep only last 100 processing times
                                if len(processing_times) > 100:
                                    processing_times = processing_times[-100:]

                            except Exception as e:
                                st.error(f"❌ Processing error: {e}")
                                live_status.error("❌ Error")
                                break
                        else:
                            # Show raw frame if detector not initialized
                            display_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            video_placeholder.image(display_rgb, channels="RGB", width=640)
                            live_status.warning("⚠️ Detector not initialized")

                        # Control frame rate - maintain consistent timing between frames
                        current_time = time.time()
                        frame_time = current_time - last_frame_time
                        target_frame_time = 1.0 / fps_target

                        if frame_time < target_frame_time:
                            time.sleep(target_frame_time - frame_time)

                        last_frame_time = time.time()

                        # Check if stream should stop (user unchecked the box)
                        if not st.session_state.get('webcam_stream', False):
                            break

                    # Cleanup
                    cap.release()
                    st.success("✅ Stream stopped")

            except Exception as e:
                st.error(f"❌ Camera error: {e}")
                stream_active = False
        else:
            # Show camera selection when not streaming
            camera_ready = bool(camera_devices)
            camera_info = selected_camera or "webcam"

            if camera_ready:
                st.info(f"📹 Ready to start real-time processing with {camera_info}")
                st.markdown("""
                **Real-Time Processing Features:**
                - 🎯 Frame-by-frame YOLO detection
                - 📊 Live statistics and FPS monitoring
                - 🚨 Instant violation alerts
                - 🎥 Continuous video stream analysis
                """)
            else:
                st.warning("⚠️ No webcams detected. Please connect a webcam.")

    with col_results:
        st.markdown("### 💡 Real-Time Processing Info")
        st.markdown("""
        - 🎬 **DeepStream-like Processing**: Frame-by-frame analysis
        - ⚡ **Low Latency**: Optimized for real-time performance
        - 📊 **Live Metrics**: FPS, detections, violations
        - 🚨 **Instant Alerts**: Telegram notifications for violations
        - 🎛️ **Configurable**: Adjust FPS and confidence thresholds
        """)

        # Current results display
        if st.session_state.results and not stream_active:
            results = st.session_state.results

            if results.has_violations:
                st.markdown('<div class="violation-alert">', unsafe_allow_html=True)
                st.markdown("### ⚠️ VIOLATIONS DETECTED")
                for i, violation in enumerate(results.violations, 1):
                    vtype = violation.get('type', 'unknown').replace('_', ' ').title()
                    severity = violation.get('severity', 'medium').upper()
                    st.markdown(f"**{i}. {vtype}** - Severity: {severity}")
                st.markdown('</div>', unsafe_allow_html=True)

                # Generate report button
                if st.session_state.report_generator:
                    st.markdown("---")
                    if st.button("📄 Generate Report", key="webcam_report", type="primary"):
                        with st.spinner("📝 Generating report..."):
                            metadata = ReportMetadata(
                                location=st.session_state.location,
                                timestamp=datetime.now(),
                                site_id=st.session_state.site_id or None,
                                inspector_id=st.session_state.inspector_id or None
                            )
                            report_format = ReportFormat[st.session_state.report_format.upper()]
                            try:
                                report = st.session_state.report_generator.generate_report(
                                    violations=results.violations,
                                    metadata=metadata,
                                    format=report_format
                                )
                                st.session_state.report = report
                                st.success("✅ Report generated!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Failed: {e}")
            else:
                st.success("✅ No violations detected!")

        # Performance metrics
        if 'webcam_stats' in st.session_state and st.session_state.webcam_stats['frames_processed'] > 0:
            st.markdown("---")
            st.markdown("### ⚡ Performance")
            stats = st.session_state.webcam_stats
            st.metric("📈 Current FPS", f"{stats.get('avg_fps', 0):.1f}")
            st.metric("🎯 Target FPS", fps_target)
            st.metric("📊 Frames Processed", stats['frames_processed'])


def onvif_detection_page():
    """ONVIF camera discovery and management page."""
    st.header("🔍 ONVIF Camera Management")

    st.markdown("""
    <div class="metric-card">
    <h3>🌐 Network Camera Discovery</h3>
    <p>Discover, configure, and manage IP cameras on your network using ONVIF protocol</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize session state for discovered and added cameras
    if 'discovered_cameras' not in st.session_state:
        st.session_state.discovered_cameras = []
    if 'added_cameras' not in st.session_state:
        st.session_state.added_cameras = []

    # Stream control
    col_control, col_status = st.columns([1, 2])

    with col_control:
        stream_active = st.checkbox("🎬 Start Camera Stream", value=False, key="onvif_stream")
        if stream_active:
            st.success("🔴 LIVE - Real-Time Processing")
        else:
            st.info("⏸️ STOPPED")

        # Stream settings
        st.markdown("### ⚙️ Stream Settings")
        fps_target = st.slider("Target FPS", 1, 30, 10, 1,
                              help="Target frames per second for processing", key="onvif_fps")
        confidence_display = st.slider("Display Confidence", 0.1, 1.0, 0.5, 0.1,
                                     help="Minimum confidence to display detections", key="onvif_confidence")

        # ONVIF camera discovery
        st.markdown("### 🔍 ONVIF Camera Discovery")

        # Step 1: Discover cameras (no credentials needed)
        if st.button("🔍 Discover Cameras on Network", key="discover_network"):
            with st.spinner("Scanning network for available cameras..."):
                try:
                    # Use the working ONVIF discovery (just find cameras, no credentials)
                    discovery = WorkingONVIFDiscovery()
                    discovered_cameras = discovery.discover_cameras(timeout=10)

                    # Format discovered cameras (without RTSP URLs yet)
                    formatted_cameras = []
                    for cam in discovered_cameras:
                        formatted_cameras.append({
                            'name': cam['name'],
                            'ip': cam['ip'],
                            'port': cam['port'],
                            'type': 'onvif',
                            'manufacturer': 'Unknown',
                            'model': 'Unknown'
                        })

                    st.session_state.discovered_cameras = formatted_cameras
                    if formatted_cameras:
                        st.success(f"✅ Found {len(formatted_cameras)} camera(s) on network")
                    else:
                        st.warning("⚠️ No cameras found on network")
                except Exception as e:
                    st.error(f"❌ Network discovery error: {str(e)}")
                    st.session_state.discovered_cameras = []

        # Step 2: Show discovered cameras with "Add Camera" buttons
        if st.session_state.discovered_cameras:
            st.markdown("### 📹 Available Cameras")

            for i, cam in enumerate(st.session_state.discovered_cameras):
                with st.container():
                    col_info, col_action = st.columns([3, 1])

                    with col_info:
                        st.markdown(f"**{cam['name']}**")
                        st.caption(f"IP: {cam['ip']} | Port: {cam['port']}")
                        # Check if already added
                        already_added = any(ac['ip'] == cam['ip'] and ac['port'] == cam['port']
                                          for ac in st.session_state.added_cameras)
                        if already_added:
                            st.success("✅ Already added to your camera list")

                    with col_action:
                        if not already_added:
                            if st.button("➕ Add Camera", key=f"add_camera_{i}"):
                                # Store camera index for credential input
                                st.session_state[f'adding_camera_{i}'] = True
                                st.rerun()

                    # Show credential input if Add Camera was clicked
                    if st.session_state.get(f'adding_camera_{i}', False):
                        st.markdown("---")
                        with st.container():
                            st.markdown(f"**Add {cam['name']}**")
                            col_cred1, col_cred2, col_buttons = st.columns([1, 1, 1])

                            with col_cred1:
                                add_username = st.text_input("Username", value="orinnano",
                                                           key=f"username_{i}")
                            with col_cred2:
                                add_password = st.text_input("Password", type="password",
                                                           value="orinnano", key=f"password_{i}")
                            with col_buttons:
                                if st.button("✅ Confirm Add", key=f"confirm_add_{i}"):
                                    # Test connection and get RTSP URL
                                    with st.spinner("Testing connection and getting RTSP URL..."):
                                        try:
                                            discovery = WorkingONVIFDiscovery()
                                            detailed_info = discovery.get_camera_info(
                                                cam['ip'], cam['port'], add_username, add_password)

                                            if detailed_info and 'stream_uris' in detailed_info and detailed_info['stream_uris']:
                                                rtsp_url = detailed_info['stream_uris'][0]
                                                manufacturer = detailed_info.get('manufacturer', 'Unknown')
                                                model = detailed_info.get('model', 'Unknown')

                                                # Add to added cameras
                                                added_camera = {
                                                    'name': cam['name'],
                                                    'ip': cam['ip'],
                                                    'port': cam['port'],
                                                    'type': 'onvif',
                                                    'rtsp_url': rtsp_url,
                                                    'username': add_username,
                                                    'password': add_password,
                                                    'manufacturer': manufacturer,
                                                    'model': model
                                                }
                                                st.session_state.added_cameras.append(added_camera)

                                                st.success(f"✅ {cam['name']} added successfully!")
                                                # Clear the adding state
                                                st.session_state[f'adding_camera_{i}'] = False
                                                st.rerun()
                                            else:
                                                st.error("❌ Could not get RTSP URL. Check credentials.")
                                        except Exception as e:
                                            st.error(f"❌ Failed to add camera: {str(e)}")

                                if st.button("❌ Cancel", key=f"cancel_add_{i}"):
                                    st.session_state[f'adding_camera_{i}'] = False
                                    st.rerun()

        # Step 3: Show added cameras for selection
        rtsp_url = None
        onvif_username = None
        onvif_password = None

        if st.session_state.added_cameras:
            st.markdown("### 🎥 Your Added Cameras")

            camera_options = []
            for i, cam in enumerate(st.session_state.added_cameras):
                camera_options.append(f"{cam['name']} ({cam['ip']}) - {cam.get('manufacturer', 'Unknown')}")

            selected_camera_option = st.selectbox("Select Camera for Live Detection",
                                                camera_options, key="added_camera_select")
            selected_index = camera_options.index(selected_camera_option)
            selected_camera_info = st.session_state.added_cameras[selected_index]

            # Show selected camera details
            rtsp_url = selected_camera_info.get('rtsp_url')
            if rtsp_url:
                st.info(f"**RTSP URL:** {rtsp_url}")
                st.caption(f"Username: {selected_camera_info.get('username', 'N/A')} | "
                         f"Password: {'*' * len(selected_camera_info.get('password', ''))}")

                # Test connection button
                if st.button("🔍 Test Connection", key="test_added_camera"):
                    with st.spinner("Testing camera connection..."):
                        try:
                            test_camera = RTSPCamera(rtsp_url,
                                                   selected_camera_info.get('username'),
                                                   selected_camera_info.get('password'))
                            if test_camera.connect():
                                st.success("✅ Camera connection successful!")
                                test_camera.cap.release()
                            else:
                                st.error("❌ Camera connection failed!")
                        except Exception as e:
                            st.error(f"❌ Connection error: {str(e)}")

                onvif_username = selected_camera_info.get('username')
                onvif_password = selected_camera_info.get('password')
            else:
                st.warning("No RTSP URL available for this camera")
        else:
            st.info("💡 No cameras added yet. Discover cameras above and add them to your list.")

    with col_status:
        if stream_active:
            st.markdown("### 📊 Live Stats")
            live_detections = st.empty()
            live_violations = st.empty()
            live_fps = st.empty()
            live_status = st.empty()
        else:
            st.markdown("### 📊 Session Stats")
            if 'onvif_stats' in st.session_state:
                stats = st.session_state.onvif_stats
                st.metric("📹 Frames Processed", stats.get('frames_processed', 0))
                st.metric("👤 Total Detections", stats.get('total_detections', 0))
                st.metric("⚠️ Total Violations", stats.get('total_violations', 0))
                st.metric("🎯 Avg FPS", f"{stats.get('avg_fps', 0):.1f}")

    # Video feed display
    col_feed, col_results = st.columns([2, 1])

    with col_feed:
        st.markdown("### 📺 Live Video Feed")

        # Placeholder for video feed
        video_placeholder = st.empty()

        # Real-time processing
        if stream_active and rtsp_url and onvif_username and onvif_password:
            try:
                # Initialize ONVIF camera
                rtsp_camera = RTSPCamera(rtsp_url, onvif_username, onvif_password)
                connected = rtsp_camera.connect()
                cap = rtsp_camera.cap if connected else None
                camera_info = f"ONVIF Camera: {rtsp_url}"

                if cap is None or not cap.isOpened():
                    st.error(f"❌ Cannot open {camera_info}")
                    stream_active = False
                else:
                    # Set camera properties for better performance
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

                    st.info(f"📹 {camera_info} opened successfully")

                    # Processing loop
                    frame_count = 0
                    start_time = time.time()
                    processing_times = []
                    last_frame_time = time.time()

                    while stream_active and cap.isOpened():
                        ret, frame = cap.read()
                        if not ret:
                            st.error(f"❌ Failed to read frame from {camera_info}")
                            break

                        frame_count += 1
                        frame_start = time.time()

                        # Process frame
                        if st.session_state.detector:
                            try:
                                results = st.session_state.detector.detect(frame, annotate=True)

                                # Filter detections by confidence for display
                                filtered_detections = [
                                    d for d in results.detections
                                    if d.confidence >= confidence_display
                                ]

                                # Create display frame with annotations
                                display_frame = results.annotated_image.copy()

                                # Update live stats
                                live_detections.metric("👤 Detections", len(filtered_detections))
                                live_violations.metric("⚠️ Violations",
                                                     len([d for d in filtered_detections if not d.compliant]))
                                live_fps.metric("🎯 FPS", f"{1.0 / (time.time() - frame_start):.1f}")

                                # Show violations in live status
                                violations = [d for d in filtered_detections if not d.compliant]
                                if violations:
                                    live_status.error(f"🚨 {len(violations)} violations detected!")
                                else:
                                    live_status.success("✅ All personnel compliant")

                                # Display frame
                                video_placeholder.image(display_frame, channels="BGR")

                                # Store results for session
                                st.session_state.results = results

                            except Exception as e:
                                st.error(f"❌ Detection error: {e}")
                                video_placeholder.image(frame, channels="BGR")
                        else:
                            # No detector available, just show raw frame
                            video_placeholder.image(frame, channels="BGR")

                        # Frame rate control
                        current_time = time.time()
                        frame_time = current_time - last_frame_time
                        target_frame_time = 1.0 / fps_target

                        if frame_time < target_frame_time:
                            time.sleep(target_frame_time - frame_time)

                        last_frame_time = time.time()

                        # Check if stream should stop (user unchecked the box)
                        if not st.session_state.get('onvif_stream', False):
                            break

                    # Cleanup
                    cap.release()
                    st.success("✅ Stream stopped")

                    # Store final stats
                    if frame_count > 0:
                        avg_fps = frame_count / (time.time() - start_time)
                        st.session_state.onvif_stats = {
                            'frames_processed': frame_count,
                            'total_detections': sum(len(r.detections) for r in [st.session_state.results] if r),
                            'total_violations': sum(len([d for d in r.detections if not d.compliant]) for r in [st.session_state.results] if r),
                            'avg_fps': avg_fps
                        }

            except Exception as e:
                st.error(f"❌ Camera error: {e}")
                stream_active = False
        else:
            # Show camera selection when not streaming
            if st.session_state.added_cameras:
                st.info("📹 Ready to start real-time processing with selected ONVIF camera")
                st.markdown("""
                **Real-Time Processing Features:**
                - 🎯 Frame-by-frame YOLO detection
                - 📊 Live statistics and FPS monitoring
                - 🚨 Instant violation alerts
                - 🎥 Continuous video stream analysis
                """)
            else:
                st.warning("⚠️ No ONVIF cameras configured. Discover and add cameras above.")

    with col_results:
        st.markdown("### 💡 Real-Time Processing Info")
        st.markdown("""
        - 🎬 **DeepStream-like Processing**: Frame-by-frame analysis
        - ⚡ **Low Latency**: Optimized for real-time performance
        - 📊 **Live Metrics**: FPS, detections, violations
        - 🚨 **Instant Alerts**: Telegram notifications for violations
        - 🎛️ **Configurable**: Adjust FPS and confidence thresholds
        """)

        # Current results display
        if st.session_state.results and not stream_active:
            results = st.session_state.results

            if results.has_violations:
                st.markdown('<div class="violation-alert">', unsafe_allow_html=True)
                st.markdown("### ⚠️ VIOLATIONS DETECTED")
                for i, violation in enumerate(results.violations, 1):
                    vtype = violation.get('type', 'unknown').replace('_', ' ').title()
                    severity = violation.get('severity', 'medium').upper()
                    st.markdown(f"**{i}. {vtype}** - Severity: {severity}")
                st.markdown('</div>', unsafe_allow_html=True)

                # Generate report button
                if st.session_state.report_generator:
                    st.markdown("---")
                    if st.button("📄 Generate Report", key="onvif_report", type="primary"):
                        with st.spinner("📝 Generating report..."):
                            metadata = ReportMetadata(
                                location=st.session_state.location,
                                timestamp=datetime.now(),
                                site_id=st.session_state.site_id or None,
                                inspector_id=st.session_state.inspector_id or None
                            )
                            report_format = ReportFormat[st.session_state.report_format.upper()]
                            try:
                                report = st.session_state.report_generator.generate_report(
                                    violations=results.violations,
                                    metadata=metadata,
                                    format=report_format
                                )
                                st.session_state.report = report
                                st.success("✅ Report generated!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Failed: {e}")
            else:
                st.success("✅ No violations detected!")

        # Performance metrics
        if 'onvif_stats' in st.session_state and st.session_state.onvif_stats['frames_processed'] > 0:
            st.markdown("---")
            st.markdown("### ⚡ Performance")
            stats = st.session_state.onvif_stats
            st.metric("📈 Current FPS", f"{stats.get('avg_fps', 0):.1f}")
            st.metric("🎯 Target FPS", fps_target)
            st.metric("📊 Frames Processed", stats['frames_processed'])


def main():
    """Main application with tabs."""
    init_session_state()

    # Load configuration
    config = load_config()

    # Show welcome screen for first-time users or if system not initialized
    if st.session_state.show_welcome or not st.session_state.system_initialized:
        show_welcome_screen()
        return

    # Header
    st.markdown('<h1 class="main-header">🦺 SiteGuard AI Pro</h1>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align: center; color: {"#999" if st.session_state.dark_mode else "#666"}; font-size: 1.1rem;">Advanced Industrial Safety & Compliance Monitor</p>', unsafe_allow_html=True)

    # Apply theme
    st.markdown(get_custom_css(st.session_state.dark_mode), unsafe_allow_html=True)

    # System status indicator at the top
    if not st.session_state.system_initialized:
        st.warning("⚠️ System not initialized. Please click '🚀 Initialize System' in the sidebar to start.")
    else:
        st.success("✅ System Ready - AI models loaded and operational")

    # Sidebar configuration
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/1f77b4/FFFFFF?text=SiteGuard+AI", width="stretch")
        st.header("⚙️ Configuration")

        # Initialize button - prominent placement
        st.markdown("### 🚀 System Control")
        if not st.session_state.system_initialized:
            st.markdown("""
            <div style="padding: 1rem; background: rgba(255,193,7,0.1); border-radius: 8px; border-left: 4px solid #ffc107; margin-bottom: 1rem;">
                <p style="margin: 0; font-weight: bold; color: #ffc107;">⚠️ Action Required</p>
                <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem;">Initialize the system to start using SiteGuard AI</p>
            </div>
            """, unsafe_allow_html=True)
            
        if st.button("🚀 Initialize System", type="primary", disabled=st.session_state.system_initialized):
            load_models(config)
        
        if st.session_state.system_initialized:
            st.success("✅ System Initialized")
            
        # Show welcome screen button
        if st.button("📖 Show Welcome Guide"):
            st.session_state.show_welcome = True
            st.rerun()

        st.markdown("---")

        # Model settings
        st.subheader("🎯 Detection Settings")
        st.session_state.confidence_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.1,
            max_value=0.9,
            value=0.5,
            step=0.05,
            help="Minimum confidence score for detections (higher = fewer false positives)"
        )

        # LLM settings
        st.subheader("📝 Report Generation")
        st.session_state.llm_provider = st.selectbox(
            "LLM Provider",
            ["ollama", "openai", "gemini"],
            help="Select the LLM provider for report generation"
        )

        if st.session_state.llm_provider == "ollama":
            st.session_state.llm_model = st.selectbox(
                "Ollama Model",
                ["llama3", "llama3.1", "llama3.2", "mistral", "phi3", "gemma2"],
                help="Select Ollama model for report generation"
            )

        st.session_state.report_format = st.selectbox(
            "Report Format",
            ["formal", "technical", "executive", "email"],
            help="Select the format style for generated reports"
        )

        # Metadata
        st.subheader("📍 Site Information")
        st.session_state.location = st.text_input(
            "Location/Site Name",
            value="Construction Site A",
            help="Enter the site or location name for reports"
        )

        st.session_state.site_id = st.text_input("Site ID (Optional)", value="", help="Optional site identifier")
        st.session_state.inspector_id = st.text_input("Inspector ID (Optional)", value="", help="Optional inspector identifier")

        st.markdown("---")

        # System stats
        if st.session_state.detector:
            st.markdown("### 📊 System Stats")
            metrics = st.session_state.detector.get_metrics()
            st.metric("Total Analyses", len(st.session_state.history))
            st.metric("Violations Found", sum(len(h.get('violations', [])) for h in st.session_state.history))

            if st.button("🗑️ Clear History"):
                st.session_state.history = []
                st.rerun()

    # Main tabs with better descriptions
    st.markdown("""
    <div style="padding: 1rem; background: rgba(0,212,255,0.05); border-radius: 8px; border: 1px solid rgba(0,212,255,0.2); margin-bottom: 1rem;">
        <h3 style="margin: 0 0 0.5rem 0; color: #00d4ff;">📋 Choose Your Analysis Mode</h3>
        <p style="margin: 0; font-size: 0.95rem;">Select a tab below based on your monitoring needs:</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📸 1. Image Analysis",
        "🎥 2. Video Analysis",
        "📹 3. Live Webcam",
        "🔍 4. RTSP Cameras",
        "📊 5. Analytics Dashboard"
    ])

    with tab1:
        # Original image upload functionality
        st.header("📸 Image Upload & Analysis")
        
        # Help text for this tab
        st.markdown("""
        <div style="padding: 1rem; background: rgba(0,212,255,0.05); border-radius: 8px; border-left: 4px solid #00d4ff; margin-bottom: 1.5rem;">
            <h4 style="margin: 0 0 0.5rem 0; color: #00d4ff;">📖 How to Use Image Analysis</h4>
            <p style="margin: 0; font-size: 0.95rem;">
                <strong>Step 1:</strong> Upload a photo (JPG/PNG) using the file uploader below<br>
                <strong>Step 2:</strong> Click "🔍 Analyze Image" to detect PPE violations<br>
                <strong>Step 3:</strong> Review results and generate OSHA reports if violations are found
            </p>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.8;">
                💡 <em>Best for: Quick checks, incident documentation, compliance audits</em>
            </p>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Upload CCTV snapshot or workplace photo",
            type=["jpg", "jpeg", "png"],
            help="Supported formats: JPG, PNG",
            key="image_uploader"
        )

        col_img1, col_img2 = st.columns(2)

        with col_img1:
            if uploaded_file is not None:
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image", width="stretch")

                # Store current image for evidence
                st.session_state.current_image = image

                # Convert to numpy
                image_np = np.array(image)
                if len(image_np.shape) == 2:
                    image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
                elif image_np.shape[2] == 4:
                    image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGR)
                else:
                    image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

                if st.button("🔍 Analyze Image", type="primary", disabled=st.session_state.detector is None):
                    if st.session_state.detector:
                        with st.spinner("🔄 Detecting PPE violations..."):
                            start_time = time.time()
                            results = st.session_state.detector.detect(image_np, annotate=True)
                            inference_time = (time.time() - start_time) * 1000

                            st.session_state.results = results

                            # Send Telegram notification if violations detected
                            if results.has_violations and st.session_state.notifier:
                                try:
                                    st.session_state.notifier.send_violation_alert(
                                        violations=results.violations,
                                        location=st.session_state.get('location', 'Industrial Site'),
                                        site_id=st.session_state.get('site_id'),
                                        timestamp=datetime.now().isoformat()
                                    )
                                except Exception as e:
                                    logger.error(f"Failed to send Telegram notification: {e}")

                            # Add to history
                            st.session_state.history.append({
                                'timestamp': datetime.now(),
                                'violations': results.violations,
                                'detections': len(results.detections),
                                'inference_time_ms': inference_time
                            })

                            # Generate report if needed
                            if results.has_violations and st.session_state.report_generator:
                                with st.spinner("📝 Generating report..."):
                                    metadata = ReportMetadata(
                                        location=st.session_state.location,
                                        timestamp=datetime.now(),
                                        site_id=st.session_state.site_id or None,
                                        inspector_id=st.session_state.inspector_id or None
                                    )
                                    report_format = ReportFormat[st.session_state.report_format.upper()]
                                    try:
                                        report = st.session_state.report_generator.generate_report(
                                            violations=results.violations,
                                            metadata=metadata,
                                            format=report_format
                                        )
                                        st.session_state.report = report
                                    except Exception as e:
                                        st.warning(f"⚠️ Report generation failed: {e}")

                        st.rerun()

        with col_img2:
            st.header("📊 Detection Results")

            if st.session_state.results:
                results = st.session_state.results

                # Display annotated image
                if hasattr(results, 'annotated_image') and results.annotated_image is not None:
                    annotated_rgb = cv2.cvtColor(results.annotated_image, cv2.COLOR_BGR2RGB)
                    st.image(annotated_rgb, caption="Detection Results", width="stretch")

                # Metrics
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric("👤 Detections", len(results.detections))
                with col_m2:
                    st.metric("⚠️ Violations", len(results.violations))
                with col_m3:
                    st.metric("⚡ Speed", f"{results.inference_time_ms:.0f}ms")

                # Violation alerts
                if results.has_violations:
                    st.markdown('<div class="violation-alert">', unsafe_allow_html=True)
                    st.markdown("### ⚠️ VIOLATIONS DETECTED")
                    for i, violation in enumerate(results.violations, 1):
                        vtype = violation.get('type', 'unknown').replace('_', ' ').title()
                        severity = violation.get('severity', 'medium').upper()
                        st.markdown(f"**{i}. {vtype}** - Severity: {severity}")
                    st.markdown('</div>', unsafe_allow_html=True)

                    # Manual report generation button
                    st.markdown("### 📝 Report Generation")
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("📄 Generate OSHA Report", type="primary", disabled=st.session_state.report_generator is None):
                            if st.session_state.report_generator:
                                with st.spinner("📝 Generating OSHA-compliant incident report..."):
                                    # Save current image for visual evidence
                                    visual_evidence_path = None
                                    try:
                                        evidence_dir = Path("data/evidence")
                                        evidence_dir.mkdir(exist_ok=True, parents=True)
                                        evidence_path = evidence_dir / f"violation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                                        st.session_state.current_image.save(str(evidence_path))
                                        visual_evidence_path = str(evidence_path)
                                    except Exception as e:
                                        st.warning(f"Could not save visual evidence: {e}")
                                        visual_evidence_path = None

                                    # Generate report with available data
                                    metadata = ReportMetadata(
                                        location=st.session_state.location,
                                        timestamp=datetime.now(),
                                        site_id=st.session_state.site_id or None,
                                        inspector_id=st.session_state.inspector_id or None,
                                        camera_id="AI Detection System",
                                        # OSHA fields will be filled by user after generation
                                        ref_no=f"SG-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}",
                                        legal_clause="Failure to comply with Section 24, OSHA 1994",
                                        penalty_amount=50.00,
                                        visual_evidence_path=visual_evidence_path
                                    )

                                    # Auto-detect violation categories from results
                                    # Map detector violation types to PPE checklist items
                                    violation_type_mapping = {
                                        'no_hardhat': 'helmet',
                                        'no_helmet': 'helmet',
                                        'no_vest': 'vest',
                                        'no_shoes': 'shoes',
                                        'no_mask': 'mask',
                                        'no_gloves': 'gloves',
                                        'no_goggles': 'goggles'
                                    }

                                    violation_categories = []
                                    if results.violations:
                                        for violation in results.violations:
                                            vtype = violation.get('type', '')
                                            # Map violation types to PPE checklist items
                                            if vtype in violation_type_mapping:
                                                ppe_item = violation_type_mapping[vtype]
                                                if ppe_item not in violation_categories:
                                                    violation_categories.append(ppe_item)
                                            elif vtype.startswith('no_'):
                                                ppe_item = vtype[3:]  # Remove 'no_' prefix
                                                if ppe_item not in violation_categories:
                                                    violation_categories.append(ppe_item)
                                            elif vtype and vtype not in violation_categories:
                                                violation_categories.append(vtype)

                                    metadata.violation_categories = violation_categories if violation_categories else None

                                    report_format = ReportFormat[st.session_state.report_format.upper()]
                                    try:
                                        report = st.session_state.report_generator.generate_report(
                                            violations=results.violations,
                                            metadata=metadata,
                                            format=report_format
                                        )
                                        st.session_state.report = report
                                        st.success("✅ OSHA report generated! Edit details below if needed.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Report generation failed: {e}")
                            else:
                                st.error("⚠️ Report generator not initialized. Configure LLM provider in sidebar.")

                    with col_btn2:
                        if st.session_state.report:
                            st.info(f"📄 Report: {st.session_state.report.report_id[:8]}...")
                        else:
                            st.info("💡 No report generated yet")
                else:
                    st.markdown('<div class="success-alert">', unsafe_allow_html=True)
                    st.markdown("### ✅ NO VIOLATIONS")
                    st.markdown("All personnel compliant!")
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("👆 Upload and analyze an image to see results")

    with tab2:
        st.header("🎥 Video Analysis")
        
        # Help text for this tab
        st.markdown("""
        <div style="padding: 1rem; background: rgba(0,212,255,0.05); border-radius: 8px; border-left: 4px solid #00d4ff; margin-bottom: 1.5rem;">
            <h4 style="margin: 0 0 0.5rem 0; color: #00d4ff;">📖 How to Use Video Analysis</h4>
            <p style="margin: 0; font-size: 0.95rem;">
                <strong>Step 1:</strong> Upload a video file (MP4/AVI/MOV/MKV)<br>
                <strong>Step 2:</strong> Adjust frame skip and confidence settings<br>
                <strong>Step 3:</strong> Click "🚀 Process Video" to analyze all frames<br>
                <strong>Step 4:</strong> Download annotated video with detected violations
            </p>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.8;">
                💡 <em>Best for: CCTV footage review, incident investigation, batch processing</em>
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="metric-card">
        <h3>🎬 Video Processing</h3>
        <p>Upload CCTV footage or workplace videos for frame-by-frame PPE detection</p>
        </div>
        """, unsafe_allow_html=True)

        col_vid1, col_vid2 = st.columns([2, 1])

        with col_vid1:
            # Video uploader
            uploaded_video = st.file_uploader(
                "Upload CCTV footage or workplace video",
                type=["mp4", "avi", "mov", "mkv"],
                help="Supported formats: MP4, AVI, MOV, MKV",
                key="video_uploader_tab2"
            )

            if uploaded_video is not None:
                st.video(uploaded_video)

                # Video processing options
                st.markdown("### 🎬 Video Processing Options")

                col_opt1, col_opt2 = st.columns(2)
                with col_opt1:
                    frame_skip = st.slider(
                        "Process every N frames",
                        min_value=1,
                        max_value=10,
                        value=1,
                        help="Process every Nth frame to speed up analysis"
                    )

                with col_opt2:
                    confidence_threshold = st.slider(
                        "Confidence Threshold",
                        min_value=0.1,
                        max_value=0.9,
                        value=0.5,
                        help="Minimum confidence for detections"
                    )

                # Process video button
                if st.button("🚀 Process Video", type="primary"):
                    # Save uploaded video to temp file
                    import tempfile
                    import os

                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                        tmp_file.write(uploaded_video.getvalue())
                        video_path = tmp_file.name

                    try:
                        # Process video
                        with st.spinner("🔄 Processing video frames..."):
                            cap = cv2.VideoCapture(video_path)

                            # Check if video opened successfully
                            if cap is None or not hasattr(cap, 'isOpened') or not cap.isOpened():
                                st.error(f"❌ Cannot open video file: {uploaded_video.name}")
                                st.stop()

                            # Get video properties
                            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                            fps = cap.get(cv2.CAP_PROP_FPS)
                            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                            st.info(f"📹 Video: {total_frames} frames @ {fps:.1f} FPS | {width}x{height}")

                            # Create output video writer with H.264 codec for browser compatibility
                            output_path = video_path.replace('.mp4', '_annotated.mp4')
                            fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264 codec
                            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

                            # Storage for results
                            all_violations = []
                            violation_frames = []
                            frames_processed = 0
                            frame_count = 0

                            # Progress bar
                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            # Store last detection results for frame interpolation
                            last_annotated = None

                            while cap.isOpened():
                                ret, frame = cap.read()
                                if not ret:
                                    break

                                # Process every Nth frame
                                if frame_count % frame_skip == 0:
                                    # Run detection
                                    results = st.session_state.detector.detect(frame, annotate=True)

                                    # Filter detections by confidence
                                    filtered_detections = [
                                        d for d in results.detections
                                        if d.confidence >= confidence_threshold
                                    ]

                                    # Check for violations
                                    violations = []
                                    for detection in filtered_detections:
                                        if not detection.compliant:
                                            violations.append({
                                                'type': detection.class_name,
                                                'bbox': detection.bbox,
                                                'confidence': detection.confidence,
                                                'frame': frame_count,
                                                'timestamp': f"{frame_count/fps:.2f}s"
                                            })

                                    # Store violations
                                    all_violations.extend(violations)

                                    # Create annotated frame
                                    if results.annotated_image is not None:
                                        annotated_rgb = cv2.cvtColor(results.annotated_image, cv2.COLOR_BGR2RGB)
                                        last_annotated = annotated_rgb.copy()
                                    else:
                                        annotated_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                                    # Write to output video
                                    out.write(results.annotated_image if results.annotated_image is not None else frame)

                                    frames_processed += 1

                                # Update progress
                                progress = min(frame_count / total_frames, 1.0)
                                progress_bar.progress(progress)
                                status_text.text(f"Processing frame {frame_count}/{total_frames}...")

                                frame_count += 1

                            # Cleanup
                            cap.release()
                            out.release()

                            # Store results
                            video_results = {
                                'total_frames': total_frames,
                                'frames_processed': frames_processed,
                                'all_violations': all_violations,
                                'violation_count': len(all_violations),
                                'output_path': output_path
                            }
                            st.session_state.video_results = video_results

                        st.success("✅ Video processing completed!")

                        # Display results
                        st.markdown("### 📊 Analysis Results")

                        col_res1, col_res2, col_res3 = st.columns(3)
                        with col_res1:
                            st.metric("🎬 Total Frames", video_results['total_frames'])
                        with col_res2:
                            st.metric("🔄 Frames Processed", video_results['frames_processed'])
                        with col_res3:
                            st.metric("⚠️ Violations Found", video_results['violation_count'])

                        # Show annotated video
                        if os.path.exists(output_path):
                            st.markdown("### 🎥 Annotated Video")
                            st.video(output_path)

                            # Download button
                            with open(output_path, 'rb') as f:
                                st.download_button(
                                    label="📥 Download Annotated Video",
                                    data=f,
                                    file_name=f"{uploaded_video.name.replace('.mp4', '_annotated.mp4')}",
                                    mime="video/mp4"
                                )

                        # Violation details
                        if video_results['violation_count'] > 0:
                            st.markdown("### ⚠️ Violation Details")

                            # Summary by type
                            violation_types = {}
                            for v in all_violations:
                                vtype = v['type']
                                violation_types[vtype] = violation_types.get(vtype, 0) + 1

                            st.markdown("**Violation Summary:**")
                            for vtype, count in violation_types.items():
                                st.markdown(f"- **{vtype.title()}**: {count} instances")

                            # Timeline of violations
                            st.markdown("**Violation Timeline:**")
                            timeline_data = []
                            for vf in violation_frames:
                                timeline_data.append({
                                    'Frame': vf['frame'],
                                    'Time': vf['timestamp'],
                                    'Violations': vf['violation_count']
                                })
                            st.dataframe(timeline_data, width="stretch")

                            # Detailed violations
                            with st.expander("📋 All Violations Detected"):
                                for i, violation in enumerate(video_results['all_violations'][:50], 1):  # Limit display
                                    vtype = violation.get('type', 'unknown').replace('_', ' ').title()
                                    frame = violation.get('frame', 'N/A')
                                    timestamp = violation.get('timestamp', 'N/A')
                                    confidence = violation.get('confidence', 0)
                                    st.markdown(f"**{i}. {vtype}** - Frame {frame} ({timestamp}) - {confidence:.2f} confidence")

                        else:
                            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                            st.markdown("### ✅ No Violations Detected")
                            st.markdown("All frames analyzed showed compliance with safety regulations.")
                            st.markdown('</div>', unsafe_allow_html=True)

                    except Exception as e:
                        st.error(f"❌ Video processing error: {str(e)}")
                    finally:
                        # Cleanup temp files
                        if 'video_path' in locals():
                            try:
                                os.unlink(video_path)
                            except:
                                pass
                        if 'output_path' in locals():
                            try:
                                if os.path.exists(output_path):
                                    os.unlink(output_path)
                            except:
                                pass

        with col_vid2:
            st.markdown("### 💡 Video Analysis Tips")
            st.markdown("""
            - **Frame Skip**: Process every Nth frame for faster analysis
            - **Confidence**: Higher values reduce false positives
            - **Output**: Annotated video shows detected PPE violations
            - **Supported Formats**: MP4, AVI, MOV, MKV
            """)

            if 'video_results' in st.session_state and st.session_state.video_results:
                results = st.session_state.video_results
                st.markdown("### 📈 Quick Stats")
                st.metric("Frames", results.get('frames_processed', 0))
                st.metric("Violations", results.get('violation_count', 0))

    with tab3:
        st.header("📹 Live Webcam Detection")
        
        # Help text for this tab
        st.markdown("""
        <div style="padding: 1rem; background: rgba(0,212,255,0.05); border-radius: 8px; border-left: 4px solid #00d4ff; margin-bottom: 1.5rem;">
            <h4 style="margin: 0 0 0.5rem 0; color: #00d4ff;">📖 How to Use Live Webcam</h4>
            <p style="margin: 0; font-size: 0.95rem;">
                <strong>Step 1:</strong> Select your webcam device from the dropdown<br>
                <strong>Step 2:</strong> Adjust FPS and confidence threshold settings<br>
                <strong>Step 3:</strong> Check "🎬 Start Webcam Stream" to begin real-time monitoring<br>
                <strong>Step 4:</strong> Watch live detection results and statistics
            </p>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.8;">
                💡 <em>Best for: Real-time monitoring, live demonstrations, continuous surveillance</em>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        webcam_detection_page()

    with tab4:
        st.header("🔍 RTSP/ONVIF Camera Monitoring")
        
        # Help text for this tab
        st.markdown("""
        <div style="padding: 1rem; background: rgba(0,212,255,0.05); border-radius: 8px; border-left: 4px solid #00d4ff; margin-bottom: 1.5rem;">
            <h4 style="margin: 0 0 0.5rem 0; color: #00d4ff;">📖 How to Use RTSP Cameras</h4>
            <p style="margin: 0; font-size: 0.95rem;">
                <strong>Step 1:</strong> Click "🔍 Discover ONVIF Cameras" to find IP cameras on your network<br>
                <strong>Step 2:</strong> Enter camera credentials (username/password)<br>
                <strong>Step 3:</strong> Add cameras to your monitoring list<br>
                <strong>Step 4:</strong> Select a camera and start real-time stream processing
            </p>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.8;">
                💡 <em>Best for: Professional CCTV systems, IP cameras, enterprise monitoring</em>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        onvif_detection_page()

        col_vid1, col_vid2 = st.columns([2, 1])

        with col_vid1:
            # Video uploader
            uploaded_video = st.file_uploader(
                "Upload CCTV footage or workplace video",
                type=["mp4", "avi", "mov", "mkv"],
                help="Supported formats: MP4, AVI, MOV, MKV",
                key="video_uploader_tab4"
            )

            if uploaded_video is not None:
                st.video(uploaded_video)

                # Video processing options
                st.markdown("### 🎬 Video Processing Options")

                col_opt1, col_opt2 = st.columns(2)
                with col_opt1:
                    frame_skip = st.slider(
                        "Process every N frames",
                        min_value=1,
                        max_value=30,
                        value=5,
                        help="Skip frames for faster processing (1 = every frame)"
                    )
                with col_opt2:
                    max_frames = st.number_input(
                        "Max frames to process",
                        min_value=10,
                        max_value=1000,
                        value=100,
                        help="Limit total frames analyzed"
                    )

                # Detection button for video
                if st.button("🔍 Analyze Video", type="primary", disabled=st.session_state.detector is None):
                    if st.session_state.detector is None:
                        st.error("⚠️ Please initialize the system first!")
                    else:
                        # Save uploaded video temporarily
                        import tempfile
                        import os

                        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                            tmp_file.write(uploaded_video.read())
                            video_path = tmp_file.name

                        # Process video
                        with st.spinner("🔄 Processing video frames..."):
                            cap = cv2.VideoCapture(video_path)

                            # Check if video opened successfully
                            if cap is None or not hasattr(cap, 'isOpened') or not cap.isOpened():
                                st.error(f"❌ Cannot open video file: {video_path}")
                                st.stop()

                            # Get video properties
                            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                            fps = cap.get(cv2.CAP_PROP_FPS)
                            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                            st.info(f"📹 Video: {total_frames} frames @ {fps:.1f} FPS | {width}x{height}")

                            # Create output video writer with H.264 codec for browser compatibility
                            output_path = video_path.replace('.mp4', '_annotated.mp4')
                            fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264 codec
                            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

                            # Storage for results
                            all_violations = []
                            violation_frames = []
                            frames_processed = 0
                            frame_count = 0

                            # Progress bar
                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            # Store last detection results for frame interpolation
                            last_annotated = None

                            while cap.isOpened():
                                ret, frame = cap.read()
                                if not ret:
                                    break

                                # Process every Nth frame
                                if frame_count % frame_skip == 0:
                                    # Run detection
                                    results = st.session_state.detector.detect(frame, annotate=True)

                                    # Store the annotated frame
                                    if results.annotated_image is not None:
                                        last_annotated = results.annotated_image.copy()
                                        out.write(last_annotated)
                                    else:
                                        last_annotated = frame.copy()
                                        out.write(frame)

                                    if results.has_violations:
                                        # Store violations with timestamp
                                        timestamp = frame_count / fps
                                        for violation in results.violations:
                                            violation['frame'] = frame_count
                                            violation['timestamp'] = f"{int(timestamp//60):02d}:{int(timestamp%60):02d}"
                                            all_violations.append(violation)

                                        # Store annotated frame
                                        violation_frames.append({
                                            'frame_num': frame_count,
                                            'timestamp': f"{int(timestamp//60):02d}:{int(timestamp%60):02d}",
                                            'image': results.annotated_image,
                                            'violation_count': len(results.violations)
                                        })

                                    frames_processed += 1
                                    if frames_processed >= max_frames:
                                        break

                                    progress = min(frames_processed / max_frames, 1.0)
                                    progress_bar.progress(progress)
                                    status_text.text(f"Processed {frames_processed}/{max_frames} frames | Found {len(violation_frames)} violation frames")
                                else:
                                    # Use last annotated frame to prevent blinking
                                    if last_annotated is not None:
                                        out.write(last_annotated)
                                    else:
                                        out.write(frame)

                                frame_count += 1

                            cap.release()
                            out.release()

                            # Read annotated video for display
                            with open(output_path, 'rb') as f:
                                annotated_video_bytes = f.read()

                            # Clean up temp files
                            os.unlink(video_path)
                            os.unlink(output_path)

                            # Store results in session state
                            st.session_state.video_results = {
                                'total_frames': total_frames,
                                'processed_frames': frames_processed,
                                'violation_frames': violation_frames,
                                'all_violations': all_violations,
                                'fps': fps,
                                'annotated_video': annotated_video_bytes
                            }

                            # Send Telegram notification if violations detected in video
                            if all_violations and st.session_state.notifier:
                                try:
                                    st.session_state.notifier.send_violation_alert(
                                        violations=all_violations[:5],  # Send first 5 violations as summary
                                        location=st.session_state.get('location', 'Industrial Site'),
                                        site_id=st.session_state.get('site_id'),
                                        timestamp=datetime.now().isoformat()
                                    )
                                except Exception as e:
                                    logger.error(f"Failed to send Telegram notification: {e}")

                            # Add to history for analytics
                            st.session_state.history.append({
                                'timestamp': datetime.now(),
                                'violations': all_violations,
                                'detections': frames_processed,
                                'inference_time_ms': (frames_processed / fps) * 1000 if fps > 0 else 0
                            })

                            progress_bar.progress(1.0)
                            status_text.text(f"✅ Complete! Processed {frames_processed} frames, found {len(violation_frames)} frames with violations")

                        # Generate report for video if violations found
                        if len(all_violations) > 0 and st.session_state.report_generator:
                            with st.spinner("📝 Generating video incident report..."):
                                metadata = ReportMetadata(
                                    location=st.session_state.location,
                                    timestamp=datetime.now(),
                                    site_id=st.session_state.site_id or None,
                                    inspector_id=st.session_state.inspector_id or None
                                )

                                report_format = ReportFormat[st.session_state.report_format.upper()]

                                try:
                                    report = st.session_state.report_generator.generate_report(
                                        violations=all_violations[:10],  # Limit to first 10 unique violations
                                        metadata=metadata,
                                        format=report_format
                                    )
                                    st.session_state.report = report
                                except Exception as e:
                                    st.warning(f"⚠️ Could not generate report: {e}")
                                    st.session_state.report = None
                        elif len(all_violations) > 0 and not st.session_state.report_generator:
                            st.info("💡 Report generation skipped (API key not configured)")

                        st.success("✅ Video analysis complete!")
                        st.rerun()

        with col_vid2:
            st.markdown("### 💡 Video Tips")
            st.markdown("""
            **Best practices:**
            - Use clear, well-lit footage
            - Recommended: 30 FPS
            - Max resolution: 1080p
            - Skip frames for faster processing

            **Processing time:**
            - 100 frames ~10-20 seconds
            - GPU: 3-5x faster

            **Output:**
            - Annotated video with bounding boxes
            - Violation timeline
            - Frame-by-frame analysis
            - Downloadable video
            """)

        # Display video results if available
        if 'video_results' in st.session_state and st.session_state.video_results is not None:
            st.markdown("---")
            video_results = st.session_state.video_results

            col_vres1, col_vres2 = st.columns([2, 1])

            with col_vres1:
                # Display annotated video
                st.markdown("### 🎬 Annotated Video with Detections")
                st.video(video_results['annotated_video'])

                # Download button for annotated video
                st.download_button(
                    label="⬇️ Download Annotated Video",
                    data=video_results['annotated_video'],
                    file_name=f"ppe_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                    mime="video/mp4"
                )

            with col_vres2:
                # Summary metrics
                st.markdown("### 📊 Summary")
                st.metric("Frames Processed", video_results['processed_frames'])
                st.metric("Violation Frames", len(video_results['violation_frames']))

                if video_results['processed_frames'] > 0:
                    violation_rate = len(video_results['violation_frames']) / video_results['processed_frames'] * 100
                    st.metric("Violation Rate", f"{violation_rate:.1f}%")

            # Display violation frames
            if len(video_results['violation_frames']) > 0:
                st.markdown('<div class="violation-alert">', unsafe_allow_html=True)
                st.markdown(f"### ⚠️ {len(video_results['violation_frames'])} FRAMES WITH VIOLATIONS")
                st.markdown('</div>', unsafe_allow_html=True)

                # Frame selector
                st.markdown("### 🎞️ Violation Frames")
                frame_idx = st.selectbox(
                    "Select frame to view",
                    range(len(video_results['violation_frames'])),
                    format_func=lambda i: f"Frame {video_results['violation_frames'][i]['frame_num']} @ {video_results['violation_frames'][i]['timestamp']} ({video_results['violation_frames'][i]['violation_count']} violations)"
                )

                # Display selected frame
                selected_frame = video_results['violation_frames'][frame_idx]
                frame_rgb = cv2.cvtColor(selected_frame['image'], cv2.COLOR_BGR2RGB)
                st.image(frame_rgb, caption=f"Frame {selected_frame['frame_num']} @ {selected_frame['timestamp']}", width="stretch")

                # Violation timeline
                st.markdown("### 📊 Violation Timeline")
                timeline_data = []
                for vf in video_results['violation_frames']:
                    timeline_data.append({
                        'Frame': vf['frame_num'],
                        'Time': vf['timestamp'],
                        'Violations': vf['violation_count']
                    })
                st.dataframe(timeline_data, width="stretch")

                # Detailed violations
                with st.expander("📋 All Violations Detected"):
                    for i, violation in enumerate(video_results['all_violations'][:50], 1):  # Limit display
                        vtype = violation.get('type', 'unknown').replace('_', ' ').title()
                        frame = violation.get('frame', 'N/A')
                        timestamp = violation.get('timestamp', 'N/A')
                        st.markdown(f"**{i}. {vtype}** - Frame {frame} @ {timestamp}")
            else:
                st.markdown('<div class="success-alert">', unsafe_allow_html=True)
                st.markdown("### ✅ NO VIOLATIONS DETECTED IN VIDEO")
                st.markdown("All frames analyzed showed compliance with safety regulations.")
                st.markdown('</div>', unsafe_allow_html=True)

    with tab5:
        st.header("📊 Analytics Dashboard")
        
        # Help text for this tab
        st.markdown("""
        <div style="padding: 1rem; background: rgba(0,212,255,0.05); border-radius: 8px; border-left: 4px solid #00d4ff; margin-bottom: 1.5rem;">
            <h4 style="margin: 0 0 0.5rem 0; color: #00d4ff;">📖 Understanding Analytics</h4>
            <p style="margin: 0; font-size: 0.95rem;">
                View comprehensive statistics and trends from all your analyses:
            </p>
            <ul style="margin: 0.5rem 0 0 0; font-size: 0.95rem;">
                <li><strong>Violation Trends:</strong> Track safety violations over time</li>
                <li><strong>Compliance Rate:</strong> Monitor overall workplace safety compliance</li>
                <li><strong>Performance Metrics:</strong> System speed and detection accuracy</li>
                <li><strong>Violation Types:</strong> Distribution of different safety violations</li>
            </ul>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.8;">
                💡 <em>Analytics update automatically as you perform more analyses</em>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        create_analytics_charts()

    # Report section (if generated)
    if st.session_state.report is not None:
        st.markdown("---")
        st.header("📄 OSHA Incident Report")

        report = st.session_state.report

        # OSHA Details Editor
        with st.expander("📝 Edit OSHA Report Details", expanded=False):
            st.markdown("### 👤 Worker Information")
            col_edit1, col_edit2 = st.columns(2)

            with col_edit1:
                worker_name = st.text_input("Worker Name", value=report.metadata.worker_name or "", placeholder="Enter worker's full name")
                worker_id = st.text_input("Staff ID", value=report.metadata.worker_id or "", placeholder="Enter staff ID")
                company_name = st.text_input("Company Name", value=report.metadata.company_name or "", placeholder="Enter company/sub-contractor name")

            with col_edit2:
                shift_options = ["Morning", "Afternoon", "Night", "Unknown"]
                current_shift = report.metadata.shift if report.metadata.shift in shift_options else "Unknown"
                shift_info = st.selectbox("Shift", shift_options, index=shift_options.index(current_shift))

                weather_options = ["Sunny", "Cloudy", "Rainy", "Unknown"]
                current_weather = report.metadata.weather_conditions if report.metadata.weather_conditions in weather_options else "Unknown"
                weather = st.selectbox("Weather Conditions", weather_options, index=weather_options.index(current_weather))

            # PPE Violation Editor
            st.markdown("### 🛡️ PPE Violation Checklist")
            st.markdown("*Auto-detected violations are pre-checked. Edit as needed.*")

            ppe_items = {
                "helmet": "Safety Helmet",
                "vest": "Safety Vest",
                "shoes": "Safety Shoes",
                "gloves": "Safety Gloves",
                "goggles": "Safety Goggles",
                "mask": "Face Mask"
            }

            current_violations = report.metadata.violation_categories or []
            updated_violations = []

            cols = st.columns(3)
            for i, (key, label) in enumerate(ppe_items.items()):
                with cols[i % 3]:
                    is_checked = st.checkbox(
                        f"{label}",
                        value=key in current_violations,
                        key=f"edit_violation_{key}",
                        help=f"Auto-detected: {'Yes' if key in current_violations else 'No'}"
                    )
                    if is_checked:
                        updated_violations.append(key)

            # Update button
            if st.button("🔄 Update Report Details", type="secondary"):
                # Update report metadata
                report.metadata.worker_name = worker_name if worker_name else None
                report.metadata.worker_id = worker_id if worker_id else None
                report.metadata.company_name = company_name if company_name else None
                report.metadata.shift = shift_info if shift_info != "Unknown" else None
                report.metadata.weather_conditions = weather if weather != "Unknown" else None
                report.metadata.violation_categories = updated_violations if updated_violations else None

                st.success("✅ Report details updated!")
                st.rerun()

        # Report Summary
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        with col_r1:
            st.metric("Report ID", report.report_id[:8] + "...")
        with col_r2:
            st.metric("Reference No", report.metadata.ref_no or "N/A")
        with col_r3:
            st.metric("Violations", len(report.violations))
        with col_r4:
            st.metric("Penalty", f"RM {report.metadata.penalty_amount:.2f}")

        # OSHA Information Display
        if report.metadata.worker_name or report.metadata.worker_id or report.metadata.company_name:
            st.markdown("### 👷 Worker Details")
            worker_info = []
            if report.metadata.worker_name:
                worker_info.append(f"**Name:** {report.metadata.worker_name}")
            if report.metadata.worker_id:
                worker_info.append(f"**Staff ID:** {report.metadata.worker_id}")
            if report.metadata.company_name:
                worker_info.append(f"**Company:** {report.metadata.company_name}")
            if report.metadata.shift:
                worker_info.append(f"**Shift:** {report.metadata.shift}")
            if report.metadata.weather_conditions:
                worker_info.append(f"**Weather:** {report.metadata.weather_conditions}")

            if worker_info:
                st.markdown(" | ".join(worker_info))

        st.text_area("Report Content", value=report.text, height=300)

        # Export buttons
        st.markdown("### 💾 Download Report")
        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            st.download_button(
                "📋 OSHA PDF Report",
                data=st.session_state.report_generator.generate_pdf_report(report),
                file_name=f"OSHA_Violation_{report.metadata.ref_no or report.report_id}.pdf",
                mime="application/pdf",
                type="primary",
                help="Download professional OSHA-compliant PDF report"
            )
        with col_e2:
            st.download_button(
                "📄 JSON Data",
                data=json.dumps(report.to_dict(), indent=2),
                file_name=f"{report.report_id}.json",
                mime="application/json",
                help="Download report data in JSON format"
            )
        with col_e3:
            st.download_button(
                "📝 Text Report",
                data=report.text,
                file_name=f"{report.report_id}.txt",
                mime="text/plain",
                help="Download report as plain text"
            )

    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: {'#999' if st.session_state.dark_mode else '#666'}; padding: 2rem 0;">
        <p><strong>SiteGuard AI Pro</strong> - Enhanced Edition with Live Detection & Analytics</p>
        <p>Powered by YOLOv8, LLMs & Plotly | CAIE Final Project 2024</p>
        <p style="font-size: 0.9rem;">© 2024 Muhamad Adib bin Suid</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"🚨 Application Error: {str(e)}")
        st.error("Please check the logs for more details.")
        import traceback
        st.code(traceback.format_exc(), language="text")
        logger.error(f"Application startup failed: {e}")
        logger.error(traceback.format_exc())
