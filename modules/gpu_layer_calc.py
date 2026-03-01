"""
modules/gpu_layer_calc.py — Auto GPU layer calculator for llama.cpp.

Uses VRAM introspection to compute the maximum safe n-gpu-layers value.
All torch calls wrapped in try/except — never crashes on CPU-only systems.
"""

from __future__ import annotations

import os
from pathlib import Path


# Bytes per GGUF Q4_K_M layer (rough heuristic — overridden per model below).
# A more accurate estimate is (model_size_bytes / num_layers).
_BYTES_PER_LAYER_FALLBACK = 200 * 1024 * 1024  # 200 MB

# Approximate layer counts for common parameter sizes
_LAYER_COUNT_MAP = {
    1:  22,   # ~1B
    3:  26,   # ~3B
    7:  32,   # ~7B
    8:  32,   # ~8B
    13: 40,   # ~13B
    14: 40,   # ~14B
    22: 48,   # ~22B
    33: 62,   # ~33B
    70: 80,   # ~70B
}


def _get_free_vram_bytes() -> int:
    """Return free VRAM in bytes, or 0 if unavailable."""
    try:
        import torch
        if not torch.cuda.is_available():
            return 0
        free, _ = torch.cuda.mem_get_info(0)
        return free
    except Exception:
        return 0


def _get_total_vram_bytes() -> int:
    """Return total VRAM in bytes, or 0 if unavailable."""
    try:
        import torch
        if not torch.cuda.is_available():
            return 0
        props = torch.cuda.get_device_properties(0)
        return props.total_memory
    except Exception:
        return 0


def _infer_layer_count(model_size_gb: float) -> int:
    """Best-guess layer count from model size in GB."""
    params_b = round(model_size_gb / 0.55)  # Q4_K_M ≈ 0.55 GB/B params
    best = 32  # default
    for p, layers in sorted(_LAYER_COUNT_MAP.items()):
        if params_b >= p:
            best = layers
    return best


def calc_gpu_layers(model_size_gb: float, safety_buffer_pct: float | None = None) -> int:
    """
    Calculate the maximum safe n-gpu-layers for a given model.

    Parameters
    ----------
    model_size_gb : float
        Approximate model file size in GB (used to estimate bytes-per-layer).
    safety_buffer_pct : float | None
        Keep this % of VRAM free as a safety buffer.
        Reads ``gpu.vram_safety_buffer_percent`` from config.yaml when None.

    Returns
    -------
    int
        Recommended n-gpu-layers value.  Returns -1 (all layers) when
        VRAM info is unavailable.
    """
    if safety_buffer_pct is None:
        try:
            import yaml
            cfg_path = Path(__file__).resolve().parents[1] / "config.yaml"
            with open(cfg_path) as f:
                cfg = yaml.safe_load(f)
            safety_buffer_pct = float(
                cfg.get("gpu", {}).get("vram_safety_buffer_percent", 10)
            )
        except Exception:
            safety_buffer_pct = 10.0

    total_vram = _get_total_vram_bytes()
    if total_vram == 0:
        return -1  # no VRAM info — let llama.cpp decide

    usable_vram = total_vram * (1.0 - safety_buffer_pct / 100.0)

    model_size_bytes = model_size_gb * (1024 ** 3)
    num_layers = _infer_layer_count(model_size_gb)
    bytes_per_layer = model_size_bytes / max(num_layers, 1)

    if bytes_per_layer <= 0:
        return -1

    max_layers = int(usable_vram / bytes_per_layer)
    max_layers = max(0, min(max_layers, num_layers))
    return max_layers
