"""
modules/ollama_backend.py — Ollama backend support for Gizmo MY-AI.

Auto-detects a running Ollama instance at localhost:11434.
Adds Ollama models to the model selector and supports pulling new models
from the UI.

Config toggle: set ``backend: "ollama"`` in config.yaml.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

OLLAMA_BASE = "http://localhost:11434"


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def is_available() -> bool:
    """Return True if Ollama is running and reachable."""
    try:
        with urllib.request.urlopen(f"{OLLAMA_BASE}/api/tags", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Model management
# ---------------------------------------------------------------------------

def list_models() -> List[str]:
    """Return list of locally available Ollama model names."""
    try:
        with urllib.request.urlopen(f"{OLLAMA_BASE}/api/tags", timeout=5) as resp:
            data = json.loads(resp.read())
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def pull_model(model_name: str) -> bool:
    """
    Pull (download) *model_name* via Ollama.

    Returns True if the pull completed without error.
    """
    try:
        payload = json.dumps({"name": model_name, "stream": False}).encode()
        req = urllib.request.Request(
            f"{OLLAMA_BASE}/api/pull",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read())
            return data.get("status") == "success"
    except Exception as exc:
        print(f"[ollama_backend] pull_model error: {exc}")
        return False


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------

def generate(
    model_name: str,
    prompt: str,
    system: str = "",
    options: Optional[Dict[str, Any]] = None,
    stream: bool = False,
) -> str:
    """
    Run inference via Ollama's /api/generate endpoint.

    Returns the generated text, or an error string.
    """
    payload: Dict[str, Any] = {
        "model":  model_name,
        "prompt": prompt,
        "stream": stream,
    }
    if system:
        payload["system"] = system
    if options:
        payload["options"] = options

    try:
        data_bytes = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{OLLAMA_BASE}/api/generate",
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result.get("response", "")
    except urllib.error.URLError as exc:
        return f"[ollama_backend] Connection error: {exc}"
    except Exception as exc:
        return f"[ollama_backend] Error: {exc}"


# ---------------------------------------------------------------------------
# Config helper
# ---------------------------------------------------------------------------

def is_enabled() -> bool:
    """Return True if config.yaml sets backend = 'ollama'."""
    try:
        import yaml
        from pathlib import Path
        cfg_path = Path(__file__).resolve().parents[1] / "config.yaml"
        with open(cfg_path) as f:
            cfg = yaml.safe_load(f) or {}
        return cfg.get("backend", "llamacpp").lower() == "ollama"
    except Exception:
        return False
