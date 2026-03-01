"""
modules/watchdog.py — Auto-restart watchdog for Gizmo MY-AI.

Pings the Gradio health endpoint every 15 seconds.
If the server stops responding:
  1. Attempts to restart (max 3 times).
  2. Sends a desktop notification via notify-send (Fedora / KDE Plasma).
  3. Writes a crash log to user_data/logs/watchdog.log.

Usage::

    from modules.watchdog import start_watchdog
    start_watchdog(port=7860)
"""

from __future__ import annotations

import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
_LOG_DIR  = Path(__file__).resolve().parents[1] / "user_data" / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE = _LOG_DIR / "watchdog.log"

PING_INTERVAL_S = 15
MAX_RESTARTS    = 3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log(msg: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    try:
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _notify(title: str, body: str) -> None:
    """Send a desktop notification via notify-send (non-blocking, best-effort)."""
    try:
        subprocess.run(
            ["notify-send", "--urgency=critical", "--icon=dialog-error", title, body],
            timeout=3,
        )
    except Exception:
        pass


def _ping(port: int) -> bool:
    """Return True if the server responds to a health check."""
    try:
        url = f"http://127.0.0.1:{port}/"
        with urllib.request.urlopen(url, timeout=5) as resp:
            return resp.status < 500
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Watchdog thread
# ---------------------------------------------------------------------------

class _Watchdog(threading.Thread):
    def __init__(self, port: int, cmd: Optional[list] = None) -> None:
        super().__init__(daemon=True, name="gizmo-watchdog")
        self.port     = port
        self.cmd      = cmd or [sys.executable, "server.py", "--listen"]
        self._stop    = threading.Event()
        self._restarts = 0

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        _log("Watchdog started.")
        while not self._stop.is_set():
            self._stop.wait(PING_INTERVAL_S)
            if self._stop.is_set():
                break
            if not _ping(self.port):
                self._handle_crash()

    def _handle_crash(self) -> None:
        if self._restarts >= MAX_RESTARTS:
            msg = f"Max restarts ({MAX_RESTARTS}) reached — giving up."
            _log(msg)
            _notify("Gizmo MY-AI Crashed", msg)
            return

        self._restarts += 1
        _log(f"Server unreachable — restart attempt {self._restarts}/{MAX_RESTARTS}")
        _notify("Gizmo MY-AI", f"Server down — restarting ({self._restarts}/{MAX_RESTARTS})…")

        try:
            subprocess.Popen(self.cmd)
            time.sleep(10)  # Allow time for restart
            if _ping(self.port):
                _log("Server recovered successfully.")
                self._restarts = 0  # Reset on recovery
            else:
                _log("Server did not recover after restart.")
        except Exception as exc:
            _log(f"Restart failed: {exc}")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

_watchdog_instance: Optional[_Watchdog] = None


def start_watchdog(port: int = 7860, cmd: Optional[list] = None) -> None:
    """
    Start the watchdog daemon thread.

    Call once during application startup.
    """
    global _watchdog_instance
    if _watchdog_instance and _watchdog_instance.is_alive():
        return  # Already running
    _watchdog_instance = _Watchdog(port=port, cmd=cmd)
    _watchdog_instance.start()


def stop_watchdog() -> None:
    """Stop the watchdog thread gracefully."""
    global _watchdog_instance
    if _watchdog_instance:
        _watchdog_instance.stop()
        _watchdog_instance = None
