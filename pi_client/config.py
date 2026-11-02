"""
ArchiveMind - Raspberry Pi Client Configuration
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Network Configuration
# Supports Dual-Homed connection: Direct Ethernet (10.42.0.1) and Local Wi-Fi (192.168.1.3)
LAPTOP_PRIMARY_IP = os.getenv("LAPTOP_IP", "10.42.0.1")
LAPTOP_IP = LAPTOP_PRIMARY_IP
LAPTOP_WIFI_IP = os.getenv("LAPTOP_WIFI_IP", "192.168.1.3")
LAPTOP_CANDIDATE_IPS = [LAPTOP_PRIMARY_IP, LAPTOP_WIFI_IP]
LAPTOP_PORT = int(os.getenv("LAPTOP_PORT", 8000))
LAPTOP_API_URL = f"http://{LAPTOP_PRIMARY_IP}:{LAPTOP_PORT}"

# Pi Service Configuration
PI_HOST = "0.0.0.0"
PI_PORT = int(os.getenv("PI_PORT", 8082))
DEVICE_ID = os.getenv("DEVICE_ID", "archivemind-pi-cam-01")
DEVICE_NAME = os.getenv("DEVICE_NAME", "Raspberry Pi 3B+ Manuscript Station")

# Storage Configuration
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "/home/abhiroop/archivemind_captures"))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

QUEUE_DIR = STORAGE_DIR / "queue"
QUEUE_DIR.mkdir(parents=True, exist_ok=True)

# Camera Capture Configuration (5MP OmniVision ov5647)
CAMERA_WIDTH = int(os.getenv("CAMERA_WIDTH", 1920))
CAMERA_HEIGHT = int(os.getenv("CAMERA_HEIGHT", 1080))
CAMERA_TIMEOUT_MS = int(os.getenv("CAMERA_TIMEOUT_MS", 1000))
JPEG_QUALITY = int(os.getenv("JPEG_QUALITY", 92))

# Optional Hardware Button (GPIO pin in BCM numbering)
GPIO_CAPTURE_PIN = int(os.getenv("GPIO_CAPTURE_PIN", 17))
GPIO_LED_PIN = int(os.getenv("GPIO_LED_PIN", 27))
