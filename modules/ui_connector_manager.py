"""Gradio UI tab for the Universal Connector Manager feature."""

from __future__ import annotations

import gradio as gr

from modules import shared

TUTORIAL_URL = (
    "https://github.com/leonlazdev-wq/Gizmo-my-ai-for-google-colab"
    "/blob/main/README.md#connector-manager"
)

_CONNECTORS = {
    "Google Workspace": [
        ("📊", "Google Slides"),
        ("📝", "Google Docs"),
        ("📈", "Google Sheets"),
        ("📅", "Google Calendar"),
        ("📁", "Google Drive"),
        ("📧", "Gmail"),
        ("🎓", "Google Classroom"),
    ],
    "Productivity": [
        ("📓", "Notion"),
        ("🐙", "GitHub"),
        ("💬", "Discord"),
    ],
    "Media": [
        ("🎵", "Spotify"),
        ("▶️", "YouTube Music"),
    ],
}

_SETUP_INSTRUCTIONS: dict[str, str] = {
    "Google Slides": (
        "1. Go to <a href='https://console.cloud.google.com/' target='_blank'>Google Cloud Console</a> "
        "→ Create a project.<br>"
        "2. Enable the <b>Google Slides API</b>.<br>"
        "3. Create OAuth 2.0 credentials and download <code>credentials.json</code>.<br>"
        "4. Enter the path to <code>credentials.json</code> in the Google Slides tab and click Authorize."
    ),
    "Google Docs": (
        "1. Enable the <b>Google Docs API</b> in Google Cloud Console.<br>"
        "2. Create a service account or OAuth 2.0 credentials.<br>"
        "3. Paste the credentials path in the Google Docs tab."
    ),
    "Google Sheets": (
        "1. Enable the <b>Google Sheets API</b> in Google Cloud Console.<br>"
        "2. Create OAuth 2.0 credentials and download <code>credentials.json</code>.<br>"
        "3. Enter the path in the Google Sheets tab."
    ),
    "Google Calendar": (
        "1. Enable the <b>Google Calendar API</b> in Google Cloud Console.<br>"
        "2. Create OAuth 2.0 credentials and download <code>credentials.json</code>.<br>"
        "3. Authorize in the Google Calendar tab."
    ),
    "Google Drive": (
        "1. Enable the <b>Google Drive API</b> in Google Cloud Console.<br>"
        "2. Create OAuth 2.0 credentials and download <code>credentials.json</code>.<br>"
        "3. Authorize in the Google Drive tab."
    ),
    "Gmail": (
        "1. Enable the <b>Gmail API</b> in Google Cloud Console.<br>"
        "2. Create OAuth 2.0 credentials and download <code>credentials.json</code>.<br>"
        "3. Authorize in the Gmail tab."
    ),
    "Google Classroom": (
        "1. Enable the <b>Google Classroom API</b> in Google Cloud Console.<br>"
        "2. Create OAuth 2.0 credentials and download <code>credentials.json</code>.<br>"
        "3. Authorize in the Google Classroom tab."
    ),
    "Notion": (
        "1. Go to <a href='https://www.notion.so/my-integrations' target='_blank'>Notion Integrations</a>.<br>"
        "2. Create a new integration and copy the <b>Internal Integration Token</b>.<br>"
        "3. Share your Notion pages with the integration.<br>"
        "4. Enter the token in the Notion tab."
    ),
    "GitHub": (
        "1. Go to GitHub → Settings → Developer Settings → Personal Access Tokens.<br>"
        "2. Generate a new token with required scopes (repo, read:user).<br>"
        "3. Enter the token in the GitHub tab."
    ),
    "Spotify": (
        "1. Go to <a href='https://developer.spotify.com/dashboard' target='_blank'>Spotify Developer Dashboard</a>.<br>"
        "2. Create an app and copy the <b>Client ID</b> and <b>Client Secret</b>.<br>"
        "3. Enter them in the Music tab."
    ),
    "YouTube Music": (
        "1. Enable the <b>YouTube Data API v3</b> in Google Cloud Console.<br>"
        "2. Create an API key or OAuth 2.0 credentials.<br>"
        "3. Enter the key in the Music tab."
    ),
}


def _check_connector_connected(name: str) -> bool:
    """Check if a connector has a saved token or config."""
    import json
    from pathlib import Path

    token_map = {
        "Google Slides": "user_data/google_slides_token.json",
        "Google Docs": "user_data/google_docs_token.json",
        "Google Sheets": "user_data/google_sheets_token.json",
        "Google Calendar": "user_data/google_calendar_token.json",
        "Google Drive": "user_data/google_drive_token.json",
        "Gmail": "user_data/gmail_token.json",
        "Google Classroom": "user_data/google_classroom_token.json",
        "Notion": "user_data/notion_token.json",
        "GitHub": "user_data/github_token.json",
        "Discord": "user_data/discord_token.json",
        "Spotify": "user_data/spotify_token.json",
        "YouTube Music": "user_data/youtube_music_token.json",
    }
    path = token_map.get(name)
    if not path:
        return False
    try:
        return Path(path).exists() and Path(path).stat().st_size > 0
    except Exception:
        return False


def _get_connector_status_html() -> str:
    """Return an HTML grid of all connector status cards."""
    sections_html = []
    for group, connectors in _CONNECTORS.items():
        cards = []
        for icon, name in connectors:
            connected = _check_connector_connected(name)
            badge = "🟢" if connected else "🔴"
            status_color = "#4CAF50" if connected else "#f44336"
            status_label = "Connected" if connected else "Not connected"
            anchor = name.lower().replace(" ", "-") + "-setup"
            tutorial_href = (
                f"https://github.com/leonlazdev-wq/Gizmo-my-ai-for-google-colab"
                f"/blob/main/README.md#{anchor}"
            )
            cards.append(
                f"<div style='border:1px solid #444;border-radius:8px;padding:10px;min-width:150px;"
                f"background:#1e1e2e;flex:1'>"
                f"<div style='font-size:1.4em'>{icon}</div>"
                f"<div style='font-weight:600;margin:4px 0'>{name}</div>"
                f"<div style='color:{status_color};font-size:.85em'>{badge} {status_label}</div>"
                f"<div style='margin-top:6px'>"
                f"<a href='{tutorial_href}' target='_blank' style='font-size:.8em;color:#8ec8ff'>📖 Tutorial</a>"
                f"</div>"
                f"</div>"
            )
        sections_html.append(
            f"<div style='margin-bottom:16px'>"
            f"<div style='font-weight:600;color:#8ec8ff;margin-bottom:8px'>{group}</div>"
            f"<div style='display:flex;flex-wrap:wrap;gap:10px'>{''.join(cards)}</div>"
            f"</div>"
        )
    return "<div style='padding:8px'>" + "".join(sections_html) + "</div>"


def _refresh_all():
    html = _get_connector_status_html()
    return html, "✅ Status refreshed"


def _get_setup_instructions(connector: str) -> str:
    instructions = _SETUP_INSTRUCTIONS.get(connector, "Select a connector to see setup instructions.")
    return f"<div style='padding:10px;line-height:1.6'>{instructions}</div>"


def _test_connection(connector: str, api_key: str):
    if not connector:
        return "<div style='color:#f44336'>Please select a connector.</div>"
    if not api_key:
        return "<div style='color:#f44336'>Please enter an API key or credentials path.</div>"
    # Stub: actual test would call the relevant module
    return (
        f"<div style='color:#888'>⚙️ Connection test for <b>{connector}</b> not yet implemented. "
        f"Please use the dedicated connector tab.</div>"
    )


def _get_ai_banner() -> str:
    active = [
        name
        for _, connectors in _CONNECTORS.items()
        for _, name in connectors
        if _check_connector_connected(name)
    ]
    if not active:
        return (
            "<div style='padding:10px;background:#1a1a2e;border-radius:6px;color:#888'>"
            "🤖 No connectors are currently feeding data to AI. Connect one to get started.</div>"
        )
    names = ", ".join(active)
    return (
        f"<div style='padding:10px;background:#1a2e1a;border-radius:6px;color:#4CAF50'>"
        f"🤖 Active AI connectors: <b>{names}</b></div>"
    )


def _view_stats():
    total = sum(len(c) for c in _CONNECTORS.values())
    connected = sum(
        1
        for _, connectors in _CONNECTORS.items()
        for _, name in connectors
        if _check_connector_connected(name)
    )
    return (
        f"### 📊 Connector Stats\n\n"
        f"- **Total connectors:** {total}\n"
        f"- **Connected:** {connected}\n"
        f"- **Disconnected:** {total - connected}\n"
    )


def create_ui():
    with gr.Tab("🔗 Connections", elem_id="connector-manager-tab"):
        gr.HTML(
            f"<div style='margin-bottom:8px'>"
            f"<a href='{TUTORIAL_URL}' target='_blank' rel='noopener noreferrer' "
            f"style='font-size:.88em;color:#8ec8ff'>📖 Tutorial: Connector Manager</a>"
            f"</div>"
        )
        gr.HTML(
            "<div style='margin-bottom:12px;color:#ccc'>"
            "Manage all your integrations in one place.</div>"
        )

        shared.gradio['conn_ai_banner'] = gr.HTML(_get_ai_banner())

        gr.Markdown("---")
        gr.Markdown("### 🗂️ All Connectors")
        shared.gradio['conn_grid_html'] = gr.HTML(_get_connector_status_html())
        with gr.Row():
            shared.gradio['conn_refresh_all_btn'] = gr.Button("🔄 Refresh All Status")
            shared.gradio['conn_refresh_status'] = gr.Textbox(label="Status", interactive=False)

        gr.Markdown("---")
        gr.Markdown("### ⚙️ Configure a Connector")
        shared.gradio['conn_select_connector'] = gr.Dropdown(
            label="Configure Connector",
            choices=[
                "Google Slides", "Google Docs", "Google Sheets", "Google Calendar",
                "Google Drive", "Gmail", "Google Classroom", "Notion", "GitHub",
                "Spotify", "YouTube Music",
            ],
            allow_custom_value=True,
        )
        shared.gradio['conn_setup_panel'] = gr.HTML(
            "<div style='padding:10px;color:#888'>Select a connector above to see setup instructions.</div>"
        )
        shared.gradio['conn_api_key'] = gr.Textbox(
            label="API Key / Credentials Path", type="password"
        )
        shared.gradio['conn_test_btn'] = gr.Button("🔗 Test Connection")
        shared.gradio['conn_test_status'] = gr.HTML(
            "<div style='color:#888'>Not tested</div>"
        )

        gr.Markdown("---")
        gr.Markdown("### ⚡ Quick Actions")
        with gr.Row():
            shared.gradio['conn_refresh_all_btn2'] = gr.Button("🔄 Refresh All")
            shared.gradio['conn_view_stats_btn'] = gr.Button("📊 View Stats")
        shared.gradio['conn_stats_output'] = gr.Markdown("")


def create_event_handlers():
    shared.gradio['conn_refresh_all_btn'].click(
        _refresh_all,
        inputs=[],
        outputs=[shared.gradio['conn_grid_html'], shared.gradio['conn_refresh_status']],
    )

    shared.gradio['conn_select_connector'].change(
        _get_setup_instructions,
        inputs=[shared.gradio['conn_select_connector']],
        outputs=[shared.gradio['conn_setup_panel']],
    )

    shared.gradio['conn_test_btn'].click(
        _test_connection,
        inputs=[shared.gradio['conn_select_connector'], shared.gradio['conn_api_key']],
        outputs=[shared.gradio['conn_test_status']],
    )

    shared.gradio['conn_refresh_all_btn2'].click(
        lambda: (_get_connector_status_html(), _get_ai_banner(), "✅ Refreshed"),
        inputs=[],
        outputs=[
            shared.gradio['conn_grid_html'],
            shared.gradio['conn_ai_banner'],
            shared.gradio['conn_refresh_status'],
        ],
    )

    shared.gradio['conn_view_stats_btn'].click(
        _view_stats,
        inputs=[],
        outputs=[shared.gradio['conn_stats_output']],
    )
