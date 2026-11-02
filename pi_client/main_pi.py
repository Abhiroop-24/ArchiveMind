"""
ArchiveMind - Raspberry Pi Acquisition Daemon
Runs as an autostart systemd service on the headless Raspberry Pi 3B+.
Listens for remote capture requests from the laptop dashboard and supports hardware button capture.
Handles retry queue, device registration, and local storage.
"""

import os
import sys
import time
import json
import threading
import threading
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

try:
    from . import config
    from . import capture
    from . import uploader
    from . import queue_manager
except ImportError:
    import config
    import capture
    import uploader
    import queue_manager

# Optional GPIO button support
BUTTON_AVAILABLE = False
try:
    from gpiozero import Button
    button = Button(config.GPIO_CAPTURE_PIN, bounce_time=0.2)
    BUTTON_AVAILABLE = True
except Exception:
    pass


_LAPTOP_ONLINE = False
_LAST_PROBE_TIME = 0

def is_laptop_reachable():
    global _LAPTOP_ONLINE, _LAST_PROBE_TIME
    now = time.time()
    if now - _LAST_PROBE_TIME > 5.0:
        _LAST_PROBE_TIME = now
        try:
            _LAPTOP_ONLINE = uploader.check_laptop_online(timeout_sec=0.25)
        except Exception:
            _LAPTOP_ONLINE = False
    return _LAPTOP_ONLINE


class PiDaemonHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send_json(200, {"status": "ok"})

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/status", "/health", "/api/status"):
            is_laptop_up = is_laptop_reachable()
            self._send_json(200, {
                "status": "online",
                "device_id": config.DEVICE_ID,
                "device_name": config.DEVICE_NAME,
                "camera_type": "5MP ov5647",
                "laptop_primary_ip": getattr(config, "LAPTOP_PRIMARY_IP", "10.42.0.1"),
                "laptop_wifi_ip": getattr(config, "LAPTOP_WIFI_IP", "192.168.1.3"),
                "active_laptop_url": uploader.get_active_laptop_base(probe_timeout=0.2),
                "laptop_online": is_laptop_up,
                "queue_size": queue_manager.queue_size(),
                "resolution": f"{config.CAMERA_WIDTH}x{config.CAMERA_HEIGHT}",
                "button_supported": BUTTON_AVAILABLE,
                "timestamp": time.time()
            })
        elif parsed.path in ("/snapshot.jpg", "/api/snapshot"):
            frame = capture.get_live_frame_bytes()
            if frame:
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(frame)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.end_headers()
                self.wfile.write(frame)
            else:
                self._send_json(503, {"error": "Camera frame not available"})
        elif parsed.path in ("/stream", "/stream.mjpg", "/api/stream"):
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.end_headers()
            try:
                while True:
                    frame = capture.get_live_frame_bytes()
                    if frame:
                        self.wfile.write(b"--frame\r\n")
                        self.wfile.write(b"Content-Type: image/jpeg\r\n")
                        self.wfile.write(f"Content-Length: {len(frame)}\r\n\r\n".encode("utf-8"))
                        self.wfile.write(frame)
                        self.wfile.write(b"\r\n")
                    time.sleep(0.04)  # ~25 FPS
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception:
                pass
        elif parsed.path == "/queue":
            self._send_json(200, {
                "queue_size": queue_manager.queue_size(),
                "pending": queue_manager.peek_queue()
            })
        else:
            self._send_json(404, {"error": "Endpoint not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/capture", "/api/capture"):
            try:
                # 1. Capture image
                capture_meta = capture.capture_manuscript()
                upload_res = None
                uploaded = False

                # 2. Try uploading to laptop
                try:
                    upload_res = uploader.upload_scan(capture_meta)
                    uploaded = True
                except Exception as upload_err:
                    # Enqueue for later upload
                    queue_manager.enqueue_scan(capture_meta)
                    upload_res = {"queued": True, "error": str(upload_err)}

                self._send_json(200, {
                    "success": True,
                    "uploaded": uploaded,
                    "scan_id": capture_meta["scan_id"],
                    "checksum_sha256": capture_meta["checksum_sha256"],
                    "filepath": capture_meta["filepath"],
                    "upload_response": upload_res
                })
            except Exception as e:
                self._send_json(500, {"success": False, "error": str(e)})

        elif parsed.path == "/flush_queue":
            count = uploader.drain_offline_queue()
            self._send_json(200, {"success": True, "uploaded_count": count})
        else:
            self._send_json(404, {"error": "Endpoint not found"})

    def log_message(self, format, *args):
        # Concise logging to stdout for systemd journalctl
        sys.stdout.write(f"[PiDaemon {time.strftime('%X')}] {args[0]} - {args[1]}\n")
        sys.stdout.flush()


def background_worker():
    """Background loop to periodically register with laptop and flush offline queue."""
    registered = False
    while True:
        try:
            if not registered:
                if uploader.check_laptop_online(timeout_sec=1.5):
                    if uploader.register_device():
                        print(f"[OK] Registered device {config.DEVICE_ID} with laptop {config.LAPTOP_IP}")
                        registered = True

            # If there are items in the offline queue, attempt to drain
            if queue_manager.queue_size() > 0:
                count = uploader.drain_offline_queue()
                if count > 0:
                    print(f"[OK] Uploaded {count} queued captures to laptop")
        except Exception as e:
            pass
        time.sleep(10)


def on_hardware_button_pressed():
    """Callback for physical capture button on GPIO pin."""
    print("[EVENT] Hardware capture button pressed! Acquiring image...")
    try:
        meta = capture.capture_manuscript()
        try:
            uploader.upload_scan(meta)
            print(f"[OK] Uploaded scan {meta['scan_id']} to laptop")
        except Exception as err:
            queue_manager.enqueue_scan(meta)
            print(f"[WARNING] Laptop unreachable, queued scan {meta['scan_id']}: {err}")
    except Exception as e:
        print(f"[ERROR] Button capture failed: {e}")


def run_daemon():
    print(f"=================================================")
    print(f"  ArchiveMind Raspberry Pi Acquisition Daemon")
    print(f"  Device: {config.DEVICE_NAME} ({config.DEVICE_ID})")
    print(f"  Laptop Target: http://{config.LAPTOP_IP}:{config.LAPTOP_PORT}")
    print(f"  Listening on: http://{config.PI_HOST}:{config.PI_PORT}")
    print(f"=================================================")

    # Wire up hardware button if present
    if BUTTON_AVAILABLE:
        button.when_pressed = on_hardware_button_pressed
        print(f"[OK] Hardware capture button active on GPIO {config.GPIO_CAPTURE_PIN}")

    # Start background retry worker thread
    bg_thread = threading.Thread(target=background_worker, daemon=True)
    bg_thread.start()

    # Pre-warm shared Picamera2 stream
    try:
        capture.get_shared_picam()
    except Exception as e:
        print(f"[NOTICE] Camera pre-warm notice: {e}")

    server = ThreadingHTTPServer((config.PI_HOST, config.PI_PORT), PiDaemonHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Pi Daemon...")
        server.server_close()


if __name__ == "__main__":
    run_daemon()
