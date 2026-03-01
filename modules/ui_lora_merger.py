"""
modules/ui_lora_merger.py — Gradio UI for the LoRA merger.

Exposes:
  - Single LoRA merge
  - Multi-LoRA stack
  - Export to GGUF
"""

from __future__ import annotations

from typing import Any


def create_lora_merger_ui() -> Any:
    """
    Build and return the LoRA Merger Gradio tab.

    Returns a gr.Tab component or None if Gradio is unavailable.
    """
    try:
        import gradio as gr
    except ImportError:
        return None

    from modules.lora_merger import export_gguf, merge_lora, stack_loras

    with gr.Tab("LoRA Merger") as tab:
        gr.Markdown("## 🔗 LoRA Merger\nMerge LoRA adapters into base model and optionally export to GGUF.")

        with gr.Accordion("Single LoRA Merge", open=True):
            with gr.Row():
                base_model_single = gr.Textbox(label="Base Model (HF ID or local path)", placeholder="meta-llama/Llama-2-7b-hf")
                lora_path_single  = gr.Textbox(label="LoRA Adapter Path", placeholder="user_data/loras/my-lora")
                output_dir_single = gr.Textbox(label="Output Directory", placeholder="user_data/training_results/merged")
            merge_btn   = gr.Button("Merge LoRA", variant="primary")
            merge_status = gr.Textbox(label="Status", interactive=False, lines=3)

        with gr.Accordion("Stack Multiple LoRAs", open=False):
            base_model_stack = gr.Textbox(label="Base Model", placeholder="meta-llama/Llama-2-7b-hf")
            lora_paths_stack = gr.Textbox(
                label="LoRA Paths (one per line)",
                placeholder="user_data/loras/lora1\nuser_data/loras/lora2",
                lines=4,
            )
            output_dir_stack = gr.Textbox(label="Output Directory", placeholder="user_data/training_results/stacked")
            stack_btn    = gr.Button("Stack & Merge", variant="primary")
            stack_status  = gr.Textbox(label="Status", interactive=False, lines=3)

        with gr.Accordion("Export to GGUF", open=False):
            with gr.Row():
                model_dir_gguf  = gr.Textbox(label="Merged Model Directory", placeholder="user_data/training_results/merged")
                output_gguf     = gr.Textbox(label="Output GGUF Path", placeholder="user_data/models/merged.Q4_K_M.gguf")
                quant_type      = gr.Dropdown(
                    label="Quantization",
                    choices=["q4_k_m", "q5_k_m", "q8_0", "f16"],
                    value="q4_k_m",
                )
            gguf_btn    = gr.Button("Export to GGUF", variant="primary")
            gguf_status  = gr.Textbox(label="Status", interactive=False, lines=3)

        # ── Event handlers ──────────────────────────────────────────────────
        def _do_merge(base, lora, out):
            if not base or not lora or not out:
                return "❌ Please fill in all fields."
            result = merge_lora(base, lora, out)
            if result["status"] == "success":
                return f"✅ Merged → {result['output_dir']}"
            return f"❌ {result['error']}"

        def _do_stack(base, loras_text, out):
            if not base or not loras_text or not out:
                return "❌ Please fill in all fields."
            paths = [p.strip() for p in loras_text.splitlines() if p.strip()]
            result = stack_loras(base, paths, out)
            if result["status"] == "success":
                return f"✅ Stacked → {result['output_dir']}"
            return f"❌ {result['error']}"

        def _do_gguf(mdir, out_path, quant):
            if not mdir or not out_path:
                return "❌ Please fill in all fields."
            result = export_gguf(mdir, out_path, quant)
            if result["status"] == "success":
                return f"✅ GGUF → {result['output_path']}"
            return f"❌ {result['error']}"

        merge_btn.click(_do_merge, [base_model_single, lora_path_single, output_dir_single], merge_status)
        stack_btn.click(_do_stack, [base_model_stack, lora_paths_stack, output_dir_stack], stack_status)
        gguf_btn.click(_do_gguf, [model_dir_gguf, output_gguf, quant_type], gguf_status)

    return tab
