"""
modules/ui_resource_monitor.py — Real-time resource status bar.

Displays VRAM, CPU, RAM, GPU temp, active model, and online user count.
Updates every 3 seconds via gr.Timer.
Color codes: 🟢 <70% | 🟡 70-90% | 🔴 >90%

All psutil / torch.cuda calls are wrapped in try/except.
"""

from __future__ import annotations

from typing import Optional

# ---------------------------------------------------------------------------
# Metric helpers — all safe (never raise)
# ---------------------------------------------------------------------------

def _dot(pct: float) -> str:
    if pct >= 90:
        return "🔴"
    if pct >= 70:
        return "🟡"
    return "🟢"


def _vram_info() -> tuple[float, float]:
    """Return (used_gb, total_gb).  (0, 0) on failure."""
    try:
        import torch
        if not torch.cuda.is_available():
            return 0.0, 0.0
        props = torch.cuda.get_device_properties(0)
        total = props.total_memory
        reserved = torch.cuda.memory_reserved(0)
        return reserved / (1024 ** 3), total / (1024 ** 3)
    except Exception:
        return 0.0, 0.0


def _gpu_temp() -> Optional[float]:
    """Return GPU temperature in °C, or None."""
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3,
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
    except Exception:
        pass
    return None


def _cpu_pct() -> float:
    """Return CPU usage percent (0–100)."""
    try:
        import psutil
        return psutil.cpu_percent(interval=None)
    except Exception:
        return 0.0


def _ram_info() -> tuple[float, float]:
    """Return (used_gb, total_gb)."""
    try:
        import psutil
        vm = psutil.virtual_memory()
        return vm.used / (1024 ** 3), vm.total / (1024 ** 3)
    except Exception:
        return 0.0, 0.0


def _active_model() -> str:
    """Return the currently loaded model name, or 'none'."""
    try:
        from modules.shared import model_name
        return model_name or "none"
    except Exception:
        return "none"


def _online_users() -> int:
    """Return number of active users in the last 5 minutes."""
    try:
        from modules.user_sessions import get_active_users
        return len(get_active_users(max_idle_seconds=300))
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Main status string builder
# ---------------------------------------------------------------------------

def build_status_html() -> str:
    """Build the status bar HTML string.  Called by gr.Timer."""
    vram_used, vram_total = _vram_info()
    vram_pct = (vram_used / vram_total * 100) if vram_total > 0 else 0.0

    cpu = _cpu_pct()
    ram_used, ram_total = _ram_info()
    ram_pct = (ram_used / ram_total * 100) if ram_total > 0 else 0.0

    temp = _gpu_temp()
    model = _active_model()
    users = _online_users()

    temp_str = f"  🌡 {temp:.0f}°C" if temp is not None else ""

    parts = [
        f"{_dot(vram_pct)} VRAM {vram_used:.1f}/{vram_total:.1f} GB ({vram_pct:.0f}%)",
        f"{_dot(cpu)} CPU {cpu:.0f}%",
        f"{_dot(ram_pct)} RAM {ram_used:.1f}/{ram_total:.1f} GB",
        f"{temp_str}",
        f"🧠 {model}",
        f"👥 {users} online",
    ]

    items_html = "".join(
        f'<span style="margin-right:1.2rem">{p.strip()}</span>'
        for p in parts
        if p.strip()
    )

    return (
        '<div id="gizmo-status-bar" style="'
        "background:#111318; color:#ccc; font-size:.82rem; padding:6px 16px;"
        "border-top:1px solid #2a2d35; display:flex; align-items:center;"
        "flex-wrap:wrap; gap:.25rem;"
        f'">{items_html}</div>'
    )


# ---------------------------------------------------------------------------
# Gradio component builder
# ---------------------------------------------------------------------------

def create_status_bar():
    """
    Return a (gr.HTML, gr.Timer) pair ready to be added to a Gradio Blocks layout.

    Usage::

        status_html, status_timer = create_status_bar()
        status_timer.tick(fn=build_status_html, outputs=status_html)
    """
    try:
        import gradio as gr
        html_component = gr.HTML(value=build_status_html(), elem_id="gizmo-status-bar")
        timer = gr.Timer(value=3)
        return html_component, timer
    except Exception as exc:
        print(f"[ui_resource_monitor] Could not create status bar: {exc}")
        return None, None
