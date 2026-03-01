"""
modules/training_presets.py — Training configuration presets for Gizmo MY-AI.

Presets are stored as JSON files in ``user_data/training_presets/``.
Five built-in presets are generated automatically on first access if the
directory is empty or missing.

Usage::

    from modules.training_presets import list_presets, load_preset, save_preset

    names = list_presets()                  # ['Quick LoRA', 'Deep Memorization', ...]
    config = load_preset('Quick LoRA')      # dict of training parameters
    save_preset('My Preset', config)        # saves to user_data/training_presets/
    delete_preset('My Preset')
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

_PRESETS_DIR = Path("user_data/training_presets")

# ---------------------------------------------------------------------------
# Built-in presets
# ---------------------------------------------------------------------------

_BUILTIN_PRESETS: Dict[str, Dict[str, Any]] = {
    "Quick LoRA": {
        "lora_rank": 8,
        "lora_alpha": 16,
        "lora_dropout": 0.05,
        "epochs": 1,
        "learning_rate": "3e-4",
        "lr_scheduler_type": "cosine",
        "micro_batch_size": 4,
        "grad_accumulation": 1,
        "cutoff_len": 512,
        "training_projection": "q-v",
        "neft_noise_alpha": 0.0,
        "warmup_steps": 100,
        "_description": "Fast style-transfer LoRA. Low rank keeps the adapter small.",
    },
    "Deep Memorization": {
        "lora_rank": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
        "epochs": 2,
        "learning_rate": "1e-4",
        "lr_scheduler_type": "cosine",
        "micro_batch_size": 4,
        "grad_accumulation": 2,
        "cutoff_len": 512,
        "training_projection": "q-v",
        "sliding_window": True,
        "neft_noise_alpha": 0.0,
        "warmup_steps": 100,
        "_description": "Sliding-window deep memorization. Good for long-form text.",
    },
    "Code Fine-tune": {
        "lora_rank": 64,
        "lora_alpha": 128,
        "lora_dropout": 0.05,
        "epochs": 3,
        "learning_rate": "2e-4",
        "lr_scheduler_type": "cosine",
        "micro_batch_size": 4,
        "grad_accumulation": 4,
        "cutoff_len": 1024,
        "training_projection": "q-k-v-o",
        "neft_noise_alpha": 0.0,
        "warmup_steps": 200,
        "_description": "High-rank code fine-tuning targeting all projection layers.",
    },
    "Chat Persona": {
        "lora_rank": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
        "epochs": 2,
        "learning_rate": "3e-4",
        "lr_scheduler_type": "cosine",
        "micro_batch_size": 4,
        "grad_accumulation": 2,
        "cutoff_len": 512,
        "training_projection": "q-v",
        "neft_noise_alpha": 5.0,
        "warmup_steps": 100,
        "_description": "Persona training with NEFTune noise for better generalization.",
    },
    "RTX 4080 Max": {
        "lora_rank": 32,
        "lora_alpha": 64,
        "lora_dropout": 0.05,
        "epochs": 3,
        "learning_rate": "3e-4",
        "lr_scheduler_type": "cosine",
        "micro_batch_size": 8,
        "grad_accumulation": 2,
        "cutoff_len": 2048,
        "training_projection": "q-k-v-o",
        "neft_noise_alpha": 0.0,
        "warmup_steps": 100,
        "_description": "Maximises the RTX 4080's 16 GB VRAM. Batch 8 × accum 2 = effective 16.",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_dir() -> Path:
    _PRESETS_DIR.mkdir(parents=True, exist_ok=True)
    return _PRESETS_DIR


def _preset_path(name: str) -> Path:
    safe = name.replace("/", "_").replace("\\", "_")
    return _ensure_dir() / f"{safe}.json"


def _seed_builtins() -> None:
    """Write built-in presets to disk if they don't exist yet."""
    for name, config in _BUILTIN_PRESETS.items():
        path = _preset_path(name)
        if not path.exists():
            try:
                path.write_text(json.dumps(config, indent=2), encoding="utf-8")
            except Exception as exc:
                print(f"[training_presets] Could not write preset '{name}': {exc}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_presets() -> List[str]:
    """Return sorted list of all preset names (built-in + user-saved)."""
    _seed_builtins()
    try:
        names = [p.stem for p in sorted(_PRESETS_DIR.glob("*.json"))]
    except Exception:
        names = list(_BUILTIN_PRESETS.keys())
    return names


def load_preset(name: str) -> Optional[Dict[str, Any]]:
    """
    Load a preset by name.

    Returns the configuration dict, or ``None`` if the preset does not exist.
    Private keys (starting with ``_``) are stripped before returning.
    """
    _seed_builtins()
    path = _preset_path(name)
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return {k: v for k, v in raw.items() if not k.startswith("_")}
    except Exception as exc:
        print(f"[training_presets] Could not load preset '{name}': {exc}")
        return None


def save_preset(name: str, config: Dict[str, Any]) -> bool:
    """
    Save *config* as a preset named *name*.

    Returns ``True`` on success, ``False`` on failure.
    """
    if not name.strip():
        return False
    try:
        _preset_path(name).write_text(json.dumps(config, indent=2), encoding="utf-8")
        return True
    except Exception as exc:
        print(f"[training_presets] Could not save preset '{name}': {exc}")
        return False


def delete_preset(name: str) -> bool:
    """
    Delete a preset by name.

    Returns ``True`` on success.  Deleting a built-in preset only removes the
    file; it will be recreated on the next call to ``list_presets()``.
    """
    path = _preset_path(name)
    if not path.exists():
        return False
    try:
        path.unlink()
        return True
    except Exception as exc:
        print(f"[training_presets] Could not delete preset '{name}': {exc}")
        return False
