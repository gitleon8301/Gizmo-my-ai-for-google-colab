"""
modules/training_eval.py — Post-training evaluation for Gizmo MY-AI.

Computes:
  - Perplexity on a test set
  - Responses to configurable test prompts
  - Comparison with base model (optional)
  - Training report card (JSON + human-readable text)

Dependencies (lazy-imported):
    pip install transformers torch
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Perplexity
# ---------------------------------------------------------------------------

def compute_perplexity(
    model_path: str,
    test_texts: List[str],
    max_length: int = 512,
) -> Optional[float]:
    """
    Compute average perplexity of *model_path* on *test_texts*.

    Returns None on failure.
    """
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model     = AutoModelForCausalLM.from_pretrained(model_path)
        model.eval()

        total_nll = 0.0
        total_tok = 0

        with torch.no_grad():
            for text in test_texts:
                enc = tokenizer(
                    text,
                    return_tensors="pt",
                    truncation=True,
                    max_length=max_length,
                )
                input_ids = enc["input_ids"]
                out = model(input_ids, labels=input_ids)
                total_nll += out.loss.item() * input_ids.shape[1]
                total_tok += input_ids.shape[1]

        return math.exp(total_nll / total_tok) if total_tok > 0 else None
    except Exception as exc:
        print(f"[training_eval] perplexity error: {exc}")
        return None


# ---------------------------------------------------------------------------
# Test prompt responses
# ---------------------------------------------------------------------------

def run_test_prompts(
    model_path: str,
    prompts: List[str],
    max_new_tokens: int = 200,
) -> List[Dict[str, str]]:
    """
    Generate responses to *prompts* and return list of {prompt, response} dicts.
    """
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

        pipe = pipeline(
            "text-generation",
            model=model_path,
            device_map="auto",
            torch_dtype=torch.float16,
        )
        results = []
        for prompt in prompts:
            output = pipe(prompt, max_new_tokens=max_new_tokens, do_sample=False)
            generated = output[0]["generated_text"][len(prompt):]
            results.append({"prompt": prompt, "response": generated.strip()})
        return results
    except Exception as exc:
        print(f"[training_eval] prompt eval error: {exc}")
        return []


# ---------------------------------------------------------------------------
# Report card
# ---------------------------------------------------------------------------

def build_report_card(
    model_path: str,
    base_model_path: Optional[str] = None,
    test_texts: Optional[List[str]] = None,
    test_prompts: Optional[List[str]] = None,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a full training report card.

    Saves JSON + text report to *output_dir* (defaults to model_path/eval/).
    Returns the report dict.
    """
    if output_dir is None:
        output_dir = str(Path(model_path) / "eval")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    default_prompts = [
        "Explain the concept of recursion in programming.",
        "Write a Python function that reverses a string.",
        "What is the capital of France?",
    ]
    test_prompts = test_prompts or default_prompts
    test_texts   = test_texts   or default_prompts

    report: Dict[str, Any] = {
        "model":      model_path,
        "timestamp":  time.strftime("%Y-%m-%d %H:%M:%S"),
        "perplexity": compute_perplexity(model_path, test_texts),
        "responses":  run_test_prompts(model_path, test_prompts),
    }

    if base_model_path:
        report["base_perplexity"] = compute_perplexity(base_model_path, test_texts)

    # Improvement summary
    if base_model_path and report["perplexity"] and report.get("base_perplexity"):
        delta = report["base_perplexity"] - report["perplexity"]
        report["perplexity_improvement"] = round(delta, 4)

    # Save JSON
    json_path = Path(output_dir) / "report.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Save human-readable text
    lines = [
        "=" * 60,
        "Gizmo MY-AI — Training Evaluation Report",
        "=" * 60,
        f"Model:      {report['model']}",
        f"Date:       {report['timestamp']}",
        f"Perplexity: {report.get('perplexity', 'N/A')}",
    ]
    if base_model_path:
        lines.append(f"Base PPL:   {report.get('base_perplexity', 'N/A')}")
        lines.append(f"Δ PPL:      {report.get('perplexity_improvement', 'N/A')}")
    lines.append("\n--- Test Prompt Responses ---\n")
    for item in report.get("responses", []):
        lines.append(f"Q: {item['prompt']}")
        lines.append(f"A: {item['response']}")
        lines.append("")

    txt_path = Path(output_dir) / "report.txt"
    txt_path.write_text("\n".join(lines), encoding="utf-8")

    report["report_json"] = str(json_path)
    report["report_txt"]  = str(txt_path)
    return report
