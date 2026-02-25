"""Gradio UI tab for the Google Drive integration."""

from __future__ import annotations

import gradio as gr

from modules import shared

TUTORIAL_URL = (
    "https://github.com/leonlazdev-wq/Gizmo-my-ai-for-google-colab"
    "/blob/main/README.md#google-drive-setup"
)


def _authorize(creds_path: str):
    if not creds_path:
        return (
            "<div style='color:#f44336'>No credentials file provided.</div>",
            "<div style='color:#888'>Not connected</div>",
        )
    try:
        from modules.google_drive_sync import authorize  # type: ignore
        success, msg = authorize(creds_path)
        color = "#4CAF50" if success else "#f44336"
        return (
            f"<div style='color:{color};font-weight:600'>{msg}</div>",
            f"<div style='color:{color}'>{msg}</div>",
        )
    except Exception as exc:
        return (
            f"<div style='color:#f44336'>Error: {exc}</div>",
            "<div style='color:#888'>Not connected</div>",
        )


def _reconnect():
    try:
        from modules.google_drive_sync import connect_from_saved  # type: ignore
        success, msg = connect_from_saved()
        color = "#4CAF50" if success else "#f44336"
        return f"<div style='color:{color};font-weight:600'>{msg}</div>"
    except Exception as exc:
        return f"<div style='color:#f44336'>Error: {exc}</div>"


def _connect_ai():
    try:
        from modules.google_drive_sync import is_connected  # type: ignore
        if is_connected():
            return "<div style='color:#4CAF50;font-weight:600'>✅ Google Drive connected to AI</div>"
        return "<div style='color:#f44336'>Not connected. Authorize first.</div>"
    except Exception:
        return "<div style='color:#f44336'>Google Drive not connected to AI.</div>"


def _search_files(query: str, file_type: str):
    if not query and file_type == "All":
        return "Enter a search query or select a file type.", []
    try:
        from modules.google_drive_sync import search_files  # type: ignore
        files, msg = search_files(query, file_type)
        rows = [[f["name"], f["type"], f["size"], f["modified"], f["owner"]] for f in files]
        return msg, rows
    except Exception as exc:
        return f"Error: {exc}", []


def _browse_drive():
    try:
        from modules.google_drive_sync import list_files  # type: ignore
        files, msg = list_files()
        rows = [[f["name"], f["type"], f["size"], f["modified"], f["owner"]] for f in files]
        return msg, rows
    except Exception as exc:
        return f"Error: {exc}", []


def _open_selected(file_name: str):
    if not file_name:
        return "No file selected.", ""
    try:
        from modules.google_drive_sync import open_file  # type: ignore
        content, msg = open_file(file_name)
        return msg, content or ""
    except Exception as exc:
        return f"Error: {exc}", ""


def _upload_file(file, dest_folder: str):
    if file is None:
        return "No file selected."
    try:
        from modules.google_drive_sync import upload_file  # type: ignore
        _, msg = upload_file(file.name, dest_folder)
        return msg
    except Exception as exc:
        return f"Error: {exc}"


def _sync_now(sync_folder: str):
    try:
        from modules.google_drive_sync import sync  # type: ignore
        _, msg = sync(sync_folder)
        return msg
    except Exception as exc:
        return f"Error: {exc}"


def create_ui():
    with gr.Tab("📁 Google Drive", elem_id="google-drive-tab"):
        gr.HTML(
            f"<div style='margin-bottom:8px'>"
            f"<a href='{TUTORIAL_URL}' target='_blank' rel='noopener noreferrer' "
            f"style='font-size:.88em;color:#8ec8ff'>📖 Tutorial: How to set up Google Drive integration</a>"
            f"</div>"
        )

        with gr.Accordion("🔌 Connection", open=True):
            with gr.Row():
                shared.gradio['gdrive_creds_path'] = gr.Textbox(
                    label="Path to credentials.json",
                    placeholder="/path/to/credentials.json",
                    scale=4,
                )
                shared.gradio['gdrive_authorize_btn'] = gr.Button(
                    "🔗 Authorize", variant="primary", scale=1
                )
            shared.gradio['gdrive_reconnect_btn'] = gr.Button(
                "Reconnect (use saved token)", size="sm"
            )
            shared.gradio['gdrive_status'] = gr.HTML(
                "<div style='color:#888'>Not connected</div>"
            )
            shared.gradio['gdrive_connect_ai_btn'] = gr.Button("🤖 Connect to AI")
            shared.gradio['gdrive_ai_status'] = gr.HTML(
                "<div style='color:#888'>AI connection: inactive</div>"
            )

        with gr.Accordion("🔍 Browse & Search", open=False):
            with gr.Row():
                shared.gradio['gdrive_search_query'] = gr.Textbox(
                    label="Search files...", placeholder="Search files...", scale=3
                )
                shared.gradio['gdrive_file_type_filter'] = gr.Dropdown(
                    label="File Type",
                    choices=["All", "Documents", "Spreadsheets", "PDFs", "Presentations", "Images"],
                    value="All",
                    allow_custom_value=True,
                    scale=2,
                )
            with gr.Row():
                shared.gradio['gdrive_search_btn'] = gr.Button("🔍 Search")
                shared.gradio['gdrive_browse_btn'] = gr.Button("📂 Browse Drive")
            shared.gradio['gdrive_search_status'] = gr.Textbox(label="Status", interactive=False)
            shared.gradio['gdrive_files_table'] = gr.Dataframe(
                headers=["Name", "Type", "Size", "Last Modified", "Owner"],
                label="Files",
                interactive=False,
            )
            with gr.Row():
                shared.gradio['gdrive_open_btn'] = gr.Button("📂 Open Selected")
                shared.gradio['gdrive_download_btn'] = gr.Button("📥 Download")

        with gr.Accordion("📤 Upload", open=False):
            shared.gradio['gdrive_upload_file'] = gr.File(label="Select file to upload")
            shared.gradio['gdrive_dest_folder'] = gr.Dropdown(
                label="Destination Folder",
                choices=["My Drive", "Gizmo Sync"],
                allow_custom_value=True,
            )
            shared.gradio['gdrive_upload_btn'] = gr.Button(
                "📤 Upload to Drive", variant="primary"
            )
            shared.gradio['gdrive_upload_status'] = gr.Textbox(
                label="Upload Status", interactive=False
            )

        with gr.Accordion("🔄 Gizmo Sync Settings", open=False):
            shared.gradio['gdrive_sync_folder'] = gr.Dropdown(
                label="Gizmo Sync Folder",
                choices=["My Drive/Gizmo"],
                allow_custom_value=True,
            )
            shared.gradio['gdrive_auto_sync'] = gr.Checkbox(
                label="Auto-sync exports to Drive", value=False
            )
            shared.gradio['gdrive_sync_btn'] = gr.Button("🔄 Sync Now")
            shared.gradio['gdrive_sync_status'] = gr.Textbox(
                label="Sync Status", interactive=False
            )

        gr.Markdown("---")
        gr.Markdown("### 📄 Selected File Preview")
        shared.gradio['gdrive_selected_file'] = gr.Textbox(
            label="Selected File", interactive=False
        )
        shared.gradio['gdrive_file_preview'] = gr.Textbox(
            label="File Preview / Content", lines=8, interactive=False
        )


def create_event_handlers():
    shared.gradio['gdrive_authorize_btn'].click(
        _authorize,
        inputs=[shared.gradio['gdrive_creds_path']],
        outputs=[shared.gradio['gdrive_status'], shared.gradio['gdrive_ai_status']],
    )

    shared.gradio['gdrive_reconnect_btn'].click(
        _reconnect,
        inputs=[],
        outputs=[shared.gradio['gdrive_status']],
    )

    shared.gradio['gdrive_connect_ai_btn'].click(
        _connect_ai,
        inputs=[],
        outputs=[shared.gradio['gdrive_ai_status']],
    )

    shared.gradio['gdrive_search_btn'].click(
        _search_files,
        inputs=[shared.gradio['gdrive_search_query'], shared.gradio['gdrive_file_type_filter']],
        outputs=[shared.gradio['gdrive_search_status'], shared.gradio['gdrive_files_table']],
    )

    shared.gradio['gdrive_browse_btn'].click(
        _browse_drive,
        inputs=[],
        outputs=[shared.gradio['gdrive_search_status'], shared.gradio['gdrive_files_table']],
    )

    shared.gradio['gdrive_open_btn'].click(
        _open_selected,
        inputs=[shared.gradio['gdrive_selected_file']],
        outputs=[shared.gradio['gdrive_search_status'], shared.gradio['gdrive_file_preview']],
    )

    shared.gradio['gdrive_upload_btn'].click(
        _upload_file,
        inputs=[shared.gradio['gdrive_upload_file'], shared.gradio['gdrive_dest_folder']],
        outputs=[shared.gradio['gdrive_upload_status']],
    )

    shared.gradio['gdrive_sync_btn'].click(
        _sync_now,
        inputs=[shared.gradio['gdrive_sync_folder']],
        outputs=[shared.gradio['gdrive_sync_status']],
    )
