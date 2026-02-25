"""Shared AI model calling utility."""
from __future__ import annotations

from typing import Optional, Tuple


def call_ai(prompt: str, max_tokens: int = 1024) -> Tuple[Optional[str], Optional[str]]:
    """Call the AI model with the given prompt. Returns (output, error)."""
    try:
        from modules import shared
        if shared.model is None:
            return None, "❌ No AI model loaded. Please load a model first."
        state = shared.settings.copy()
        state['max_new_tokens'] = max_tokens
        from modules.text_generation import generate_reply
        output = ""
        for chunk in generate_reply(prompt, state, stopping_strings=[], is_chat=False):
            if isinstance(chunk, str):
                output = chunk
            elif isinstance(chunk, (list, tuple)) and len(chunk) > 0:
                output = chunk[0] if isinstance(chunk[0], str) else str(chunk[0])
        return output.strip(), None
    except Exception as exc:
        return None, f"❌ AI error: {exc}"
