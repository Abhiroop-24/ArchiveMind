"""
ArchiveMind - Local Offline Queue Manager for Raspberry Pi
Retains images locally when the laptop server is offline or unreachable.
Persists queue index in JSON format.
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from . import config
except ImportError:
    import config

INDEX_FILE = config.QUEUE_DIR / "queue_index.json"


def _read_index() -> List[Dict[str, Any]]:
    if not INDEX_FILE.exists():
        return []
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _write_index(items: List[Dict[str, Any]]) -> None:
    temp_file = config.QUEUE_DIR / "queue_index.tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)
    temp_file.replace(INDEX_FILE)


def enqueue_scan(capture_meta: Dict[str, Any]) -> None:
    """Adds a capture to the pending upload queue."""
    items = _read_index()
    # Avoid duplicate scans
    if any(item["scan_id"] == capture_meta["scan_id"] for item in items):
        return
    capture_meta["queued_at"] = time.time()
    capture_meta["attempts"] = 0
    items.append(capture_meta)
    _write_index(items)


def peek_queue() -> List[Dict[str, Any]]:
    """Returns list of all pending captures."""
    return _read_index()


def dequeue_scan(scan_id: str) -> Optional[Dict[str, Any]]:
    """Removes a scan from the queue after successful upload."""
    items = _read_index()
    removed = None
    remaining = []
    for item in items:
        if item["scan_id"] == scan_id:
            removed = item
        else:
            remaining.append(item)
    _write_index(remaining)
    return removed


def mark_attempt(scan_id: str, error: str) -> None:
    """Updates attempt count and last error for a pending capture."""
    items = _read_index()
    for item in items:
        if item["scan_id"] == scan_id:
            item["attempts"] = item.get("attempts", 0) + 1
            item["last_error"] = error
            item["last_attempt_at"] = time.time()
            break
    _write_index(items)


def queue_size() -> int:
    return len(_read_index())
