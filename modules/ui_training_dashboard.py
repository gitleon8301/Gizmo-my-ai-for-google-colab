"""
modules/ui_training_dashboard.py — Live training metrics dashboard.

Provides:
  - update_metrics()  called from the training loop to record loss/LR/GPU
  - build_charts()    returns Plotly figures for loss, LR, and GPU utilization
  - get_summary()     returns a plain-text summary string

Requires Plotly for charts (lazy-imported).
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# In-memory metrics store (reset on each training run)
# ---------------------------------------------------------------------------
_metrics: Dict[str, List] = {
    "step":      [],
    "loss":      [],
    "lr":        [],
    "tokens_ps": [],
    "gpu_util":  [],
    "best_loss": None,
    "best_step": None,
    "start_time": None,
    "total_steps": 0,
}

_paused = False


def reset_metrics(total_steps: int = 0) -> None:
    """Reset all training metrics (call at the start of a new run)."""
    global _metrics, _paused
    _metrics = {
        "step":       [],
        "loss":       [],
        "lr":         [],
        "tokens_ps":  [],
        "gpu_util":   [],
        "best_loss":  None,
        "best_step":  None,
        "start_time": time.time(),
        "total_steps": total_steps,
    }
    _paused = False


def update_metrics(
    step: int,
    loss: float,
    lr: float = 0.0,
    tokens_per_second: float = 0.0,
    gpu_util_pct: float = 0.0,
) -> None:
    """Append one step's metrics.  Called from the training loop."""
    if _paused:
        return
    _metrics["step"].append(step)
    _metrics["loss"].append(loss)
    _metrics["lr"].append(lr)
    _metrics["tokens_ps"].append(tokens_per_second)
    _metrics["gpu_util"].append(gpu_util_pct)

    if _metrics["best_loss"] is None or loss < _metrics["best_loss"]:
        _metrics["best_loss"] = loss
        _metrics["best_step"] = step


def pause_training() -> None:
    global _paused
    _paused = True


def resume_training() -> None:
    global _paused
    _paused = False


def is_paused() -> bool:
    return _paused


# ---------------------------------------------------------------------------
# Chart builders (lazy Plotly import)
# ---------------------------------------------------------------------------

def _make_plotly_figure(x, y, title: str, x_label: str, y_label: str) -> Optional[Any]:
    try:
        import plotly.graph_objects as go
        fig = go.Figure(go.Scatter(x=x, y=y, mode="lines", line={"color": "#6C63FF"}))
        fig.update_layout(
            title=title,
            xaxis_title=x_label,
            yaxis_title=y_label,
            template="plotly_dark",
            paper_bgcolor="#0d0f12",
            plot_bgcolor="#0d0f12",
            margin={"l": 50, "r": 20, "t": 40, "b": 40},
        )
        return fig
    except ImportError:
        print("[ui_training_dashboard] plotly not installed.\n  Run: pip install plotly")
        return None


def build_loss_chart() -> Optional[Any]:
    return _make_plotly_figure(
        _metrics["step"], _metrics["loss"],
        "Training Loss", "Step", "Loss"
    )


def build_lr_chart() -> Optional[Any]:
    return _make_plotly_figure(
        _metrics["step"], _metrics["lr"],
        "Learning Rate", "Step", "LR"
    )


def build_gpu_chart() -> Optional[Any]:
    return _make_plotly_figure(
        _metrics["step"], _metrics["gpu_util"],
        "GPU Utilization", "Step", "GPU %"
    )


# ---------------------------------------------------------------------------
# Summary string
# ---------------------------------------------------------------------------

def get_summary() -> str:
    steps = _metrics["step"]
    if not steps:
        return "No training data yet."

    current_step  = steps[-1]
    total_steps   = _metrics["total_steps"] or current_step
    elapsed       = time.time() - (_metrics["start_time"] or time.time())
    tokens_ps_avg = (sum(_metrics["tokens_ps"]) / len(_metrics["tokens_ps"])
                     if _metrics["tokens_ps"] else 0.0)
    eta_s         = ((total_steps - current_step) * elapsed / current_step
                     if current_step > 0 else 0)
    eta_str       = f"{eta_s/60:.1f} min" if eta_s > 0 else "—"
    best_loss     = _metrics["best_loss"]
    best_step     = _metrics["best_step"]
    current_loss  = _metrics["loss"][-1] if _metrics["loss"] else "—"

    paused_str    = "  ⏸ PAUSED" if _paused else ""
    return (
        f"Step {current_step}/{total_steps}{paused_str}\n"
        f"Loss: {current_loss:.4f}  |  Best: {best_loss:.4f} @ step {best_step}\n"
        f"Tokens/s: {tokens_ps_avg:.1f}  |  ETA: {eta_str}"
    )
