"""
ui_theme_toggle.py — Dark/Light theme toggle component.

Renders a fixed-position pill button (top-right) that toggles the `dark` class on
`document.body`, keeps syntax highlight theme in sync, and persists user choice.
"""

THEME_TOGGLE_HTML = """
<style>
#theme-toggle-btn {
    position: fixed;
    top: 12px;
    right: 16px;
    z-index: 9999;
    font-size: 16px;
    background: var(--g-glass-bg, rgba(28,28,40,.78));
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--g-border, #2a2a3d);
    border-radius: 999px;
    width: 42px;
    height: 42px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all .25s cubic-bezier(.4,0,.2,1);
    box-shadow: 0 2px 8px rgba(0,0,0,.15);
}
#theme-toggle-btn:hover {
    transform: scale(1.08);
    border-color: var(--g-accent, #6c63ff);
    box-shadow: 0 4px 14px rgba(108,99,255,.25);
}
#theme-toggle-btn .icon {
    display: inline-block;
    transition: transform .4s cubic-bezier(.4,0,.2,1);
}
#theme-toggle-btn:hover .icon {
    transform: rotate(25deg);
}
</style>
<button id="theme-toggle-btn" onclick="window.gizmoToggleTheme && window.gizmoToggleTheme()" title="Toggle dark/light theme"><span class="icon">🌙</span></button>
<script>
(function () {
    function setHighlightByTheme(isDark) {
        var currentCSS = document.getElementById('highlight-css');
        if (currentCSS) {
            currentCSS.setAttribute('href', isDark
                ? 'file/css/highlightjs/github-dark.min.css'
                : 'file/css/highlightjs/github.min.css');
        }
    }

    function syncThemeStateInput(mode) {
        var input = document.querySelector('#theme_state textarea, #theme_state input');
        if (!input) return;
        input.value = mode;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
    }

    function updateButtonIcon() {
        var btn = document.getElementById('theme-toggle-btn');
        if (!btn) return;
        var icon = btn.querySelector('.icon');
        if (!icon) return;
        icon.textContent = document.body.classList.contains('dark') ? '☀️' : '🌙';
    }

    window.gizmoToggleTheme = function () {
        // Use existing global helper if available.
        if (typeof toggleDarkMode === 'function') {
            toggleDarkMode();
        } else {
            document.body.classList.toggle('dark');
        }

        var isDark = document.body.classList.contains('dark');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        setHighlightByTheme(isDark);
        syncThemeStateInput(isDark ? 'dark' : 'light');
        updateButtonIcon();
    };

    // Initial sync on load — default to dark mode.
    var saved = localStorage.getItem('theme');
    if (saved === 'light') {
        document.body.classList.remove('dark');
    } else {
        document.body.classList.add('dark');
        localStorage.setItem('theme', 'dark');
    }

    setHighlightByTheme(document.body.classList.contains('dark'));
    updateButtonIcon();
})();
</script>
"""


def get_html() -> str:
    """Return the HTML snippet for the theme toggle button."""
    return THEME_TOGGLE_HTML
