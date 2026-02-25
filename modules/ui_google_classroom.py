"""Gradio UI tab for the Google Classroom integration feature."""

from __future__ import annotations

import gradio as gr

from modules import shared

TUTORIAL_URL = (
    "https://github.com/leonlazdev-wq/Gizmo-my-ai-for-google-colab"
    "/blob/main/README.md#google-classroom-setup"
)


def _authorize(creds_path: str):
    if not creds_path:
        return "<div style='color:#f44336'>No credentials file provided.</div>"
    try:
        from modules.google_classroom_integration import authorize  # type: ignore
        success, msg = authorize(creds_path)
        color = "#4CAF50" if success else "#f44336"
        return f"<div style='color:{color};font-weight:600'>{msg}</div>"
    except Exception as exc:
        return f"<div style='color:#f44336'>Error: {exc}</div>"


def _reconnect():
    try:
        from modules.google_classroom_integration import connect_from_saved  # type: ignore
        success, msg = connect_from_saved()
        color = "#4CAF50" if success else "#f44336"
        return f"<div style='color:{color};font-weight:600'>{msg}</div>"
    except Exception as exc:
        return f"<div style='color:#f44336'>Error: {exc}</div>"


def _connect_ai():
    try:
        from modules.google_classroom_integration import is_connected  # type: ignore
        if is_connected():
            return "<div style='color:#4CAF50;font-weight:600'>✅ Google Classroom connected to AI</div>"
        return "<div style='color:#f44336'>Not connected. Authorize first.</div>"
    except Exception:
        return "<div style='color:#f44336'>Google Classroom not connected to AI.</div>"


def _fetch_courses():
    try:
        from modules.google_classroom_integration import list_courses  # type: ignore
        courses, msg = list_courses()
        choices = [f"{c['name']} ({c['id']})" for c in courses]
        return msg, gr.update(choices=choices, value=choices[0] if choices else None)
    except Exception as exc:
        return f"Error: {exc}", gr.update(choices=[])


def _fetch_assignments(course: str, status_filter: str):
    if not course:
        return "Please select a course.", []
    try:
        from modules.google_classroom_integration import list_assignments  # type: ignore
        course_id = _parse_id(course)
        assignments, msg = list_assignments(course_id, status_filter)
        rows = [
            [a["title"], a["course"], a["due_date"], a["status"], a.get("grade", "")]
            for a in assignments
        ]
        return msg, rows
    except Exception as exc:
        return f"Error: {exc}", []


def _sync_to_calendar(course: str):
    if not course:
        return "Please select a course."
    try:
        from modules.google_classroom_integration import sync_assignments_to_calendar  # type: ignore
        course_id = _parse_id(course)
        _, msg = sync_assignments_to_calendar(course_id)
        return msg
    except Exception as exc:
        return f"Error: {exc}"


def _sync_to_tracker(course: str):
    if not course:
        return "Please select a course."
    try:
        from modules.google_classroom_integration import sync_assignments_to_tracker  # type: ignore
        course_id = _parse_id(course)
        _, msg = sync_assignments_to_tracker(course_id)
        return msg
    except Exception as exc:
        return f"Error: {exc}"


def _make_flashcards(course: str):
    if not course:
        return "Please select a course.", ""
    try:
        from modules.google_classroom_integration import get_assignment_content  # type: ignore
        course_id = _parse_id(course)
        content, _ = get_assignment_content(course_id)
        if not content:
            return "No assignment content available.", ""
        from modules.text_generation import generate_reply as _gen  # type: ignore
        prompt = f"Create 10 flashcards (Q&A format) from the following assignment content:\n\n{content}"
        full = ""
        for chunk in _gen(prompt, state={}, stopping_strings=[]):
            if isinstance(chunk, str):
                full = chunk
        return "✅ Flashcards generated.", full
    except Exception as exc:
        return f"Error: {exc}", ""


def _make_quiz(course: str):
    if not course:
        return "Please select a course.", ""
    try:
        from modules.google_classroom_integration import get_assignment_content  # type: ignore
        course_id = _parse_id(course)
        content, _ = get_assignment_content(course_id)
        if not content:
            return "No assignment content available.", ""
        from modules.text_generation import generate_reply as _gen  # type: ignore
        prompt = f"Create a 5-question multiple choice quiz from the following content:\n\n{content}"
        full = ""
        for chunk in _gen(prompt, state={}, stopping_strings=[]):
            if isinstance(chunk, str):
                full = chunk
        return "✅ Quiz generated.", full
    except Exception as exc:
        return f"Error: {exc}", ""


def _make_notes(course: str):
    if not course:
        return "Please select a course.", ""
    try:
        from modules.google_classroom_integration import get_assignment_content  # type: ignore
        course_id = _parse_id(course)
        content, _ = get_assignment_content(course_id)
        if not content:
            return "No assignment content available.", ""
        from modules.text_generation import generate_reply as _gen  # type: ignore
        prompt = f"Create detailed study notes from the following content:\n\n{content}"
        full = ""
        for chunk in _gen(prompt, state={}, stopping_strings=[]):
            if isinstance(chunk, str):
                full = chunk
        return "✅ Study notes generated.", full
    except Exception as exc:
        return f"Error: {exc}", ""


def _fetch_announcements(course: str):
    if not course:
        return "Please select a course.", []
    try:
        from modules.google_classroom_integration import list_announcements  # type: ignore
        course_id = _parse_id(course)
        items, msg = list_announcements(course_id)
        rows = [[a["course"], a["author"], a["date"], a["preview"]] for a in items]
        return msg, rows
    except Exception as exc:
        return f"Error: {exc}", []


def _summarize_announcement(course: str):
    if not course:
        return "Please select a course.", ""
    try:
        from modules.google_classroom_integration import get_latest_announcement  # type: ignore
        course_id = _parse_id(course)
        content, _ = get_latest_announcement(course_id)
        if not content:
            return "No announcement content available.", ""
        from modules.text_generation import generate_reply as _gen  # type: ignore
        prompt = f"Summarize the following classroom announcement:\n\n{content}"
        full = ""
        for chunk in _gen(prompt, state={}, stopping_strings=[]):
            if isinstance(chunk, str):
                full = chunk
        return "✅ Summary ready.", full
    except Exception as exc:
        return f"Error: {exc}", ""


def _fetch_materials(course: str):
    if not course:
        return "Please select a course.", []
    try:
        from modules.google_classroom_integration import list_materials  # type: ignore
        course_id = _parse_id(course)
        items, msg = list_materials(course_id)
        rows = [[m["title"], m["type"], m["posted_date"], m["description"]] for m in items]
        return msg, rows
    except Exception as exc:
        return f"Error: {exc}", []


def _open_material(material_title: str):
    if not material_title:
        return "No material selected.", ""
    try:
        from modules.google_classroom_integration import fetch_material_content  # type: ignore
        content, msg = fetch_material_content(material_title)
        return msg, content or ""
    except Exception as exc:
        return f"Error: {exc}", ""


def _study_material(material_title: str):
    if not material_title:
        return "No material selected.", ""
    try:
        from modules.google_classroom_integration import fetch_material_content  # type: ignore
        content, _ = fetch_material_content(material_title)
        if not content:
            return "No content available.", ""
        from modules.text_generation import generate_reply as _gen  # type: ignore
        prompt = (
            f"I'm studying the following classroom material. "
            f"Provide key points, definitions, and study tips:\n\n{content}"
        )
        full = ""
        for chunk in _gen(prompt, state={}, stopping_strings=[]):
            if isinstance(chunk, str):
                full = chunk
        return "✅ Study guide ready.", full
    except Exception as exc:
        return f"Error: {exc}", ""


def _fetch_grades(course: str):
    if not course:
        return "Please select a course.", [], ""
    try:
        from modules.google_classroom_integration import list_grades  # type: ignore
        course_id = _parse_id(course)
        grades, msg = list_grades(course_id)
        rows = [
            [g["course"], g["assignment"], g["grade"], g["max_points"], g["percentage"]]
            for g in grades
        ]
        if grades:
            avg = sum(
                float(g["percentage"].rstrip("%")) for g in grades if g["percentage"]
            ) / len(grades)
            gpa_html = (
                f"<div style='padding:10px'>"
                f"📊 <b>Course Average:</b> <span style='color:#4CAF50'>{avg:.1f}%</span></div>"
            )
        else:
            gpa_html = "<div style='color:#888;padding:10px'>No grade data available.</div>"
        return msg, rows, gpa_html
    except Exception as exc:
        return f"Error: {exc}", [], ""


def _parse_id(selector: str) -> str:
    """Extract an ID from 'Name (id)' formatted string."""
    if not selector:
        return ""
    if "(" in selector and selector.endswith(")"):
        return selector.rsplit("(", 1)[-1].rstrip(")")
    return selector


def create_ui():
    with gr.Tab("🎓 Google Classroom", elem_id="google-classroom-tab"):
        gr.HTML(
            f"<div style='margin-bottom:8px'>"
            f"<a href='{TUTORIAL_URL}' target='_blank' rel='noopener noreferrer' "
            f"style='font-size:.88em;color:#8ec8ff'>📖 Tutorial: How to set up Google Classroom integration</a>"
            f"</div>"
        )

        with gr.Accordion("🔌 Connection", open=True):
            with gr.Row():
                shared.gradio['gclass_creds_path'] = gr.Textbox(
                    label="Path to credentials.json",
                    placeholder="/path/to/credentials.json",
                    scale=4,
                )
                shared.gradio['gclass_authorize_btn'] = gr.Button(
                    "🔗 Authorize", variant="primary", scale=1
                )
            shared.gradio['gclass_reconnect_btn'] = gr.Button(
                "Reconnect (use saved token)", size="sm"
            )
            shared.gradio['gclass_status'] = gr.HTML(
                "<div style='color:#888'>Not connected</div>"
            )
            shared.gradio['gclass_connect_ai_btn'] = gr.Button("🤖 Connect to AI")

        gr.Markdown("---")
        gr.Markdown("### 📚 Course Selector")
        with gr.Row():
            shared.gradio['gclass_fetch_courses_btn'] = gr.Button("🔄 Fetch Courses")
            shared.gradio['gclass_course_selector'] = gr.Dropdown(
                label="Select Course", choices=[], allow_custom_value=True, scale=3
            )
        shared.gradio['gclass_fetch_courses_status'] = gr.Textbox(
            label="Status", interactive=False
        )

        gr.Markdown("---")

        with gr.Tabs():
            with gr.Tab("📋 Assignments"):
                shared.gradio['gclass_fetch_assignments_btn'] = gr.Button(
                    "🔄 Fetch Assignments"
                )
                with gr.Row():
                    shared.gradio['gclass_status_filter'] = gr.Dropdown(
                        choices=["All", "Assigned", "Turned In", "Graded"],
                        value="All",
                        allow_custom_value=True,
                        label="Status Filter",
                        scale=2,
                    )
                shared.gradio['gclass_assignments_table'] = gr.Dataframe(
                    headers=["Title", "Class", "Due Date", "Status", "Grade"],
                    label="Assignments",
                    interactive=False,
                )
                with gr.Row():
                    shared.gradio['gclass_sync_calendar_btn'] = gr.Button("📅 Sync to Calendar")
                    shared.gradio['gclass_sync_tracker_btn'] = gr.Button(
                        "📋 Sync to Assignments"
                    )
                with gr.Row():
                    shared.gradio['gclass_make_flashcards_btn'] = gr.Button("🃏 Make Flashcards")
                    shared.gradio['gclass_make_quiz_btn'] = gr.Button("📝 Make Quiz")
                    shared.gradio['gclass_make_notes_btn'] = gr.Button("📚 Make Notes")
                shared.gradio['gclass_assignment_status'] = gr.Textbox(
                    label="Status", interactive=False
                )
                shared.gradio['gclass_assignment_ai_output'] = gr.Textbox(
                    label="AI Output", lines=8, interactive=False
                )

            with gr.Tab("📢 Announcements"):
                shared.gradio['gclass_fetch_announcements_btn'] = gr.Button(
                    "🔄 Fetch Announcements"
                )
                shared.gradio['gclass_announcements_table'] = gr.Dataframe(
                    headers=["Course", "Author", "Date", "Preview"],
                    label="Announcements",
                    interactive=False,
                )
                shared.gradio['gclass_summarize_announcement_btn'] = gr.Button("📋 Summarize")
                shared.gradio['gclass_announcement_status'] = gr.Textbox(
                    label="Status", interactive=False
                )
                shared.gradio['gclass_announcement_content'] = gr.Textbox(
                    label="Announcement Content", lines=6, interactive=False
                )

            with gr.Tab("📁 Materials"):
                shared.gradio['gclass_fetch_materials_btn'] = gr.Button("🔄 Fetch Materials")
                shared.gradio['gclass_materials_table'] = gr.Dataframe(
                    headers=["Title", "Type", "Posted Date", "Description"],
                    label="Materials",
                    interactive=False,
                )
                with gr.Row():
                    shared.gradio['gclass_open_material_btn'] = gr.Button("📂 Open in Gizmo")
                    shared.gradio['gclass_study_material_btn'] = gr.Button(
                        "📚 Study This Material"
                    )
                shared.gradio['gclass_materials_status'] = gr.Textbox(
                    label="Status", interactive=False
                )
                shared.gradio['gclass_materials_content'] = gr.Textbox(
                    label="Material Content", lines=6, interactive=False
                )

            with gr.Tab("📊 Grades"):
                shared.gradio['gclass_fetch_grades_btn'] = gr.Button("🔄 Fetch Grades")
                shared.gradio['gclass_grades_table'] = gr.Dataframe(
                    headers=["Course", "Assignment", "Grade", "Max Points", "Percentage"],
                    label="Grades",
                    interactive=False,
                )
                shared.gradio['gclass_grades_status'] = gr.Textbox(
                    label="Status", interactive=False
                )
                shared.gradio['gclass_gpa_html'] = gr.HTML(
                    "<div style='color:#888;padding:10px'>Fetch grades to see your average.</div>"
                )


def create_event_handlers():
    shared.gradio['gclass_authorize_btn'].click(
        _authorize,
        inputs=[shared.gradio['gclass_creds_path']],
        outputs=[shared.gradio['gclass_status']],
    )

    shared.gradio['gclass_reconnect_btn'].click(
        _reconnect,
        inputs=[],
        outputs=[shared.gradio['gclass_status']],
    )

    shared.gradio['gclass_connect_ai_btn'].click(
        _connect_ai,
        inputs=[],
        outputs=[shared.gradio['gclass_status']],
    )

    shared.gradio['gclass_fetch_courses_btn'].click(
        _fetch_courses,
        inputs=[],
        outputs=[
            shared.gradio['gclass_fetch_courses_status'],
            shared.gradio['gclass_course_selector'],
        ],
    )

    shared.gradio['gclass_fetch_assignments_btn'].click(
        _fetch_assignments,
        inputs=[
            shared.gradio['gclass_course_selector'],
            shared.gradio['gclass_status_filter'],
        ],
        outputs=[
            shared.gradio['gclass_assignment_status'],
            shared.gradio['gclass_assignments_table'],
        ],
    )

    shared.gradio['gclass_sync_calendar_btn'].click(
        _sync_to_calendar,
        inputs=[shared.gradio['gclass_course_selector']],
        outputs=[shared.gradio['gclass_assignment_status']],
    )

    shared.gradio['gclass_sync_tracker_btn'].click(
        _sync_to_tracker,
        inputs=[shared.gradio['gclass_course_selector']],
        outputs=[shared.gradio['gclass_assignment_status']],
    )

    shared.gradio['gclass_make_flashcards_btn'].click(
        _make_flashcards,
        inputs=[shared.gradio['gclass_course_selector']],
        outputs=[
            shared.gradio['gclass_assignment_status'],
            shared.gradio['gclass_assignment_ai_output'],
        ],
        show_progress=True,
    )

    shared.gradio['gclass_make_quiz_btn'].click(
        _make_quiz,
        inputs=[shared.gradio['gclass_course_selector']],
        outputs=[
            shared.gradio['gclass_assignment_status'],
            shared.gradio['gclass_assignment_ai_output'],
        ],
        show_progress=True,
    )

    shared.gradio['gclass_make_notes_btn'].click(
        _make_notes,
        inputs=[shared.gradio['gclass_course_selector']],
        outputs=[
            shared.gradio['gclass_assignment_status'],
            shared.gradio['gclass_assignment_ai_output'],
        ],
        show_progress=True,
    )

    shared.gradio['gclass_fetch_announcements_btn'].click(
        _fetch_announcements,
        inputs=[shared.gradio['gclass_course_selector']],
        outputs=[
            shared.gradio['gclass_announcement_status'],
            shared.gradio['gclass_announcements_table'],
        ],
    )

    shared.gradio['gclass_summarize_announcement_btn'].click(
        _summarize_announcement,
        inputs=[shared.gradio['gclass_course_selector']],
        outputs=[
            shared.gradio['gclass_announcement_status'],
            shared.gradio['gclass_announcement_content'],
        ],
        show_progress=True,
    )

    shared.gradio['gclass_fetch_materials_btn'].click(
        _fetch_materials,
        inputs=[shared.gradio['gclass_course_selector']],
        outputs=[
            shared.gradio['gclass_materials_status'],
            shared.gradio['gclass_materials_table'],
        ],
    )

    shared.gradio['gclass_open_material_btn'].click(
        _open_material,
        inputs=[shared.gradio['gclass_materials_status']],
        outputs=[
            shared.gradio['gclass_materials_status'],
            shared.gradio['gclass_materials_content'],
        ],
    )

    shared.gradio['gclass_study_material_btn'].click(
        _study_material,
        inputs=[shared.gradio['gclass_materials_status']],
        outputs=[
            shared.gradio['gclass_materials_status'],
            shared.gradio['gclass_materials_content'],
        ],
        show_progress=True,
    )

    shared.gradio['gclass_fetch_grades_btn'].click(
        _fetch_grades,
        inputs=[shared.gradio['gclass_course_selector']],
        outputs=[
            shared.gradio['gclass_grades_status'],
            shared.gradio['gclass_grades_table'],
            shared.gradio['gclass_gpa_html'],
        ],
    )
