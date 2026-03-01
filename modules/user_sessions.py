"""
modules/user_sessions.py — Per-user session isolation for Gizmo MY-AI.

Each authenticated user gets their own isolated directory under
``user_data/sessions/<sha256_of_email>/`` containing:
  - chats/         — conversation history
  - settings.json  — per-user preferences
  - uploads/       — temporary file uploads

Users cannot access each other's data.  The owner additionally sees
the User Management Panel.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Base path
# ---------------------------------------------------------------------------
_USER_DATA = Path(__file__).resolve().parents[1] / "user_data"
_SESSIONS_ROOT = _USER_DATA / "sessions"


def _session_dir(email: str) -> Path:
    """Return the isolated session directory for *email*."""
    key = hashlib.sha256(email.strip().lower().encode()).hexdigest()
    d = _SESSIONS_ROOT / key
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_session_dir(email: str) -> Path:
    """Return (and create if needed) the session directory for *email*."""
    return _session_dir(email)


def get_chats_dir(email: str) -> Path:
    d = _session_dir(email) / "chats"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_uploads_dir(email: str) -> Path:
    d = _session_dir(email) / "uploads"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_settings(email: str) -> Dict[str, Any]:
    """Load per-user settings.  Returns empty dict if not set."""
    path = _session_dir(email) / "settings.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_settings(email: str, settings: Dict[str, Any]) -> None:
    """Persist per-user settings."""
    path = _session_dir(email) / "settings.json"
    path.write_text(json.dumps(settings, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Active-session tracking (in-memory, best-effort)
# ---------------------------------------------------------------------------
_active_sessions: Dict[str, float] = {}  # email → last-seen timestamp


def mark_active(email: str) -> None:
    """Record that *email* is currently active."""
    _active_sessions[email.lower()] = time.time()


def mark_inactive(email: str) -> None:
    """Remove *email* from the active session list."""
    _active_sessions.pop(email.lower(), None)


def get_active_users(max_idle_seconds: int = 300) -> List[str]:
    """Return list of emails seen within the last *max_idle_seconds*."""
    cutoff = time.time() - max_idle_seconds
    return [e for e, t in _active_sessions.items() if t >= cutoff]


# ---------------------------------------------------------------------------
# Owner: User Management Panel data
# ---------------------------------------------------------------------------

def list_all_users() -> List[Dict[str, Any]]:
    """
    Return metadata for every user who has a session directory.

    Used by the Admin Panel (owner only).
    """
    users: List[Dict[str, Any]] = []
    if not _SESSIONS_ROOT.exists():
        return users

    # Load the allow-list to map hashes → emails
    try:
        from modules.auth_google import load_allowed_emails
        allowed = load_allowed_emails()
    except Exception:
        allowed = []

    hash_to_email = {
        hashlib.sha256(e.encode()).hexdigest(): e for e in allowed
    }

    for entry in _SESSIONS_ROOT.iterdir():
        if not entry.is_dir():
            continue
        email = hash_to_email.get(entry.name, f"<unknown:{entry.name[:8]}…>")
        last_seen = _active_sessions.get(email.lower(), 0)
        chats_dir = entry / "chats"
        num_chats = len(list(chats_dir.glob("*.json"))) if chats_dir.exists() else 0
        users.append({
            "email":     email,
            "hash":      entry.name,
            "num_chats": num_chats,
            "last_seen": last_seen,
            "active":    email.lower() in get_active_users(),
        })

    return sorted(users, key=lambda u: u["last_seen"], reverse=True)


def revoke_user_session(email: str) -> None:
    """Mark a user's session as revoked (owner action)."""
    mark_inactive(email)
    # Optionally clear the session directory (uncomment if desired):
    # import shutil
    # d = _session_dir(email)
    # shutil.rmtree(d, ignore_errors=True)
