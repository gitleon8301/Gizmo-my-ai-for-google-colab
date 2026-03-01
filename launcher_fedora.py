#!/usr/bin/env python3
# ================================================================
# Gizmo MY-AI  •  Fedora Self-Hosted Launcher  v1.0.0
# ================================================================
# Runs on a local Fedora Linux machine (not Google Colab).
# Reads all paths from config.yaml so nothing is hard-coded.
# The original launcher.py (Colab) is untouched and still works.
# ================================================================

from __future__ import annotations

import os
import sys
import subprocess
import shutil
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Guard: never crash if google.colab is absent (it won't be on Fedora)
# ---------------------------------------------------------------------------
try:
    from google.colab import drive as _colab_drive  # noqa: F401
    IN_COLAB = True
except Exception:
    IN_COLAB = False

# ---------------------------------------------------------------------------
# Load config.yaml from the repo root
# ---------------------------------------------------------------------------
try:
    import yaml
    _CFG_PATH = Path(__file__).resolve().parent / "config.yaml"
    with open(_CFG_PATH) as _f:
        _CFG = yaml.safe_load(_f)
except Exception as _e:
    print(f"[launcher_fedora] WARNING: could not read config.yaml ({_e}). Using defaults.")
    _CFG = {}

def _cfg(keys: str, default):
    """Safely walk a dot-separated key path in _CFG."""
    node = _CFG
    for k in keys.split("."):
        if not isinstance(node, dict):
            return default
        node = node.get(k, default)
    return node if node is not None else default

# ---------------------------------------------------------------------------
# Path configuration  (from config.yaml with fallbacks)
# ---------------------------------------------------------------------------
BASE_DIR    = Path(_cfg("storage.base_dir",   "/mnt/gizmo-storage"))
MODELS_DIR  = Path(_cfg("storage.models_dir", str(BASE_DIR / "models")))
CACHE_DIR   = Path(_cfg("storage.cache_dir",  str(BASE_DIR / "cache")))
LOGS_DIR    = Path(_cfg("storage.logs_dir",   str(BASE_DIR / "logs")))
USER_DATA   = Path(__file__).resolve().parent / "user_data"

SERVER_PORT = int(_cfg("server.port",       7860))
SERVER_HOST = str(_cfg("server.host",       "127.0.0.1"))
PUBLIC_URL  = str(_cfg("server.public_url", "https://gizmohub.ai"))
BACKEND     = str(_cfg("backend",           "llamacpp"))

REQUIRED_DIRS = [
    MODELS_DIR,
    CACHE_DIR / "transformers",
    CACHE_DIR / "hf",
    CACHE_DIR / "torch",
    LOGS_DIR,
    USER_DATA,
    USER_DATA / "sessions",
]

# ---------------------------------------------------------------------------
# Expanded GGUF model menu  (13 models, TinyLlama → LLaMA-3.1 70B)
# ---------------------------------------------------------------------------
MODEL_MENU = [
    ("1  TinyLlama-1.1B        Q4_K_M  [~0.7 GB]  ← fastest, good for testing",
     "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
     "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf", 0.7),

    ("2  Phi-3-mini-4k          Q4_K_M  [~2.2 GB]  ← great quality/speed",
     "bartowski/Phi-3-mini-4k-instruct-GGUF",
     "Phi-3-mini-4k-instruct-Q4_K_M.gguf", 2.2),

    ("3  Mistral-7B-v0.3        Q4_K_M  [~4.4 GB]  ← best general 7B",
     "bartowski/Mistral-7B-v0.3-GGUF",
     "Mistral-7B-v0.3-Q4_K_M.gguf", 4.4),

    ("4  Qwen2.5-Coder-7B      Q4_K_M  [~4.7 GB]  ← best coding 7B",
     "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
     "qwen2.5-coder-7b-instruct-q4_k_m.gguf", 4.7),

    ("5  LLaMA-3-8B-Instruct   Q4_K_M  [~5.0 GB]  ← Meta LLaMA 3",
     "bartowski/Meta-Llama-3-8B-Instruct-GGUF",
     "Meta-Llama-3-8B-Instruct-Q4_K_M.gguf", 5.0),

    ("6  Qwen2.5-14B            Q4_K_M  [~8.9 GB]  ← great 14B",
     "Qwen/Qwen2.5-14B-Instruct-GGUF",
     "qwen2.5-14b-instruct-q4_k_m.gguf", 8.9),

    ("7  Mixtral-8x7B            Q4_K_M  [~26 GB]  ← MoE powerhouse (needs lots of RAM)",
     "TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF",
     "mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf", 26.0),

    ("8  LLaMA-3-70B-Instruct  Q4_K_M  [~42 GB]  ← large (multi-GPU / offload)",
     "bartowski/Meta-Llama-3-70B-Instruct-GGUF",
     "Meta-Llama-3-70B-Instruct-Q4_K_M.gguf", 42.0),

    ("9  DeepSeek-Coder-33B    Q4_K_M  [~19 GB]  ← best 33B coding",
     "TheBloke/deepseek-coder-33B-instruct-GGUF",
     "deepseek-coder-33b-instruct.Q4_K_M.gguf", 19.0),

    ("10 Codestral-22B          Q4_K_M  [~13 GB]  ← Mistral coding flagship",
     "bartowski/Codestral-22B-v0.1-GGUF",
     "Codestral-22B-v0.1-Q4_K_M.gguf", 13.0),

    ("11 Qwen2.5-Coder-32B     Q4_K_M  [~19 GB]  ← best open coding model",
     "Qwen/Qwen2.5-Coder-32B-Instruct-GGUF",
     "qwen2.5-coder-32b-instruct-q4_k_m.gguf", 19.0),

    ("12 LLaMA-3.1-70B         Q4_K_M  [~42 GB]  ← LLaMA 3.1 flagship",
     "bartowski/Meta-Llama-3.1-70B-Instruct-GGUF",
     "Meta-Llama-3.1-70B-Instruct-Q4_K_M.gguf", 42.0),

    ("13 Custom  — enter your own HF repo + filename", "", "", 0),
]

# ---------------------------------------------------------------------------
# HuggingFace environment variables → point to local storage
# ---------------------------------------------------------------------------
def _set_hf_env() -> None:
    os.environ.setdefault("TRANSFORMERS_CACHE", str(CACHE_DIR / "transformers"))
    os.environ.setdefault("HF_HOME",            str(CACHE_DIR / "hf"))
    os.environ.setdefault("TORCH_HOME",          str(CACHE_DIR / "torch"))
    os.environ.setdefault("HF_DATASETS_CACHE",   str(CACHE_DIR / "datasets"))

# ---------------------------------------------------------------------------
# Directory bootstrap
# ---------------------------------------------------------------------------
def _ensure_dirs() -> None:
    for d in REQUIRED_DIRS:
        Path(d).mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Startup banner
# ---------------------------------------------------------------------------
def _print_banner() -> None:
    print("=" * 65)
    print("   🤖  Gizmo MY-AI  •  Fedora Self-Hosted Launcher")
    print("=" * 65)
    print(f"   Models  → {MODELS_DIR}")
    print(f"   Cache   → {CACHE_DIR}")
    print(f"   Logs    → {LOGS_DIR}")
    print(f"   Port    → {SERVER_PORT}")
    print(f"   URL     → {PUBLIC_URL}")
    print(f"   Backend → {BACKEND}")
    print("=" * 65)

# ---------------------------------------------------------------------------
# CUDA setup (delegated to modules/cuda_setup.py when available)
# ---------------------------------------------------------------------------
def _setup_cuda() -> None:
    try:
        from modules.cuda_setup import setup_cuda
        setup_cuda()
    except ImportError:
        pass  # cuda_setup.py not yet present — silently skip

# ---------------------------------------------------------------------------
# GPU layer calculation helper
# ---------------------------------------------------------------------------
def _auto_gpu_layers(model_size_gb: float) -> int:
    try:
        from modules.gpu_layer_calc import calc_gpu_layers
        layers = calc_gpu_layers(model_size_gb)
        print(f"   ⚡ Auto GPU layers: {layers}")
        return layers
    except Exception:
        return -1  # default: all layers on GPU

# ---------------------------------------------------------------------------
# Model download with skip-if-exists logic + tqdm progress
# ---------------------------------------------------------------------------
def _download_model(repo_id: str, filename: str) -> Path:
    dest = MODELS_DIR / filename
    if dest.exists():
        print(f"   💾 Model already downloaded: {dest}")
        return dest

    print(f"\n   ⬇  Downloading {filename} from {repo_id} …")
    try:
        from huggingface_hub import hf_hub_download
        try:
            from tqdm.auto import tqdm as _tqdm  # noqa: F401 — ensure tqdm is used by HF
        except ImportError:
            pass
        path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=str(MODELS_DIR),
            local_dir_use_symlinks=False,
        )
        print(f"   ✅ Saved to {path}")
        return Path(path)
    except ImportError:
        print("   ❌ huggingface_hub not installed. Run: pip install huggingface_hub tqdm")
        sys.exit(1)
    except Exception as e:
        print(f"   ❌ Download failed: {e}")
        sys.exit(1)

# ---------------------------------------------------------------------------
# Interactive model selector
# ---------------------------------------------------------------------------
def _select_model() -> tuple[str, str, float]:
    print("\n   📦  Available models:")
    for entry in MODEL_MENU:
        print(f"      {entry[0]}")

    while True:
        choice = input("\n   Enter number (or 0 to skip): ").strip()
        if choice == "0":
            return "", "", 0.0
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(MODEL_MENU) - 1:
                _, repo, fname, size_gb = MODEL_MENU[idx]
                return repo, fname, size_gb
            elif idx == len(MODEL_MENU) - 1:
                # Custom model
                repo  = input("   HF repo ID (e.g. TheBloke/Mistral-7B-GGUF): ").strip()
                fname = input("   Filename (e.g. mistral-7b.Q4_K_M.gguf): ").strip()
                return repo, fname, 0.0
            else:
                print("   Invalid choice, try again.")
        except ValueError:
            print("   Please enter a number.")

# ---------------------------------------------------------------------------
# Build server.py argument list
# ---------------------------------------------------------------------------
def _build_server_args(model_path: str, gpu_layers: int, extra: list[str]) -> list[str]:
    args = [
        sys.executable, "server.py",
        "--listen",
        "--listen-host", SERVER_HOST,
        "--listen-port", str(SERVER_PORT),
        "--model-dir", str(MODELS_DIR),
    ]
    if model_path:
        args += ["--model", model_path]
    if BACKEND == "llamacpp":
        args += ["--loader", "llama.cpp"]
    if gpu_layers >= 0:
        args += ["--gpu-layers", str(gpu_layers)]
    args += extra
    return args

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main() -> None:
    _print_banner()
    _ensure_dirs()
    _set_hf_env()
    _setup_cuda()

    # Parse simple CLI flags
    cpu_only = "--cpu-only" in sys.argv
    dev_mode = "--dev" in sys.argv
    skip_model_select = "--no-model-select" in sys.argv

    extra_args: list[str] = []
    if cpu_only:
        print("   ⚠️  CPU-only mode — GPU disabled")
        extra_args.append("--cpu")
    if dev_mode:
        print("   🔧  Dev mode — authentication disabled")
        extra_args.append("--dev")

    # Model selection
    model_path = ""
    gpu_layers = 0

    if not skip_model_select:
        repo, fname, size_gb = _select_model()
        if repo and fname:
            dest = _download_model(repo, fname)
            model_path = str(dest)
            if not cpu_only:
                gpu_layers = _auto_gpu_layers(size_gb)

    # Launch server
    cmd = _build_server_args(model_path, gpu_layers, extra_args)
    print(f"\n   🚀  Starting server on {PUBLIC_URL} …\n")
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n   👋  Gizmo stopped.")
    except subprocess.CalledProcessError as e:
        print(f"\n   ❌  Server exited with code {e.returncode}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()
