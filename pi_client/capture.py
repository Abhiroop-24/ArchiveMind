"""
ArchiveMind - Manuscript Camera Capture Module
Acquires high-resolution images via Raspberry Pi Camera Module 5MP (ov5647).
Calculates SHA-256 cryptographic checksums for chain-of-custody.
"""

import os
import subprocess
import hashlib
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from . import config
except ImportError:
    import config


def compute_sha256(filepath: str) -> str:
    """Calculates SHA-256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_image_file(filepath: str) -> bool:
    """Validates that file exists, has content > 10KB, and has valid JPEG header."""
    path = Path(filepath)
    if not path.exists():
        return False
    size = path.stat().st_size
    if size < 10240:  # Minimum 10 KB
        return False
    # Check JPEG SOI marker (0xFF, 0xD8)
    try:
        with open(filepath, "rb") as f:
            header = f.read(2)
            return header == b"\xff\xd8"
    except Exception:
        return False


def capture_manuscript(custom_scan_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes rpicam-still to capture a high-resolution manuscript image.
    Returns metadata dict including file path, SHA-256, dimensions, and timestamp.
    """
    scan_id = custom_scan_id or f"scan_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    filename = f"{scan_id}.jpg"
    target_path = config.STORAGE_DIR / filename

    # Attempt capture with rpicam-still (headless mode: -n --nopreview)
    cmd = [
        "rpicam-still",
        "-n",
        "-t", str(config.CAMERA_TIMEOUT_MS),
        "-o", str(target_path),
        "--width", str(config.CAMERA_WIDTH),
        "--height", str(config.CAMERA_HEIGHT),
        "-q", str(config.JPEG_QUALITY)
    ]

    captured_ok = False
    error_msg = None

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        if proc.returncode == 0 and validate_image_file(str(target_path)):
            captured_ok = True
        else:
            error_msg = proc.stderr.strip() or "Image validation failed"
    except FileNotFoundError:
        # Try legacy libcamera-still
        try:
            cmd[0] = "libcamera-still"
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            if proc.returncode == 0 and validate_image_file(str(target_path)):
                captured_ok = True
            else:
                error_msg = proc.stderr.strip() or "libcamera validation failed"
        except Exception as e:
            error_msg = f"Camera CLI error: {str(e)}"
    except Exception as e:
        error_msg = f"Capture exception: {str(e)}"

    if not captured_ok:
        raise RuntimeError(f"Manuscript capture failed: {error_msg}")

    # Compute cryptographic checksum
    checksum = compute_sha256(str(target_path))
    filesize = target_path.stat().st_size

    return {
        "scan_id": scan_id,
        "device_id": config.DEVICE_ID,
        "filename": filename,
        "filepath": str(target_path),
        "filesize": filesize,
        "checksum_sha256": checksum,
        "width": config.CAMERA_WIDTH,
        "height": config.CAMERA_HEIGHT,
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


if __name__ == "__main__":
    print(f"Triggering test capture on {config.DEVICE_NAME}...")
    try:
        meta = capture_manuscript()
        print("Capture successful:")
        for k, v in meta.items():
            print(f"  {k}: {v}")
    except Exception as ex:
        print(f"Capture failed: {ex}")
