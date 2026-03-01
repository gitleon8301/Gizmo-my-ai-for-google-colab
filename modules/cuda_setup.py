"""
modules/cuda_setup.py — NVIDIA CUDA detection and environment setup.

All torch/nvidia calls are wrapped in try/except so this module
never crashes the server if CUDA is unavailable.
"""

from __future__ import annotations

import os
import subprocess


def _nvidia_smi_available() -> bool:
    """Return True if nvidia-smi can be called successfully."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0 and result.stdout.strip() != ""
    except Exception:
        return False


def _torch_cuda_available() -> bool:
    """Return True if torch reports CUDA is available."""
    try:
        import torch  # lazy import — never crash if torch missing
        return torch.cuda.is_available()
    except Exception:
        return False


def setup_cuda() -> bool:
    """
    Detect NVIDIA GPU, set CUDA environment variables, and print status.

    Returns True if CUDA is available, False otherwise.
    Never raises an exception.
    """
    try:
        cuda_ok = _torch_cuda_available() or _nvidia_smi_available()

        if cuda_ok:
            os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
            os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "max_split_size_mb:512")

            # Report GPU name if torch is available
            try:
                import torch
                gpu_name = torch.cuda.get_device_name(0)
                vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
                print(f"   🟢 GPU: {gpu_name}  ({vram_gb:.1f} GB VRAM)")
            except Exception:
                print("   🟢 CUDA GPU detected")
        else:
            print(
                "   ⚠️  No CUDA GPU detected — running on CPU.\n"
                "   To enable GPU support on Fedora:\n"
                "     See docs/CUDA_SETUP.md for full instructions.\n"
                "   Quick summary:\n"
                "     sudo dnf install akmod-nvidia xorg-x11-drv-nvidia-cuda\n"
                "     pip install torch --index-url https://download.pytorch.org/whl/cu121"
            )

        return cuda_ok

    except Exception as exc:
        print(f"   ⚠️  cuda_setup error (non-fatal): {exc}")
        return False
