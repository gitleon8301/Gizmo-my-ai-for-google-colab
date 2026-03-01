"""
modules/audit_enhanced.py — Append-only JSON audit log for Gizmo MY-AI.

Records:
  login / denied / logout
  model_load / model_unload / model_download
  generation_start / generation_complete / generation_cancel
  training_start / training_complete / training_cancel
  settings_change
  api_key_generate / api_key_revoke
  user_revoke / user_add

The log is stored in user_data/logs/audit.jsonl (newline-delimited JSON).
It is readable in the Admin Panel (owner only).
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Log file location
# ---------------------------------------------------------------------------
_LOG_DIR  = Path(__file__).resolve().parents[1] / "user_data" / "logs"
_LOG_FILE = _LOG_DIR / "audit.jsonl"
_LOCK     = threading.Lock()

_LOG_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Core writer
# ---------------------------------------------------------------------------

def log_event(
    event_type: str,
    email: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Append one audit record to the JSONL log.

    Parameters
    ----------
    event_type : str
        One of the event types listed in the module docstring.
    email : str | None
        The user associated with this event.
    details : dict | None
        Any additional fields to record.
    """
    record: Dict[str, Any] = {
        "ts":         time.time(),
        "event":      event_type,
        "email":      (email or "").lower() or None,
    }
    if details:
        record.update(details)

    line = json.dumps(record, ensure_ascii=False) + "\n"
    with _LOCK:
        try:
            with open(_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as exc:
            print(f"[audit_enhanced] write error (non-fatal): {exc}")


# ---------------------------------------------------------------------------
# Convenience wrappers
# ---------------------------------------------------------------------------

def log_login(email: str) -> None:
    log_event("login", email)

def log_denied(email: str) -> None:
    log_event("denied", email)

def log_logout(email: str) -> None:
    log_event("logout", email)

def log_model_load(email: str, model_name: str) -> None:
    log_event("model_load", email, {"model": model_name})

def log_model_unload(model_name: str) -> None:
    log_event("model_unload", details={"model": model_name})

def log_model_download(email: str, model_name: str, size_gb: float) -> None:
    log_event("model_download", email, {"model": model_name, "size_gb": size_gb})

def log_generation_start(email: str, model_name: str) -> None:
    log_event("generation_start", email, {"model": model_name})

def log_generation_complete(email: str, tokens: int = 0) -> None:
    log_event("generation_complete", email, {"tokens": tokens})

def log_generation_cancel(email: str) -> None:
    log_event("generation_cancel", email)

def log_training_start(email: str, job_id: str) -> None:
    log_event("training_start", email, {"job_id": job_id})

def log_training_complete(email: str, job_id: str) -> None:
    log_event("training_complete", email, {"job_id": job_id})

def log_settings_change(email: str, key: str) -> None:
    log_event("settings_change", email, {"key": key})

def log_api_key_generate(email: str, label: str) -> None:
    log_event("api_key_generate", email, {"label": label})

def log_api_key_revoke(email: str, label: str) -> None:
    log_event("api_key_revoke", email, {"label": label})

def log_user_revoke(owner_email: str, target_email: str) -> None:
    log_event("user_revoke", owner_email, {"target": target_email})

def log_user_add(owner_email: str, new_email: str) -> None:
    log_event("user_add", owner_email, {"new_user": new_email})


# ---------------------------------------------------------------------------
# Reader (Admin Panel)
# ---------------------------------------------------------------------------

def read_recent(n: int = 200) -> list[Dict[str, Any]]:
    """Return the last *n* audit records, most-recent first."""
    if not _LOG_FILE.exists():
        return []
    try:
        lines = _LOG_FILE.read_text(encoding="utf-8").splitlines()
        records = []
        for line in lines:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
        return list(reversed(records[-n:]))
    except Exception:
        return []
