"""
modules/request_queue.py — FIFO inference queue + per-user rate limiter.

The RTX 4080 runs one generation at a time.  All requests enter a thread-safe
FIFO queue.  Queue position and estimated wait time are exposed so the UI
can display them.

Rate limiting:
  • max_requests_per_minute (config.yaml) — per-user token bucket
  • Owner email is always exempt from rate limits

Storage limits (checked but NOT enforced here — UI reads the values):
  • max_model_storage_gb_per_user (default 100 GB)
  • max_chat_storage_gb total (default 50 GB)
"""

from __future__ import annotations

import threading
import time
from collections import deque
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
def _load_config() -> dict:
    try:
        import yaml
        cfg_path = Path(__file__).resolve().parents[1] / "config.yaml"
        with open(cfg_path) as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _get_limits() -> Tuple[int, int]:
    """Return (max_requests_per_minute, max_concurrent_users)."""
    cfg = _load_config()
    rl = cfg.get("rate_limits", {})
    return (
        int(rl.get("max_requests_per_minute", 8)),
        int(rl.get("max_concurrent_users", 6)),
    )


def _get_owner_email() -> str:
    try:
        from modules.auth_google import get_owner_email
        return get_owner_email()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Per-user rate limiter (token bucket, 1-minute window)
# ---------------------------------------------------------------------------
class _UserBucket:
    def __init__(self, max_per_minute: int) -> None:
        self.max_per_minute = max_per_minute
        self._lock = threading.Lock()
        self._timestamps: deque[float] = deque()

    def is_allowed(self) -> bool:
        """Return True if the user is within their rate limit."""
        now = time.monotonic()
        with self._lock:
            # Remove timestamps older than 60 s
            while self._timestamps and now - self._timestamps[0] > 60:
                self._timestamps.popleft()
            if len(self._timestamps) >= self.max_per_minute:
                return False
            self._timestamps.append(now)
            return True

    def seconds_until_next(self) -> float:
        """Seconds until the oldest request falls outside the 60-s window."""
        if not self._timestamps:
            return 0.0
        return max(0.0, 60.0 - (time.monotonic() - self._timestamps[0]))


# ---------------------------------------------------------------------------
# Global queue state
# ---------------------------------------------------------------------------
_queue_lock   = threading.Lock()
_queue: deque[Tuple[str, Callable, Any, threading.Event]] = deque()
_running      = False
_worker_thread: Optional[threading.Thread] = None
_user_buckets: Dict[str, _UserBucket] = {}
_queue_result: Dict[str, Any] = {}   # request_id → result (for polling)


def _get_bucket(email: str, max_per_minute: int) -> _UserBucket:
    key = email.lower()
    if key not in _user_buckets:
        _user_buckets[key] = _UserBucket(max_per_minute)
    return _user_buckets[key]


# ---------------------------------------------------------------------------
# Queue worker (runs in a daemon thread)
# ---------------------------------------------------------------------------
def _run_worker() -> None:
    global _running
    while True:
        with _queue_lock:
            if not _queue:
                _running = False
                return
            req_id, fn, kwargs, done_event = _queue.popleft()

        try:
            result = fn(**kwargs) if isinstance(kwargs, dict) else fn(kwargs)
        except Exception as exc:
            result = {"error": str(exc)}

        _queue_result[req_id] = result
        done_event.set()


def _ensure_worker() -> None:
    global _running, _worker_thread
    if not _running:
        _running = True
        _worker_thread = threading.Thread(target=_run_worker, daemon=True)
        _worker_thread.start()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def enqueue(
    email: str,
    fn: Callable,
    kwargs: Any,
    request_id: Optional[str] = None,
) -> Tuple[bool, str, Optional[threading.Event]]:
    """
    Add a generation request to the FIFO queue.

    Returns
    -------
    (accepted, message, done_event)
        accepted   — False if the user is rate-limited
        message    — human-readable status string
        done_event — threading.Event set when the job completes (or None)
    """
    max_rpm, _ = _get_limits()
    owner = _get_owner_email()
    is_owner = email.lower() == owner.lower() and owner

    if not is_owner:
        bucket = _get_bucket(email, max_rpm)
        if not bucket.is_allowed():
            wait = bucket.seconds_until_next()
            return False, f"⏳ Rate limit — try again in {wait:.0f}s", None

    if request_id is None:
        import uuid
        request_id = str(uuid.uuid4())

    done_event = threading.Event()

    with _queue_lock:
        _queue.append((request_id, fn, kwargs, done_event))
        position = len(_queue)
        _ensure_worker()

    msg = f"✅ Queued (position {position})" if position > 1 else "✅ Processing"
    return True, msg, done_event


def queue_length() -> int:
    """Return the current number of pending requests."""
    with _queue_lock:
        return len(_queue)


def queue_position(request_id: str) -> int:
    """Return the 1-based position of *request_id* in the queue, or 0 if not found."""
    with _queue_lock:
        for i, (rid, *_) in enumerate(_queue):
            if rid == request_id:
                return i + 1
    return 0


def estimated_wait_seconds(request_id: str, seconds_per_request: float = 30.0) -> float:
    """Rough ETA for *request_id* based on queue position."""
    pos = queue_position(request_id)
    return pos * seconds_per_request


def get_result(request_id: str) -> Any:
    """Return the stored result for a completed request, or None."""
    return _queue_result.pop(request_id, None)
