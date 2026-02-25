"""Gradio UI tab for the Music integration feature."""

from __future__ import annotations

import gradio as gr

from modules import shared

TUTORIAL_URL = (
    "https://github.com/leonlazdev-wq/Gizmo-my-ai-for-google-colab"
    "/blob/main/README.md#music-integration"
)


def _connect(platform: str, client_id: str, client_secret: str):
    if not client_id:
        return "<div style='color:#f44336'>No API key / Client ID provided.</div>"
    try:
        from modules.music_integration import connect  # type: ignore
        success, msg = connect(platform, client_id, client_secret)
        color = "#4CAF50" if success else "#f44336"
        return f"<div style='color:{color};font-weight:600'>{msg}</div>"
    except Exception as exc:
        return f"<div style='color:#f44336'>Error: {exc}</div>"


def _connect_ai(platform: str):
    try:
        from modules.music_integration import is_connected  # type: ignore
        if is_connected(platform):
            return "<div style='color:#4CAF50;font-weight:600'>✅ Music connected to AI</div>"
        return "<div style='color:#f44336'>Not connected. Authorize first.</div>"
    except Exception:
        return "<div style='color:#f44336'>Music not connected to AI.</div>"


def _play_pause():
    try:
        from modules.music_integration import play_pause  # type: ignore
        msg = play_pause()
        return msg
    except Exception as exc:
        return f"Error: {exc}"


def _prev_track():
    try:
        from modules.music_integration import previous_track  # type: ignore
        return previous_track()
    except Exception as exc:
        return f"Error: {exc}"


def _next_track():
    try:
        from modules.music_integration import next_track  # type: ignore
        return next_track()
    except Exception as exc:
        return f"Error: {exc}"


def _set_volume(volume: int):
    try:
        from modules.music_integration import set_volume  # type: ignore
        return set_volume(int(volume))
    except Exception as exc:
        return f"Error: {exc}"


def _search_music(query: str):
    if not query:
        return "Enter a search query.", []
    try:
        from modules.music_integration import search  # type: ignore
        results, msg = search(query)
        rows = [[r["title"], r["artist"], r["album"], r["duration"]] for r in results]
        return msg, rows
    except Exception as exc:
        return f"Error: {exc}", []


def _play_selected(title: str):
    if not title:
        return "No track selected."
    try:
        from modules.music_integration import play_track  # type: ignore
        return play_track(title)
    except Exception as exc:
        return f"Error: {exc}"


def _generate_study_playlist(mood: str, subject: str):
    try:
        from modules.text_generation import generate_reply as _gen  # type: ignore
        prompt = (
            f"Generate a study playlist for mood: {mood}."
            + (f" Subject: {subject}." if subject else "")
            + " List 10 songs with artist names. Format: Song Title - Artist"
        )
        full = ""
        for chunk in _gen(prompt, state={}, stopping_strings=[]):
            if isinstance(chunk, str):
                full = chunk
        return "✅ Playlist generated.", full
    except Exception as exc:
        return f"Error: {exc}", ""


def _fetch_playlists():
    try:
        from modules.music_integration import get_playlists  # type: ignore
        playlists, msg = get_playlists()
        rows = [[p["name"], p["tracks"], p["platform"]] for p in playlists]
        return msg, rows
    except Exception as exc:
        return f"Error: {exc}", []


def _play_ambient(ambient_type: str, volume: int):
    try:
        from modules.music_integration import play_ambient  # type: ignore
        return play_ambient(ambient_type, int(volume))
    except Exception as exc:
        return f"Error: {exc}"


def _stop_ambient():
    try:
        from modules.music_integration import stop_ambient  # type: ignore
        return stop_ambient()
    except Exception as exc:
        return f"Error: {exc}"


def create_ui():
    with gr.Tab("🎵 Music", elem_id="music-tab"):
        gr.HTML(
            f"<div style='margin-bottom:8px'>"
            f"<a href='{TUTORIAL_URL}' target='_blank' rel='noopener noreferrer' "
            f"style='font-size:.88em;color:#8ec8ff'>📖 Tutorial: Music Integration</a>"
            f"</div>"
        )

        with gr.Row():
            shared.gradio['music_platform'] = gr.Radio(
                choices=["Spotify", "YouTube Music"],
                value="Spotify",
                label="Platform",
            )

        with gr.Accordion("🔌 Connection", open=True):
            shared.gradio['music_client_id'] = gr.Textbox(
                label="Client ID / API Key", type="password"
            )
            shared.gradio['music_client_secret'] = gr.Textbox(
                label="Client Secret", type="password"
            )
            shared.gradio['music_connect_btn'] = gr.Button("🔗 Connect", variant="primary")
            shared.gradio['music_status'] = gr.HTML(
                "<div style='color:#888'>Not connected</div>"
            )
            shared.gradio['music_connect_ai_btn'] = gr.Button("🤖 Connect to AI")

        gr.Markdown("---")
        gr.Markdown("### 🎶 Now Playing")
        shared.gradio['music_now_playing'] = gr.HTML(
            "<div style='padding:10px;border:1px solid #444;border-radius:8px;color:#888'>"
            "No track playing</div>"
        )
        with gr.Row():
            shared.gradio['music_prev_btn'] = gr.Button("⏮")
            shared.gradio['music_play_btn'] = gr.Button("▶ / ⏸")
            shared.gradio['music_next_btn'] = gr.Button("⏭")
        shared.gradio['music_volume'] = gr.Slider(
            label="Volume", minimum=0, maximum=100, value=70
        )

        with gr.Accordion("🔍 Search", open=False):
            shared.gradio['music_search_query'] = gr.Textbox(
                label="Search",
                placeholder="Search songs, artists, albums...",
            )
            shared.gradio['music_search_btn'] = gr.Button("🔍 Search")
            shared.gradio['music_search_status'] = gr.Textbox(label="Status", interactive=False)
            shared.gradio['music_search_results'] = gr.Dataframe(
                headers=["Title", "Artist", "Album", "Duration"],
                label="Results",
                interactive=False,
            )
            shared.gradio['music_play_selected_btn'] = gr.Button("▶ Play Selected")

        with gr.Accordion("🎓 AI Study Playlist Generator", open=False):
            shared.gradio['music_mood'] = gr.Dropdown(
                choices=["Focused", "Energetic", "Calm", "Ambient", "Happy", "Motivational"],
                value="Focused",
                allow_custom_value=True,
                label="Mood",
            )
            shared.gradio['music_subject'] = gr.Textbox(
                label="Study Subject (optional)",
                placeholder="Math, History, etc.",
            )
            shared.gradio['music_gen_playlist_btn'] = gr.Button(
                "🎵 Generate Study Playlist", variant="primary"
            )
            shared.gradio['music_gen_status'] = gr.Textbox(label="Status", interactive=False)
            shared.gradio['music_gen_result'] = gr.Markdown("")

        with gr.Accordion("⏱️ Pomodoro Music Settings", open=False):
            shared.gradio['music_focus_playlist'] = gr.Dropdown(
                label="Focus Playlist", choices=[], allow_custom_value=True
            )
            shared.gradio['music_break_playlist'] = gr.Dropdown(
                label="Break Playlist", choices=[], allow_custom_value=True
            )
            shared.gradio['music_auto_play'] = gr.Checkbox(
                label="Auto-play during Pomodoro", value=False
            )
            shared.gradio['music_focus_volume'] = gr.Slider(
                label="Focus Volume", minimum=0, maximum=100, value=50
            )
            shared.gradio['music_break_volume'] = gr.Slider(
                label="Break Volume", minimum=0, maximum=100, value=70
            )

        with gr.Accordion("🌧️ Ambient Sounds", open=False):
            shared.gradio['music_ambient_type'] = gr.Dropdown(
                choices=["Lofi", "Rain", "Coffee Shop", "Library", "Nature", "White Noise"],
                value="Lofi",
                allow_custom_value=True,
                label="Ambient Sound",
            )
            shared.gradio['music_ambient_volume'] = gr.Slider(
                label="Ambient Volume", minimum=0, maximum=100, value=40
            )
            with gr.Row():
                shared.gradio['music_ambient_play_btn'] = gr.Button("▶ Play Ambient")
                shared.gradio['music_ambient_stop_btn'] = gr.Button("⏹ Stop")
            shared.gradio['music_ambient_status'] = gr.Textbox(label="Status", interactive=False)

        with gr.Accordion("📋 Your Playlists", open=False):
            shared.gradio['music_fetch_playlists_btn'] = gr.Button("🔄 Fetch Playlists")
            shared.gradio['music_playlists_list'] = gr.Dataframe(
                headers=["Name", "Tracks", "Platform"],
                label="Playlists",
                interactive=False,
            )
            shared.gradio['music_play_playlist_btn'] = gr.Button("▶ Play Playlist")


def create_event_handlers():
    shared.gradio['music_connect_btn'].click(
        _connect,
        inputs=[
            shared.gradio['music_platform'],
            shared.gradio['music_client_id'],
            shared.gradio['music_client_secret'],
        ],
        outputs=[shared.gradio['music_status']],
    )

    shared.gradio['music_connect_ai_btn'].click(
        _connect_ai,
        inputs=[shared.gradio['music_platform']],
        outputs=[shared.gradio['music_status']],
    )

    shared.gradio['music_play_btn'].click(
        _play_pause,
        inputs=[],
        outputs=[shared.gradio['music_now_playing']],
    )

    shared.gradio['music_prev_btn'].click(
        _prev_track,
        inputs=[],
        outputs=[shared.gradio['music_now_playing']],
    )

    shared.gradio['music_next_btn'].click(
        _next_track,
        inputs=[],
        outputs=[shared.gradio['music_now_playing']],
    )

    shared.gradio['music_search_btn'].click(
        _search_music,
        inputs=[shared.gradio['music_search_query']],
        outputs=[shared.gradio['music_search_status'], shared.gradio['music_search_results']],
    )

    shared.gradio['music_play_selected_btn'].click(
        _play_selected,
        inputs=[shared.gradio['music_search_query']],
        outputs=[shared.gradio['music_search_status']],
    )

    shared.gradio['music_gen_playlist_btn'].click(
        _generate_study_playlist,
        inputs=[shared.gradio['music_mood'], shared.gradio['music_subject']],
        outputs=[shared.gradio['music_gen_status'], shared.gradio['music_gen_result']],
    )

    shared.gradio['music_ambient_play_btn'].click(
        _play_ambient,
        inputs=[shared.gradio['music_ambient_type'], shared.gradio['music_ambient_volume']],
        outputs=[shared.gradio['music_ambient_status']],
    )

    shared.gradio['music_ambient_stop_btn'].click(
        _stop_ambient,
        inputs=[],
        outputs=[shared.gradio['music_ambient_status']],
    )

    shared.gradio['music_fetch_playlists_btn'].click(
        _fetch_playlists,
        inputs=[],
        outputs=[shared.gradio['music_ambient_status'], shared.gradio['music_playlists_list']],
    )
