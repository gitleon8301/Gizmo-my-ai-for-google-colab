"""
modules/chat_search.py — Full-text chat search for Gizmo MY-AI.

Searches only the authenticated user's isolated session folder.
Uses simple substring / trigram matching — no external dependencies.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List


def _get_chats_dir(email: str) -> Path:
    try:
        from modules.user_sessions import get_chats_dir
        return get_chats_dir(email)
    except Exception:
        return Path("user_data/sessions") / email / "chats"


def _snippet(text: str, query: str, radius: int = 80) -> str:
    """Extract a snippet of *text* centred around *query*."""
    idx = text.lower().find(query.lower())
    if idx == -1:
        return text[:radius * 2]
    start = max(0, idx - radius)
    end   = min(len(text), idx + len(query) + radius)
    snippet = ("…" if start > 0 else "") + text[start:end] + ("…" if end < len(text) else "")
    # Bold the match
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    snippet = pattern.sub(lambda m: f"**{m.group()}**", snippet)
    return snippet


def search_chats(email: str, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
    """
    Search the user's chat history for *query*.

    Returns a list of dicts with keys: title, snippet, date, filename.
    """
    if not query.strip():
        return []

    chats_dir = _get_chats_dir(email)
    if not chats_dir.exists():
        return []

    results: List[Dict[str, Any]] = []
    q_lower = query.lower()

    for chat_file in sorted(chats_dir.glob("*.json"), reverse=True):
        try:
            data = json.loads(chat_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        # Support both list-of-turns and {"history": [...]} formats
        turns = data if isinstance(data, list) else data.get("history", [])
        title = data.get("title", chat_file.stem) if isinstance(data, dict) else chat_file.stem
        date  = data.get("date", "") if isinstance(data, dict) else ""

        full_text = " ".join(
            str(t.get("content", t) if isinstance(t, dict) else t)
            for t in turns
        )

        if q_lower in full_text.lower():
            results.append({
                "title":    title,
                "snippet":  _snippet(full_text, query),
                "date":     date,
                "filename": chat_file.name,
            })
            if len(results) >= max_results:
                break

    return results
