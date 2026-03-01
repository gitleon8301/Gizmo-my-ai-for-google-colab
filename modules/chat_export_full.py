"""
modules/chat_export_full.py — Export chat conversations to PDF, Markdown, JSON.
Supports single-chat and bulk export (zip of all chats).

Optional dependency for PDF:
    pip install reportlab

Markdown and JSON work without any extra dependencies.
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional


def _get_chats_dir(email: str) -> Path:
    try:
        from modules.user_sessions import get_chats_dir
        return get_chats_dir(email)
    except Exception:
        return Path("user_data/sessions") / email / "chats"


# ---------------------------------------------------------------------------
# Markdown export
# ---------------------------------------------------------------------------

def export_markdown(turns: List[Any], title: str = "Chat") -> str:
    lines = [f"# {title}\n"]
    for t in turns:
        if isinstance(t, dict):
            role    = t.get("role", "unknown").capitalize()
            content = t.get("content", str(t))
        else:
            role, content = "Message", str(t)
        lines.append(f"**{role}:**\n\n{content}\n")
    return "\n---\n\n".join(lines)


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------

def export_json(turns: List[Any], title: str = "Chat") -> str:
    return json.dumps({"title": title, "history": turns}, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# PDF export (requires reportlab)
# ---------------------------------------------------------------------------

def export_pdf(turns: List[Any], title: str = "Chat") -> Optional[bytes]:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
        from reportlab.lib.units import cm
    except ImportError:
        print(
            "[chat_export_full] reportlab not installed — PDF export unavailable.\n"
            "  Run: pip install reportlab"
        )
        return None

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 0.5*cm)]

    for t in turns:
        if isinstance(t, dict):
            role    = t.get("role", "unknown").capitalize()
            content = t.get("content", str(t))
        else:
            role, content = "Message", str(t)

        story.append(Paragraph(f"<b>{role}:</b>", styles["Heading3"]))
        # Escape HTML entities for reportlab
        safe = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        story.append(Paragraph(safe, styles["Normal"]))
        story.append(Spacer(1, 0.3*cm))

    doc.build(story)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Single-file export dispatcher
# ---------------------------------------------------------------------------

def export_chat(
    email: str,
    filename: str,
    fmt: str = "markdown",
) -> Optional[bytes]:
    """
    Export a single chat file.

    Parameters
    ----------
    email    : str  — authenticated user email
    filename : str  — chat JSON filename (basename only)
    fmt      : str  — "markdown", "json", or "pdf"

    Returns the exported bytes, or None on failure.
    """
    chat_path = _get_chats_dir(email) / filename
    if not chat_path.exists():
        return None

    try:
        data  = json.loads(chat_path.read_text(encoding="utf-8"))
        turns = data if isinstance(data, list) else data.get("history", [])
        title = data.get("title", chat_path.stem) if isinstance(data, dict) else chat_path.stem
    except Exception:
        return None

    if fmt == "json":
        return export_json(turns, title).encode("utf-8")
    if fmt == "pdf":
        return export_pdf(turns, title)
    return export_markdown(turns, title).encode("utf-8")


# ---------------------------------------------------------------------------
# Bulk export (zip)
# ---------------------------------------------------------------------------

def export_all_zip(email: str, fmt: str = "markdown") -> Optional[bytes]:
    """
    Zip-export every chat the user has.

    Returns the ZIP bytes, or None if there are no chats.
    """
    chats_dir = _get_chats_dir(email)
    if not chats_dir.exists():
        return None

    ext = {"json": "json", "pdf": "pdf"}.get(fmt, "md")
    buf = io.BytesIO()
    count = 0

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for chat_file in sorted(chats_dir.glob("*.json")):
            content = export_chat(email, chat_file.name, fmt)
            if content:
                zf.writestr(f"{chat_file.stem}.{ext}", content)
                count += 1

    if count == 0:
        return None

    buf.seek(0)
    return buf.read()
