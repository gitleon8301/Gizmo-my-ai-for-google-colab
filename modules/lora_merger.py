"""
modules/lora_merger.py — LoRA merge utilities for Gizmo MY-AI.

Supports:
  - Merging a single LoRA adapter into the base model
  - Stacking multiple LoRA adapters
  - Exporting merged model to GGUF format (via llama.cpp convert script)

Dependencies (lazy-imported):
    pip install peft transformers torch
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Single LoRA merge
# ---------------------------------------------------------------------------

def merge_lora(
    base_model: str,
    lora_path: str,
    output_dir: str,
    progress_callback=None,
) -> Dict[str, Any]:
    """
    Merge *lora_path* into *base_model* and save the merged weights to *output_dir*.

    Parameters
    ----------
    base_model        : HF model name or local path
    lora_path         : path to the LoRA adapter directory
    output_dir        : where to save the merged model
    progress_callback : optional callable(step: str) for status updates

    Returns dict with keys: status, output_dir, error.
    """
    for pkg, install in [
        ("peft",         "pip install peft"),
        ("transformers", "pip install transformers"),
        ("torch",        "pip install torch"),
    ]:
        try:
            __import__(pkg)
        except ImportError:
            return {"status": "error", "error": f"{pkg} not installed. Run: {install}"}

    try:
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer

        def _cb(msg):
            if progress_callback:
                progress_callback(msg)
            else:
                print(f"[lora_merger] {msg}")

        _cb("Loading base model…")
        tokenizer = AutoTokenizer.from_pretrained(base_model)
        model     = AutoModelForCausalLM.from_pretrained(base_model)

        _cb("Loading LoRA adapter…")
        model = PeftModel.from_pretrained(model, lora_path)

        _cb("Merging weights…")
        model = model.merge_and_unload()

        _cb(f"Saving merged model → {output_dir}")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        model.save_pretrained(output_dir)
        tokenizer.save_pretrained(output_dir)

        _cb("Done ✅")
        return {"status": "success", "output_dir": output_dir}

    except Exception as exc:
        return {"status": "error", "error": str(exc)}


# ---------------------------------------------------------------------------
# Stack multiple LoRAs
# ---------------------------------------------------------------------------

def stack_loras(
    base_model: str,
    lora_paths: List[str],
    output_dir: str,
    progress_callback=None,
) -> Dict[str, Any]:
    """
    Sequentially merge a list of LoRA adapters into *base_model*.
    """
    try:
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer

        def _cb(msg):
            if progress_callback:
                progress_callback(msg)

        _cb("Loading base model…")
        tokenizer = AutoTokenizer.from_pretrained(base_model)
        model     = AutoModelForCausalLM.from_pretrained(base_model)

        for i, lp in enumerate(lora_paths):
            _cb(f"Merging LoRA {i+1}/{len(lora_paths)}: {lp}")
            model = PeftModel.from_pretrained(model, lp)
            model = model.merge_and_unload()

        _cb(f"Saving → {output_dir}")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        model.save_pretrained(output_dir)
        tokenizer.save_pretrained(output_dir)
        return {"status": "success", "output_dir": output_dir}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


# ---------------------------------------------------------------------------
# Export to GGUF (requires llama.cpp convert script)
# ---------------------------------------------------------------------------

def export_gguf(
    model_dir: str,
    output_path: str,
    quantization: str = "q4_k_m",
    progress_callback=None,
) -> Dict[str, Any]:
    """
    Convert a HuggingFace model directory to GGUF using llama.cpp's
    ``convert_hf_to_gguf.py`` script (must be in PATH or current directory).

    Returns dict with keys: status, output_path, error.
    """
    import subprocess
    import shutil

    convert_script = shutil.which("convert_hf_to_gguf.py") or "convert_hf_to_gguf.py"

    cmd = [
        "python3", convert_script,
        model_dir,
        "--outfile", output_path,
        "--outtype", quantization,
    ]

    def _cb(msg):
        if progress_callback:
            progress_callback(msg)

    try:
        _cb(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            _cb(f"GGUF saved to {output_path} ✅")
            return {"status": "success", "output_path": output_path}
        else:
            return {"status": "error", "error": result.stderr or result.stdout}
    except FileNotFoundError:
        return {
            "status": "error",
            "error": "convert_hf_to_gguf.py not found. Clone llama.cpp and add it to PATH.",
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
