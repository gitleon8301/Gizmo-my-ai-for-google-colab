#!/usr/bin/env bash
# ================================================================
# Gizmo MY-AI  •  Fedora Launch Script
# ================================================================
# Usage:
#   ./start_fedora.sh [--port PORT] [--cpu-only] [--dev]
#
# Flags:
#   --port N     Override server port (default: from config.yaml or 7860)
#   --cpu-only   Disable GPU (pure CPU inference)
#   --dev        Skip authentication (local development only)
# ================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ---------------------------------------------------------------------------
# Defaults (overridden by config.yaml values parsed below or by CLI flags)
# ---------------------------------------------------------------------------
PORT=7860
CPU_ONLY=0
DEV_MODE=0

# ---------------------------------------------------------------------------
# Parse CLI flags
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --port)   PORT="$2"; shift 2 ;;
        --cpu-only) CPU_ONLY=1; shift ;;
        --dev)    DEV_MODE=1; shift ;;
        *) echo "Unknown flag: $1" >&2; shift ;;
    esac
done

# ---------------------------------------------------------------------------
# Read storage paths from config.yaml (requires python3 + PyYAML)
# ---------------------------------------------------------------------------
if command -v python3 &>/dev/null && python3 -c "import yaml" &>/dev/null 2>&1; then
    MODELS_DIR=$(python3 -c "
import yaml, pathlib
cfg = yaml.safe_load(open('config.yaml'))
print(cfg.get('storage', {}).get('models_dir', '/mnt/gizmo-storage/models'))
" 2>/dev/null || echo "/mnt/gizmo-storage/models")

    CACHE_DIR=$(python3 -c "
import yaml
cfg = yaml.safe_load(open('config.yaml'))
print(cfg.get('storage', {}).get('cache_dir', '/mnt/gizmo-storage/cache'))
" 2>/dev/null || echo "/mnt/gizmo-storage/cache")

    LOGS_DIR=$(python3 -c "
import yaml
cfg = yaml.safe_load(open('config.yaml'))
print(cfg.get('storage', {}).get('logs_dir', '/mnt/gizmo-storage/logs'))
" 2>/dev/null || echo "/mnt/gizmo-storage/logs")

    CFG_PORT=$(python3 -c "
import yaml
cfg = yaml.safe_load(open('config.yaml'))
print(cfg.get('server', {}).get('port', 7860))
" 2>/dev/null || echo "7860")

    PUBLIC_URL=$(python3 -c "
import yaml
cfg = yaml.safe_load(open('config.yaml'))
print(cfg.get('server', {}).get('public_url', 'https://gizmohub.ai'))
" 2>/dev/null || echo "https://gizmohub.ai")

    # Only use config port if the user didn't pass --port
    [[ "$PORT" == "7860" ]] && PORT="$CFG_PORT"
else
    MODELS_DIR="/mnt/gizmo-storage/models"
    CACHE_DIR="/mnt/gizmo-storage/cache"
    LOGS_DIR="/mnt/gizmo-storage/logs"
    PUBLIC_URL="https://gizmohub.ai"
fi

# ---------------------------------------------------------------------------
# Export HuggingFace / PyTorch cache env vars
# ---------------------------------------------------------------------------
export TRANSFORMERS_CACHE="${CACHE_DIR}/transformers"
export HF_HOME="${CACHE_DIR}/hf"
export TORCH_HOME="${CACHE_DIR}/torch"
export HF_DATASETS_CACHE="${CACHE_DIR}/datasets"

# ---------------------------------------------------------------------------
# Source Google OAuth credentials (gitignored; safe to skip if missing)
# ---------------------------------------------------------------------------
OAUTH_ENV="user_data/google_oauth.env"
if [[ -f "$OAUTH_ENV" ]]; then
    # shellcheck disable=SC1090
    source "$OAUTH_ENV"
    echo "🔑  OAuth credentials loaded from $OAUTH_ENV"
fi

# ---------------------------------------------------------------------------
# Activate Python virtual environment (if present)
# ---------------------------------------------------------------------------
VENV_ACTIVATE="./venv/bin/activate"
if [[ -f "$VENV_ACTIVATE" ]]; then
    # shellcheck disable=SC1090
    source "$VENV_ACTIVATE"
    echo "🐍  Virtual environment activated"
fi

# ---------------------------------------------------------------------------
# Ensure required directories exist
# ---------------------------------------------------------------------------
mkdir -p "$MODELS_DIR" \
         "${CACHE_DIR}/transformers" \
         "${CACHE_DIR}/hf" \
         "${CACHE_DIR}/torch" \
         "${LOGS_DIR}" \
         "user_data/sessions"

# ---------------------------------------------------------------------------
# Build server.py argument list
# ---------------------------------------------------------------------------
SERVER_ARGS=(
    python3 server.py
    --listen
    --listen-host "127.0.0.1"
    --listen-port "$PORT"
    --model-dir "$MODELS_DIR"
)

[[ $CPU_ONLY -eq 1 ]] && SERVER_ARGS+=(--cpu)
[[ $DEV_MODE -eq 1 ]] && SERVER_ARGS+=(--dev)

# ---------------------------------------------------------------------------
# Print startup banner
# ---------------------------------------------------------------------------
echo "================================================================"
echo "   🤖  Gizmo MY-AI  •  Fedora Self-Hosted"
echo "================================================================"
echo "   Models  → $MODELS_DIR"
echo "   Cache   → $CACHE_DIR"
echo "   Logs    → $LOGS_DIR"
echo "   Port    → $PORT"
[[ $CPU_ONLY -eq 1 ]] && echo "   Mode    → CPU-only"
[[ $DEV_MODE -eq 1 ]] && echo "   Auth    → DISABLED (dev mode)"
echo "================================================================"

# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------
echo "✅  Gizmo is running → ${PUBLIC_URL}"
exec "${SERVER_ARGS[@]}"
