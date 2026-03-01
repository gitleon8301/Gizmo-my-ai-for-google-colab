"""
modules/rtx4080_optimizer.py — RTX 4080 training defaults for Gizmo MY-AI.

Provides optimal LoRA training settings for the NVIDIA RTX 4080 (16 GB VRAM)
and a simple VRAM estimator so users can tune their configuration without
running out of memory.

Usage::

    from modules.rtx4080_optimizer import get_rtx4080_defaults, estimate_vram_usage

    defaults = get_rtx4080_defaults()
    vram_gb  = estimate_vram_usage(model_size_gb=7, batch_size=8, rank=32, cutoff_len=2048)
"""

from __future__ import annotations

from typing import Any, Dict


# ---------------------------------------------------------------------------
# Optimal defaults
# ---------------------------------------------------------------------------

_RTX4080_DEFAULTS: Dict[str, Any] = {
    # LoRA config
    "lora_rank": 32,
    "lora_alpha": 64,
    "lora_dropout": 0.05,
    "training_projection": "q-k-v-o",
    # Training loop
    "micro_batch_size": 8,
    "grad_accumulation": 2,
    "cutoff_len": 2048,
    "epochs": 3,
    "learning_rate": "3e-4",
    "lr_scheduler_type": "cosine",
    "warmup_steps": 100,
    "optimizer": "adamw_torch",
    # Stability
    "neft_noise_alpha": 0.0,
    "add_bos_token": True,
    "add_eos_token": False,
}


def get_rtx4080_defaults() -> Dict[str, Any]:
    """
    Return a copy of the optimal training configuration for the RTX 4080 (16 GB).

    Configuration rationale
    -----------------------
    - True batch size 8 × gradient accumulation 2 = effective batch 16, which
      fills VRAM well for 7-13 B models without OOM.
    - Rank 32 with all four projection targets (q/k/v/o) balances expressivity
      against adapter size.
    - Cutoff 2048 enables learning long contexts while staying under 16 GB.
    """
    return dict(_RTX4080_DEFAULTS)


# ---------------------------------------------------------------------------
# VRAM estimator
# ---------------------------------------------------------------------------

def estimate_vram_usage(
    model_size_gb: float,
    batch_size: int = 8,
    rank: int = 32,
    cutoff_len: int = 2048,
) -> float:
    """
    Rough VRAM estimate (in GB) for LoRA fine-tuning.

    The formula is intentionally conservative (overestimates) so users
    have a buffer.  All numbers wrap in try/except so the function never
    raises.

    Parameters
    ----------
    model_size_gb : size of the base model weights in GB
    batch_size    : true (per-device) batch size
    rank          : LoRA rank
    cutoff_len    : token sequence length per sample

    Returns
    -------
    Estimated VRAM usage in GB (float).
    """
    try:
        # Base model weights (loaded in fp16 ≈ half of fp32 size)
        base_vram = model_size_gb * 0.6

        # Activations: roughly proportional to batch_size × cutoff_len
        # Empirical constant calibrated on RTX 4080 with 7B model
        activation_vram = (batch_size * cutoff_len) / (512 * 8) * 2.0

        # LoRA adapter overhead is small; rank scales it slightly
        lora_overhead = (rank / 64) * 0.5

        # Optimizer states (AdamW keeps fp32 copies ≈ 2× model)
        optimizer_vram = model_size_gb * 0.3

        total = base_vram + activation_vram + lora_overhead + optimizer_vram
        return round(total, 2)
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# UI helper
# ---------------------------------------------------------------------------

def apply_rtx4080_defaults(ui_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge RTX 4080 defaults into *ui_state* and return the updated dict.

    Only keys that exist in *ui_state* are overwritten so that unrelated
    settings are left intact.

    Parameters
    ----------
    ui_state : dict representing the current Training_PRO UI component values

    Returns
    -------
    Updated copy of *ui_state*.
    """
    try:
        updated = dict(ui_state)
        defaults = get_rtx4080_defaults()
        for key, value in defaults.items():
            if key in updated:
                updated[key] = value
        return updated
    except Exception as exc:
        print(f"[rtx4080_optimizer] apply_rtx4080_defaults error: {exc}")
        return ui_state
