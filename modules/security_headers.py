"""
modules/security_headers.py — HTTP security headers middleware for Gizmo MY-AI.

Adds essential security headers to every response without breaking
Gradio WebSocket connections or inline scripts.

Note: No strict Content-Security-Policy is set because Gradio relies
on inline scripts and WebSocket connections that a strict CSP would block.
"""

from __future__ import annotations

from typing import Any, Callable

# Security headers applied to every HTTP response
_SECURITY_HEADERS = [
    ("X-Frame-Options", "SAMEORIGIN"),
    ("X-Content-Type-Options", "nosniff"),
    ("Referrer-Policy", "strict-origin-when-cross-origin"),
    (
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=(), payment=()",
    ),
]


class SecurityHeadersMiddleware:
    """
    WSGI middleware that injects security headers into every response.

    WebSocket upgrade requests are passed through unchanged so Gradio
    streaming works correctly.
    """

    def __init__(self, app: Callable) -> None:
        self.app = app

    def __call__(self, environ: dict, start_response: Callable) -> Any:
        # WebSocket upgrade — pass through without modification
        if environ.get("HTTP_UPGRADE", "").lower() == "websocket":
            return self.app(environ, start_response)

        def _inject_headers(status: str, response_headers: list, exc_info=None) -> Any:
            existing_names = {h[0].lower() for h in response_headers}
            for name, value in _SECURITY_HEADERS:
                if name.lower() not in existing_names:
                    response_headers.append((name, value))
            return start_response(status, response_headers, exc_info)

        return self.app(environ, _inject_headers)
