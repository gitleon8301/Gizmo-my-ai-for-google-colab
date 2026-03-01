"""
modules/api_keys.py — Personal API key management for Gizmo MY-AI.

Keys are generated per user from the Settings page, stored as bcrypt hashes,
and used as Bearer tokens on /api/ endpoints.

Dependencies (lazy-imported):
    pip install bcrypt

No plaintext keys are ever stored after initial generation.
"""

from __future__ import annotations

import json
import os
import secrets
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Storage path
# ---------------------------------------------------------------------------
_USER_DATA = Path(__file__).resolve().parents[1] / "user_data"
_KEYS_FILE  = _USER_DATA / "api_keys.json"
_KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_db() -> Dict[str, Any]:
    if _KEYS_FILE.exists():
        try:
            return json.loads(_KEYS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_db(db: Dict[str, Any]) -> None:
    _KEYS_FILE.write_text(json.dumps(db, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# bcrypt helpers
# ---------------------------------------------------------------------------
def _hash_key(plaintext: str) -> str:
    try:
        import bcrypt
        return bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt()).decode()
    except ImportError:
        print("[api_keys] bcrypt not installed. Run: pip install bcrypt")
        raise


def _verify_key(plaintext: str, hashed: str) -> bool:
    try:
        import bcrypt
        return bcrypt.checkpw(plaintext.encode(), hashed.encode())
    except ImportError:
        return False
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_api_key(email: str, label: str = "") -> str:
    """
    Generate a new API key for *email*, store its hash, return the plaintext.

    The plaintext is returned ONLY here — it is never stored.
    """
    plaintext = "gizmo-" + secrets.token_urlsafe(32)
    hashed = _hash_key(plaintext)

    db = _load_db()
    user_keys: List[Dict] = db.get(email.lower(), [])
    user_keys.append({
        "hash":       hashed,
        "label":      label or f"key-{len(user_keys)+1}",
        "created_at": time.time(),
        "revoked":    False,
    })
    db[email.lower()] = user_keys
    _save_db(db)
    return plaintext


def verify_api_key(plaintext: str) -> Optional[str]:
    """
    Verify a Bearer token and return the associated email, or None.
    """
    if not plaintext:
        return None
    db = _load_db()
    for email, keys in db.items():
        for entry in keys:
            if not entry.get("revoked") and _verify_key(plaintext, entry["hash"]):
                return email
    return None


def list_keys(email: str) -> List[Dict]:
    """Return key metadata (never the hash) for *email*."""
    db = _load_db()
    return [
        {
            "label":      k["label"],
            "created_at": k["created_at"],
            "revoked":    k.get("revoked", False),
            "index":      i,
        }
        for i, k in enumerate(db.get(email.lower(), []))
    ]


def revoke_key(email: str, index: int) -> bool:
    """Revoke key at *index* for *email*.  Returns True on success."""
    db = _load_db()
    keys = db.get(email.lower(), [])
    if 0 <= index < len(keys):
        keys[index]["revoked"] = True
        db[email.lower()] = keys
        _save_db(db)
        return True
    return False


def revoke_all_keys(email: str) -> None:
    """Owner action: revoke all keys belonging to *email*."""
    db = _load_db()
    for entry in db.get(email.lower(), []):
        entry["revoked"] = True
    _save_db(db)
