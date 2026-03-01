"""
modules/training_queue.py — Training job queue for Gizmo MY-AI.

Supports:
  - Queuing multiple training jobs back-to-back
  - Drag-reorder (via index swapping)
  - Estimated total time
  - Per-job status: queued / running / done / error
"""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any, Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# Job data class
# ---------------------------------------------------------------------------

class TrainingJob:
    def __init__(
        self,
        name: str,
        fn: Callable,
        kwargs: Dict[str, Any],
        estimated_minutes: float = 30.0,
    ) -> None:
        self.id               = str(uuid.uuid4())
        self.name             = name
        self.fn               = fn
        self.kwargs           = kwargs
        self.estimated_minutes = estimated_minutes
        self.status           = "queued"   # queued | running | done | error
        self.result: Any      = None
        self.error: str       = ""
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None


# ---------------------------------------------------------------------------
# Queue state
# ---------------------------------------------------------------------------

_lock   = threading.Lock()
_jobs:  List[TrainingJob] = []
_running = False
_worker: Optional[threading.Thread] = None


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------

def _run_worker() -> None:
    global _running
    while True:
        with _lock:
            pending = [j for j in _jobs if j.status == "queued"]
            if not pending:
                _running = False
                return
            job = pending[0]
            job.status     = "running"
            job.started_at = time.time()

        try:
            result          = job.fn(**job.kwargs)
            job.result      = result
            job.status      = "done"
        except Exception as exc:
            job.error  = str(exc)
            job.status = "error"
        finally:
            job.finished_at = time.time()


def _ensure_worker() -> None:
    global _running, _worker
    if not _running:
        _running = True
        _worker  = threading.Thread(target=_run_worker, daemon=True, name="training-queue")
        _worker.start()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def add_job(
    name: str,
    fn: Callable,
    kwargs: Dict[str, Any],
    estimated_minutes: float = 30.0,
) -> TrainingJob:
    """Add a training job to the queue and start the worker if idle."""
    job = TrainingJob(name, fn, kwargs, estimated_minutes)
    with _lock:
        _jobs.append(job)
        _ensure_worker()
    return job


def get_jobs() -> List[TrainingJob]:
    """Return a snapshot of all jobs (any status)."""
    with _lock:
        return list(_jobs)


def move_job(job_id: str, direction: int) -> None:
    """
    Swap job *job_id* up (-1) or down (+1) in the pending queue.
    Only moves queued jobs.
    """
    with _lock:
        pending = [j for j in _jobs if j.status == "queued"]
        ids     = [j.id for j in pending]
        if job_id not in ids:
            return
        idx = ids.index(job_id)
        new_idx = idx + direction
        if 0 <= new_idx < len(pending):
            pending[idx], pending[new_idx] = pending[new_idx], pending[idx]
            # Re-insert into _jobs preserving non-queued positions
            q_iter = iter(pending)
            for i, j in enumerate(_jobs):
                if j.status == "queued":
                    _jobs[i] = next(q_iter)


def cancel_job(job_id: str) -> bool:
    """Remove a queued job.  Running jobs cannot be cancelled here."""
    with _lock:
        for j in _jobs:
            if j.id == job_id and j.status == "queued":
                j.status = "error"
                j.error  = "Cancelled by user."
                return True
    return False


def estimated_total_minutes() -> float:
    """Return estimated minutes until all queued jobs finish."""
    with _lock:
        return sum(j.estimated_minutes for j in _jobs if j.status in ("queued", "running"))


def clear_finished() -> None:
    """Remove all completed / errored jobs from the list."""
    with _lock:
        _jobs[:] = [j for j in _jobs if j.status not in ("done", "error")]
