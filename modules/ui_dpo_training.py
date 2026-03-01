"""
modules/ui_dpo_training.py — Direct Preference Optimization (DPO) training tab.

Uses the `trl` library (lazy import).  Shows example datasets and a simple
configuration UI.

Install::
    pip install trl datasets
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Example DPO datasets
# ---------------------------------------------------------------------------

DPO_EXAMPLE_DATASETS = [
    {
        "id":   "Anthropic/hh-rlhf",
        "desc": "Human-feedback preference pairs (chosen/rejected)",
        "cols": ["chosen", "rejected"],
    },
    {
        "id":   "HuggingFaceH4/ultrafeedback_binarized",
        "desc": "Ultra-feedback binary preference dataset",
        "cols": ["chosen", "rejected", "prompt"],
    },
    {
        "id":   "Intel/orca_dpo_pairs",
        "desc": "DPO pairs derived from Orca instructions",
        "cols": ["system", "question", "chosen", "rejected"],
    },
]


def get_example_datasets() -> List[Dict[str, Any]]:
    return DPO_EXAMPLE_DATASETS


# ---------------------------------------------------------------------------
# DPO training (requires trl)
# ---------------------------------------------------------------------------

def train_dpo(
    model_name: str,
    dataset_id: str,
    output_dir: Optional[str] = None,
    beta: float = 0.1,
    learning_rate: float = 5e-7,
    num_train_epochs: int = 1,
    per_device_batch_size: int = 2,
    max_length: int = 512,
    progress_callback=None,
) -> Dict[str, Any]:
    """
    Run DPO training using trl.DPOTrainer.

    Parameters
    ----------
    model_name          : HF model name or local path
    dataset_id          : HF dataset ID (must have 'chosen' and 'rejected' columns)
    output_dir          : where to save the fine-tuned model
    beta                : DPO temperature (default 0.1)
    learning_rate       : AdamW learning rate
    num_train_epochs    : training epochs
    per_device_batch_size : batch size per GPU
    max_length          : maximum sequence length
    progress_callback   : optional callable(step, loss) for live updates

    Returns a dict with keys: status, output_dir, error.
    """
    # Lazy imports
    for pkg, install_cmd in [
        ("trl",      "pip install trl"),
        ("datasets", "pip install datasets"),
        ("transformers", "pip install transformers"),
        ("peft",     "pip install peft"),
    ]:
        try:
            __import__(pkg)
        except ImportError:
            return {"status": "error", "error": f"{pkg} not installed. Run: {install_cmd}"}

    try:
        from datasets import load_dataset
        from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
        from trl import DPOTrainer

        if output_dir is None:
            base = Path(__file__).resolve().parents[1] / "user_data" / "training_results"
            output_dir = str(base / f"dpo_{Path(model_name).name}")
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model     = AutoModelForCausalLM.from_pretrained(model_name)

        dataset = load_dataset(dataset_id)

        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_train_epochs,
            per_device_train_batch_size=per_device_batch_size,
            learning_rate=learning_rate,
            logging_steps=10,
            save_strategy="epoch",
            remove_unused_columns=False,
        )

        trainer = DPOTrainer(
            model=model,
            args=training_args,
            beta=beta,
            train_dataset=dataset.get("train", dataset[list(dataset.keys())[0]]),
            tokenizer=tokenizer,
            max_length=max_length,
        )

        trainer.train()
        trainer.save_model(output_dir)
        return {"status": "success", "output_dir": output_dir}

    except Exception as exc:
        return {"status": "error", "error": str(exc)}
