"""
modules/ui_dataset_browser.py — HuggingFace Dataset Hub browser for Gizmo MY-AI.

Allows users to search/browse HF datasets from the UI, preview samples,
and download with one click.

Optional dependency:
    pip install datasets huggingface_hub
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Lazy imports
# ---------------------------------------------------------------------------

def _require_hf_hub():
    try:
        import huggingface_hub  # noqa: F401
        return True
    except ImportError:
        print("[ui_dataset_browser] huggingface_hub not installed.\n  Run: pip install huggingface_hub")
        return False


def _require_datasets():
    try:
        import datasets  # noqa: F401
        return True
    except ImportError:
        print("[ui_dataset_browser] datasets not installed.\n  Run: pip install datasets")
        return False


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def search_datasets(
    query: str = "",
    task: str = "",
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Search the HuggingFace Hub for datasets matching *query*.

    Returns a list of dicts with keys: id, downloads, likes, tags, task_categories.
    """
    if not _require_hf_hub():
        return []

    try:
        from huggingface_hub import HfApi
        api = HfApi()
        kwargs: Dict[str, Any] = {"limit": limit, "sort": "downloads", "direction": -1}
        if query:
            kwargs["search"] = query
        if task:
            kwargs["task_categories"] = task

        datasets_list = list(api.list_datasets(**kwargs))
        results = []
        for d in datasets_list:
            results.append({
                "id":               d.id,
                "downloads":        getattr(d, "downloads", 0),
                "likes":            getattr(d, "likes", 0),
                "tags":             getattr(d, "tags", []),
                "task_categories":  getattr(d, "task_categories", []),
            })
        return results
    except Exception as exc:
        print(f"[ui_dataset_browser] search error: {exc}")
        return []


def preview_dataset(dataset_id: str, split: str = "train", n: int = 3) -> List[Dict]:
    """Return the first *n* rows of *dataset_id*."""
    if not _require_datasets():
        return []
    try:
        from datasets import load_dataset
        ds = load_dataset(dataset_id, split=split, streaming=True)
        return [row for _, row in zip(range(n), ds)]
    except Exception as exc:
        print(f"[ui_dataset_browser] preview error: {exc}")
        return []


def download_dataset(dataset_id: str, save_dir: Optional[str] = None) -> str:
    """
    Download *dataset_id* to *save_dir* (defaults to user_data/training_datasets/).

    Returns a status message.
    """
    if not _require_datasets():
        return "❌ datasets library not installed."

    from pathlib import Path
    if save_dir is None:
        base = Path(__file__).resolve().parents[1] / "user_data" / "training_datasets"
        base.mkdir(parents=True, exist_ok=True)
        save_dir = str(base / dataset_id.replace("/", "__"))

    try:
        from datasets import load_dataset
        ds = load_dataset(dataset_id)
        ds.save_to_disk(save_dir)
        return f"✅ Saved to {save_dir}"
    except Exception as exc:
        return f"❌ Download failed: {exc}"


# ---------------------------------------------------------------------------
# Featured datasets panel
# ---------------------------------------------------------------------------

FEATURED_DATASETS = [
    {"id": "tatsu-lab/alpaca",       "desc": "Instruction-following (Alpaca format)"},
    {"id": "Open-Orca/OpenOrca",     "desc": "Large instruction dataset"},
    {"id": "teknium/OpenHermes-2.5", "desc": "High-quality chat instructions"},
    {"id": "HuggingFaceH4/ultrachat_200k", "desc": "Multi-turn conversations"},
    {"id": "bigcode/the-stack",      "desc": "Source code (multi-language)"},
    {"id": "codeparrot/github-code", "desc": "GitHub code corpus"},
    {"id": "Anthropic/hh-rlhf",      "desc": "Human preference data for RLHF"},
]


def get_featured() -> List[Dict[str, str]]:
    return FEATURED_DATASETS
