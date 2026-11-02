"""
ArchiveMind - Raspberry Pi Uploader Module
Transfers captured manuscript images to the Laptop FastAPI server via direct Ethernet (HTTP).
Handles network checks, retry logic, and queue draining.
"""

import os
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from . import config
    from . import queue_manager
except ImportError:
    import config
    import queue_manager


def check_laptop_online(timeout_sec: float = 2.0) -> bool:
    """Checks if Laptop FastAPI server is reachable."""
    url = f"{config.LAPTOP_API_URL}/api/health"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ArchiveMind-PiClient/1.0"})
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            return resp.status == 200
    except Exception:
        return False


def register_device() -> bool:
    """Registers this Pi device with the central ArchiveMind laptop registry."""
    url = f"{config.LAPTOP_API_URL}/api/devices/register"
    payload = json.dumps({
        "device_id": config.DEVICE_ID,
        "device_name": config.DEVICE_NAME,
        "device_type": "Raspberry Pi 3B+ (5MP ov5647)",
        "ip_address": "10.42.0.116"
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "ArchiveMind-PiClient/1.0"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            return resp.status in (200, 201)
    except Exception as e:
        return False


def upload_scan(capture_meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Uploads a captured manuscript image and its checksum to the laptop ingestion API.
    Uses standard multipart/form-data encoding without third-party dependencies.
    """
    filepath = capture_meta["filepath"]
    filename = capture_meta["filename"]
    scan_id = capture_meta["scan_id"]
    checksum = capture_meta.get("checksum_sha256", "")
    device_id = capture_meta.get("device_id", config.DEVICE_ID)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Image not found at {filepath}")

    with open(filepath, "rb") as f:
        file_bytes = f.read()

    boundary = "----ArchiveMindBoundary" + hex(int(time.time() * 1000))[2:]
    body = bytearray()

    # Field: scan_id
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="scan_id"\r\n\r\n{scan_id}\r\n'.encode("utf-8"))

    # Field: device_id
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="device_id"\r\n\r\n{device_id}\r\n'.encode("utf-8"))

    # Field: checksum_sha256
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="checksum_sha256"\r\n\r\n{checksum}\r\n'.encode("utf-8"))

    # Field: file
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode("utf-8"))
    body.extend(b"Content-Type: image/jpeg\r\n\r\n")
    body.extend(file_bytes)
    body.extend(b"\r\n")

    # Closing boundary
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    url = f"{config.LAPTOP_API_URL}/api/ingestion/upload"
    req = urllib.request.Request(
        url,
        data=bytes(body),
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "ArchiveMind-PiClient/1.0"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8") if e.fp else str(e)
        raise RuntimeError(f"HTTP Error {e.code}: {err_msg}")
    except Exception as e:
        raise RuntimeError(f"Network error during upload: {str(e)}")


def drain_offline_queue() -> int:
    """Attempts to upload any queued scans that were stored offline."""
    pending = queue_manager.peek_queue()
    if not pending:
        return 0

    if not check_laptop_online(timeout_sec=1.5):
        return 0

    successful = 0
    for item in pending:
        try:
            upload_scan(item)
            queue_manager.dequeue_scan(item["scan_id"])
            successful += 1
        except Exception as e:
            queue_manager.mark_attempt(item["scan_id"], str(e))
    return successful
