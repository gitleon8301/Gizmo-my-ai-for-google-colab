"""Gradio UI tab for the Gmail integration feature."""

from __future__ import annotations

import gradio as gr

from modules import shared

TUTORIAL_URL = (
    "https://github.com/leonlazdev-wq/Gizmo-my-ai-for-google-colab"
    "/blob/main/README.md#gmail-setup"
)


def _authorize(creds_path: str):
    if not creds_path:
        return "<div style='color:#f44336'>No credentials file provided.</div>"
    try:
        from modules.gmail_integration import authorize  # type: ignore
        success, msg = authorize(creds_path)
        color = "#4CAF50" if success else "#f44336"
        return f"<div style='color:{color};font-weight:600'>{msg}</div>"
    except Exception as exc:
        return f"<div style='color:#f44336'>Error: {exc}</div>"


def _reconnect():
    try:
        from modules.gmail_integration import connect_from_saved  # type: ignore
        success, msg = connect_from_saved()
        color = "#4CAF50" if success else "#f44336"
        return f"<div style='color:{color};font-weight:600'>{msg}</div>"
    except Exception as exc:
        return f"<div style='color:#f44336'>Error: {exc}</div>"


def _connect_ai():
    try:
        from modules.gmail_integration import is_connected  # type: ignore
        if is_connected():
            return "<div style='color:#4CAF50;font-weight:600'>✅ Gmail connected to AI</div>"
        return "<div style='color:#f44336'>Not connected. Authorize first.</div>"
    except Exception:
        return "<div style='color:#f44336'>Gmail not connected to AI.</div>"


def _fetch_classroom_alerts():
    try:
        from modules.gmail_integration import detect_classroom_assignments  # type: ignore
        items, msg = detect_classroom_assignments()
        if not items:
            return (
                "<div style='color:#888'>No Classroom assignments detected in Gmail.</div>",
                msg,
            )
        rows = "".join(f"<li>📋 {item}</li>" for item in items)
        return (
            f"<div style='color:#4CAF50'>"
            f"<ul style='padding-left:20px'>{rows}</ul></div>",
            msg,
        )
    except Exception as exc:
        return (
            "<div style='color:#888'>Connect Gmail to detect Classroom assignments</div>",
            f"Error: {exc}",
        )


def _add_classroom_to_calendar():
    try:
        from modules.gmail_integration import sync_classroom_to_calendar  # type: ignore
        _, msg = sync_classroom_to_calendar()
        return msg
    except Exception as exc:
        return f"Error: {exc}"


def _fetch_inbox():
    try:
        from modules.gmail_integration import fetch_inbox  # type: ignore
        emails, msg = fetch_inbox()
        rows = [[e["from"], e["subject"], e["date"], e["preview"]] for e in emails]
        return msg, rows
    except Exception as exc:
        return f"Error: {exc}", []


def _search_inbox(query: str):
    if not query:
        return "Enter a search query.", []
    try:
        from modules.gmail_integration import search_emails  # type: ignore
        emails, msg = search_emails(query)
        rows = [[e["from"], e["subject"], e["date"], e["preview"]] for e in emails]
        return msg, rows
    except Exception as exc:
        return f"Error: {exc}", []


def _view_email(email_id: str):
    if not email_id:
        return "No email selected.", ""
    try:
        from modules.gmail_integration import get_email_content  # type: ignore
        content, msg = get_email_content(email_id)
        return msg, content or ""
    except Exception as exc:
        return f"Error: {exc}", ""


def _summarize_email(email_id: str):
    if not email_id:
        return "No email selected.", ""
    try:
        from modules.gmail_integration import get_email_content  # type: ignore
        content, _ = get_email_content(email_id)
        if not content:
            return "Could not fetch email content.", ""
        from modules.text_generation import generate_reply as _gen  # type: ignore
        prompt = f"Please summarize the following email in 3-5 bullet points:\n\n{content}"
        full = ""
        for chunk in _gen(prompt, state={}, stopping_strings=[]):
            if isinstance(chunk, str):
                full = chunk
        return "✅ Summary generated.", full
    except Exception as exc:
        return f"Error: {exc}", ""


def _draft_reply(email_id: str):
    if not email_id:
        return "No email selected.", ""
    try:
        from modules.gmail_integration import get_email_content  # type: ignore
        content, _ = get_email_content(email_id)
        if not content:
            return "Could not fetch email content.", ""
        from modules.text_generation import generate_reply as _gen  # type: ignore
        prompt = (
            f"Draft a professional reply to the following email. "
            f"Be concise and helpful:\n\n{content}"
        )
        full = ""
        for chunk in _gen(prompt, state={}, stopping_strings=[]):
            if isinstance(chunk, str):
                full = chunk
        return "✅ Draft reply generated.", full
    except Exception as exc:
        return f"Error: {exc}", ""


def _ai_draft_compose(to: str, subject: str, body: str, tone: str):
    if not subject:
        return "Please provide a subject.", body
    try:
        from modules.text_generation import generate_reply as _gen  # type: ignore
        prompt = (
            f"Write a {tone.lower()} email.\n"
            f"To: {to or '(recipient)'}\n"
            f"Subject: {subject}\n"
            f"Context/notes: {body or '(none)'}\n\n"
            "Write only the email body text."
        )
        full = ""
        for chunk in _gen(prompt, state={}, stopping_strings=[]):
            if isinstance(chunk, str):
                full = chunk
        return "✅ Draft ready.", full
    except Exception as exc:
        return f"Error: {exc}", body


def _send_email(to: str, subject: str, body: str):
    if not to or not subject or not body:
        return "Please fill in To, Subject, and Message."
    try:
        from modules.gmail_integration import send_email  # type: ignore
        _, msg = send_email(to, subject, body)
        return msg
    except Exception as exc:
        return f"Error: {exc}"


def _advanced_search(query: str, sender: str, date_from: str, date_to: str):
    try:
        from modules.gmail_integration import advanced_search  # type: ignore
        emails, msg = advanced_search(query, sender, date_from, date_to)
        rows = [[e["from"], e["subject"], e["date"], e["preview"]] for e in emails]
        return msg, rows
    except Exception as exc:
        return f"Error: {exc}", []


def create_ui():
    with gr.Tab("📧 Gmail", elem_id="gmail-tab"):
        gr.HTML(
            f"<div style='margin-bottom:8px'>"
            f"<a href='{TUTORIAL_URL}' target='_blank' rel='noopener noreferrer' "
            f"style='font-size:.88em;color:#8ec8ff'>📖 Tutorial: How to set up Gmail integration</a>"
            f"</div>"
        )

        with gr.Accordion("🔌 Connection", open=True):
            with gr.Row():
                shared.gradio['gmail_creds_path'] = gr.Textbox(
                    label="Path to credentials.json",
                    placeholder="/path/to/credentials.json",
                    scale=4,
                )
                shared.gradio['gmail_authorize_btn'] = gr.Button(
                    "🔗 Authorize", variant="primary", scale=1
                )
            shared.gradio['gmail_reconnect_btn'] = gr.Button(
                "Reconnect (use saved token)", size="sm"
            )
            shared.gradio['gmail_status'] = gr.HTML(
                "<div style='color:#888'>Not connected</div>"
            )
            shared.gradio['gmail_connect_ai_btn'] = gr.Button("🤖 Connect to AI")

        gr.Markdown("---")
        gr.Markdown("### 🎓 Classroom Alert Banner")
        shared.gradio['gmail_classroom_banner'] = gr.HTML(
            "<div style='color:#888'>Connect Gmail to detect Classroom assignments</div>"
        )
        with gr.Row():
            shared.gradio['gmail_add_to_calendar_btn'] = gr.Button("📅 Add All to Calendar")
        shared.gradio['gmail_classroom_status'] = gr.Textbox(label="Status", interactive=False)

        gr.Markdown("---")
        gr.Markdown("### 📨 Inbox")
        with gr.Row():
            shared.gradio['gmail_fetch_inbox_btn'] = gr.Button("📨 Fetch Inbox")
            shared.gradio['gmail_inbox_search'] = gr.Textbox(
                label="Search", placeholder="Search emails...", scale=3
            )
        shared.gradio['gmail_fetch_status'] = gr.Textbox(label="Status", interactive=False)
        shared.gradio['gmail_inbox_table'] = gr.Dataframe(
            headers=["From", "Subject", "Date", "Preview"],
            label="Inbox",
            interactive=False,
        )
        shared.gradio['gmail_selected_email'] = gr.Textbox(
            label="Selected Email ID", interactive=False
        )
        shared.gradio['gmail_view_btn'] = gr.Button("📖 View Email")
        shared.gradio['gmail_email_content'] = gr.Textbox(
            label="Email Content", lines=8, interactive=False
        )

        gr.Markdown("---")
        gr.Markdown("### 🤖 AI Actions")
        with gr.Row():
            shared.gradio['gmail_summarize_btn'] = gr.Button("📋 Summarize Selected")
            shared.gradio['gmail_draft_reply_btn'] = gr.Button("✍️ Draft Reply")
        shared.gradio['gmail_ai_status'] = gr.Textbox(label="Status", interactive=False)
        shared.gradio['gmail_ai_output'] = gr.Textbox(
            label="AI Output", lines=6, interactive=False
        )

        with gr.Accordion("✍️ Compose", open=False):
            shared.gradio['gmail_compose_to'] = gr.Textbox(label="To")
            shared.gradio['gmail_compose_subject'] = gr.Textbox(label="Subject")
            shared.gradio['gmail_compose_body'] = gr.Textbox(label="Message", lines=6)
            shared.gradio['gmail_compose_tone'] = gr.Dropdown(
                choices=["Formal", "Casual", "Professional", "Friendly"],
                value="Professional",
                allow_custom_value=True,
                label="Tone",
            )
            with gr.Row():
                shared.gradio['gmail_ai_draft_btn'] = gr.Button("🤖 AI Draft")
                shared.gradio['gmail_send_btn'] = gr.Button("📤 Send", variant="primary")
            shared.gradio['gmail_send_status'] = gr.Textbox(label="Status", interactive=False)

        with gr.Accordion("🔍 Advanced Search", open=False):
            shared.gradio['gmail_adv_search'] = gr.Textbox(
                label="Search Query", placeholder="Search query..."
            )
            with gr.Row():
                shared.gradio['gmail_sender_filter'] = gr.Textbox(label="From (sender)", scale=2)
                shared.gradio['gmail_date_from'] = gr.Textbox(
                    label="Date From (YYYY-MM-DD)", scale=2
                )
                shared.gradio['gmail_date_to'] = gr.Textbox(
                    label="Date To (YYYY-MM-DD)", scale=2
                )
            shared.gradio['gmail_adv_search_btn'] = gr.Button("🔍 Search")
            shared.gradio['gmail_adv_status'] = gr.Textbox(label="Status", interactive=False)
            shared.gradio['gmail_adv_results'] = gr.Dataframe(
                headers=["From", "Subject", "Date", "Preview"],
                label="Search Results",
                interactive=False,
            )


def create_event_handlers():
    shared.gradio['gmail_authorize_btn'].click(
        _authorize,
        inputs=[shared.gradio['gmail_creds_path']],
        outputs=[shared.gradio['gmail_status']],
    )

    shared.gradio['gmail_reconnect_btn'].click(
        _reconnect,
        inputs=[],
        outputs=[shared.gradio['gmail_status']],
    )

    shared.gradio['gmail_connect_ai_btn'].click(
        _connect_ai,
        inputs=[],
        outputs=[shared.gradio['gmail_status']],
    )

    shared.gradio['gmail_fetch_inbox_btn'].click(
        _fetch_inbox,
        inputs=[],
        outputs=[shared.gradio['gmail_fetch_status'], shared.gradio['gmail_inbox_table']],
    )

    shared.gradio['gmail_inbox_search'].submit(
        _search_inbox,
        inputs=[shared.gradio['gmail_inbox_search']],
        outputs=[shared.gradio['gmail_fetch_status'], shared.gradio['gmail_inbox_table']],
    )

    shared.gradio['gmail_view_btn'].click(
        _view_email,
        inputs=[shared.gradio['gmail_selected_email']],
        outputs=[shared.gradio['gmail_fetch_status'], shared.gradio['gmail_email_content']],
    )

    shared.gradio['gmail_summarize_btn'].click(
        _summarize_email,
        inputs=[shared.gradio['gmail_selected_email']],
        outputs=[shared.gradio['gmail_ai_status'], shared.gradio['gmail_ai_output']],
        show_progress=True,
    )

    shared.gradio['gmail_draft_reply_btn'].click(
        _draft_reply,
        inputs=[shared.gradio['gmail_selected_email']],
        outputs=[shared.gradio['gmail_ai_status'], shared.gradio['gmail_ai_output']],
        show_progress=True,
    )

    shared.gradio['gmail_ai_draft_btn'].click(
        _ai_draft_compose,
        inputs=[
            shared.gradio['gmail_compose_to'],
            shared.gradio['gmail_compose_subject'],
            shared.gradio['gmail_compose_body'],
            shared.gradio['gmail_compose_tone'],
        ],
        outputs=[shared.gradio['gmail_send_status'], shared.gradio['gmail_compose_body']],
        show_progress=True,
    )

    shared.gradio['gmail_send_btn'].click(
        _send_email,
        inputs=[
            shared.gradio['gmail_compose_to'],
            shared.gradio['gmail_compose_subject'],
            shared.gradio['gmail_compose_body'],
        ],
        outputs=[shared.gradio['gmail_send_status']],
    )

    shared.gradio['gmail_add_to_calendar_btn'].click(
        _add_classroom_to_calendar,
        inputs=[],
        outputs=[shared.gradio['gmail_classroom_status']],
    )

    shared.gradio['gmail_adv_search_btn'].click(
        _advanced_search,
        inputs=[
            shared.gradio['gmail_adv_search'],
            shared.gradio['gmail_sender_filter'],
            shared.gradio['gmail_date_from'],
            shared.gradio['gmail_date_to'],
        ],
        outputs=[shared.gradio['gmail_adv_status'], shared.gradio['gmail_adv_results']],
    )
