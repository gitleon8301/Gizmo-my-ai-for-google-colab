#!/usr/bin/env bash
# ================================================================
# Gizmo MY-AI  •  Fedora Launch Script
# ================================================================
# Usage:
#   ./start_fedora.sh [--token GITHUB_PAT] [--port PORT] [--cpu-only]
#
# Flags:
#   --token PAT  GitHub personal access token — pulls latest code
#                from GitHub, backs up user data first, then restores
#   --port N     Override server port (default: 7860)
#   --cpu-only   Disable GPU (pure CPU inference)
# ================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
PORT=7860
CPU_ONLY=0
TOKEN=""
REPO_URL="https://github.com/leonlazdev-wq/Gizmo_MY_AI.git"

# ---------------------------------------------------------------------------
# Parse CLI flags
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --token)    TOKEN="$2"; shift 2 ;;
        --port)     PORT="$2"; shift 2 ;;
        --cpu-only) CPU_ONLY=1; shift ;;
        *) echo "Unknown flag: $1" >&2; shift ;;
    esac
done

# ---------------------------------------------------------------------------
# Optional: pull latest code from GitHub (preserving user data)
# ---------------------------------------------------------------------------
if [[ -n "$TOKEN" ]]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_DIR="/tmp/gizmo_backup_${TIMESTAMP}"
    FRESH_CLONE="/tmp/gizmo_fresh_${TIMESTAMP}"

    echo "🔄  Backing up user data to ${BACKUP_DIR} …"
    mkdir -p "$BACKUP_DIR"
    [[ -d "./user_data"      ]] && cp -a "./user_data"      "$BACKUP_DIR/"
    [[ -d "./storage/models" ]] && cp -a "./storage/models" "$BACKUP_DIR/storage_models"
    [[ -d "./storage/cache"  ]] && cp -a "./storage/cache"  "$BACKUP_DIR/storage_cache"
    [[ -d "./storage/logs"   ]] && cp -a "./storage/logs"   "$BACKUP_DIR/storage_logs"

    echo "📥  Cloning latest repo …"
    git -c "credential.helper=" \
        -c "credential.helper=!printf 'username=x-access-token\npassword=${TOKEN}\n'" \
        clone "$REPO_URL" "$FRESH_CLONE"

    echo "🗑️   Removing old project files (keeping user_data/ and storage/) …"
    find "$SCRIPT_DIR" -mindepth 1 -maxdepth 1 \
        ! -name 'user_data' \
        ! -name 'storage' \
        ! -name 'venv' \
        ! -name '.git' \
        -exec rm -rf {} +

    echo "📦  Installing fresh code …"
    cp -a "$FRESH_CLONE"/. "$SCRIPT_DIR/"

    echo "♻️   Restoring user data …"
    [[ -d "$BACKUP_DIR/user_data"      ]] && cp -a "$BACKUP_DIR/user_data"      "$SCRIPT_DIR/"
    [[ -d "$BACKUP_DIR/storage_models" ]] && { mkdir -p "$SCRIPT_DIR/storage"; cp -a "$BACKUP_DIR/storage_models" "$SCRIPT_DIR/storage/models"; }
    [[ -d "$BACKUP_DIR/storage_cache"  ]] && { mkdir -p "$SCRIPT_DIR/storage"; cp -a "$BACKUP_DIR/storage_cache"  "$SCRIPT_DIR/storage/cache";  }
    [[ -d "$BACKUP_DIR/storage_logs"   ]] && { mkdir -p "$SCRIPT_DIR/storage"; cp -a "$BACKUP_DIR/storage_logs"   "$SCRIPT_DIR/storage/logs";   }

    echo "🧹  Cleaning up temp files …"
    rm -rf "$BACKUP_DIR" "$FRESH_CLONE"
    echo "✅  Repo updated."
fi

# ---------------------------------------------------------------------------
# Create Python virtual environment if needed
# ---------------------------------------------------------------------------
if [[ ! -f "./venv/bin/activate" ]]; then
    echo "🐍  Creating Python virtual environment …"
    python3 -m venv venv
fi

# ---------------------------------------------------------------------------
# Activate venv
# ---------------------------------------------------------------------------
# shellcheck disable=SC1091
source ./venv/bin/activate
echo "🐍  Virtual environment activated"

# ---------------------------------------------------------------------------
# Install / upgrade pip dependencies
# ---------------------------------------------------------------------------
echo "📦  Installing pip dependencies …"
pip install --upgrade pip --quiet
pip install -r requirements/full/requirements.txt --quiet
echo "✅  Dependencies installed."

# ---------------------------------------------------------------------------
# Storage paths (local, relative to project root)
# ---------------------------------------------------------------------------
MODELS_DIR="./storage/models"
CACHE_DIR="./storage/cache"
LOGS_DIR="./storage/logs"

# ---------------------------------------------------------------------------
# Export HuggingFace / PyTorch cache env vars
# ---------------------------------------------------------------------------
export TRANSFORMERS_CACHE="${CACHE_DIR}/transformers"
export HF_HOME="${CACHE_DIR}/hf"
export TORCH_HOME="${CACHE_DIR}/torch"
export HF_DATASETS_CACHE="${CACHE_DIR}/datasets"

# ---------------------------------------------------------------------------
# Ensure required directories exist
# ---------------------------------------------------------------------------
mkdir -p "$MODELS_DIR" \
         "${CACHE_DIR}/transformers" \
         "${CACHE_DIR}/hf" \
         "${CACHE_DIR}/torch" \
         "$LOGS_DIR" \
         "user_data/sessions" \
         "user_data/code_tutor_sessions"

# ---------------------------------------------------------------------------
# Build server.py argument list
# ---------------------------------------------------------------------------
PUBLIC_URL="http://localhost:${PORT}"

SERVER_ARGS=(
    python3 server.py
    --listen
    --listen-host "127.0.0.1"
    --listen-port "$PORT"
    --model-dir "$MODELS_DIR"
    --dev
)

[[ $CPU_ONLY -eq 1 ]] && SERVER_ARGS+=(--cpu)

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
echo "   Auth    → DISABLED (local dev mode)"
echo "================================================================"

# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------
echo "✅  Gizmo is running → ${PUBLIC_URL}"
exec "${SERVER_ARGS[@]}"

