/* ============================================================
   Gizmo MY-AI — Keyboard Shortcuts  (vanilla JS, no frameworks)
   js/shortcuts.js

   Shortcuts:
     Ctrl+K          → Open search
     Ctrl+N          → New chat
     Ctrl+Shift+C    → Copy last AI message
     Ctrl+Enter      → Send message
     [               → Toggle sidebar
     Escape          → Close any open modal
     Ctrl+/          → Show keyboard shortcut help
   ============================================================ */

(function () {
  'use strict';

  /* ── Helpers ──────────────────────────────────────────────── */
  function isInputFocused() {
    const el = document.activeElement;
    if (!el) return false;
    return el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable;
  }

  function closeOpenModals() {
    document.querySelectorAll('.gizmo-modal.open, [id$="-modal"].open').forEach(function (m) {
      m.classList.remove('open');
    });
    const helpModal = document.getElementById('gizmo-shortcuts-help');
    if (helpModal) helpModal.style.display = 'none';
  }

  function triggerSearch() {
    /* Try to focus the search input if present */
    const searchInput = document.querySelector('#gizmo-search-input, input[placeholder*="search" i]');
    if (searchInput) {
      searchInput.focus();
      searchInput.select();
    }
  }

  function newChat() {
    /* Click the "New Chat" button if it exists, otherwise dispatch a custom event */
    const btn = document.querySelector('#new-chat-btn, button[aria-label*="new chat" i]');
    if (btn) {
      btn.click();
    } else {
      document.dispatchEvent(new CustomEvent('gizmo:new-chat'));
    }
  }

  function copyLastAIMessage() {
    const bubbles = document.querySelectorAll('.gizmo-ai-bubble');
    if (!bubbles.length) return;
    const last = bubbles[bubbles.length - 1];
    const text = last.innerText || last.textContent || '';
    navigator.clipboard.writeText(text.trim()).then(function () {
      showToast('✅ Copied last AI message');
    }).catch(function () {
      showToast('❌ Copy failed');
    });
  }

  function sendMessage() {
    /* Find the active send button */
    const btn = document.querySelector('.gizmo-send-btn, #generate, button[title="Send"]');
    if (btn) btn.click();
  }

  function toggleSidebar() {
    /* Reuse sidebar.js function if available */
    if (typeof window.gizmoToggleSidebar === 'function') {
      window.gizmoToggleSidebar();
    } else {
      const s = document.getElementById('gizmo-sidebar');
      if (s) s.classList.toggle('collapsed');
    }
  }

  /* ── Toast notification ───────────────────────────────────── */
  function showToast(msg, duration) {
    duration = duration || 2000;
    let toast = document.getElementById('gizmo-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'gizmo-toast';
      Object.assign(toast.style, {
        position: 'fixed', bottom: '80px', left: '50%',
        transform: 'translateX(-50%)',
        background: '#1a1d23', color: '#e6e8ec',
        border: '1px solid #2a2d35', borderRadius: '10px',
        padding: '8px 20px', fontSize: '.88rem',
        zIndex: '9999', pointerEvents: 'none',
        transition: 'opacity .2s ease',
      });
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.style.opacity = '1';
    clearTimeout(toast._timer);
    toast._timer = setTimeout(function () {
      toast.style.opacity = '0';
    }, duration);
  }

  /* ── Shortcut help overlay ────────────────────────────────── */
  function showShortcutsHelp() {
    let modal = document.getElementById('gizmo-shortcuts-help');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'gizmo-shortcuts-help';
      Object.assign(modal.style, {
        display: 'none', position: 'fixed', inset: '0',
        background: 'rgba(0,0,0,.75)',
        zIndex: '10000', alignItems: 'center', justifyContent: 'center',
      });
      modal.innerHTML = [
        '<div style="background:#111318;border:1px solid #2a2d35;border-radius:14px;',
        'padding:28px 32px;max-width:480px;width:100%;color:#e6e8ec;font-family:sans-serif">',
        '<h3 style="margin:0 0 16px;color:#6C63FF">⌨ Keyboard Shortcuts</h3>',
        '<table style="width:100%;border-collapse:collapse;font-size:.9rem">',
        rows([
          ['Ctrl+K',       'Open search'],
          ['Ctrl+N',       'New chat'],
          ['Ctrl+Shift+C', 'Copy last AI message'],
          ['Ctrl+Enter',   'Send message'],
          ['[',            'Toggle sidebar'],
          ['Escape',       'Close modal'],
          ['Ctrl+/',       'Show this help'],
        ]),
        '</table>',
        '<button onclick="this.closest(\'#gizmo-shortcuts-help\').style.display=\'none\'" ',
        'style="margin-top:18px;background:#6C63FF;border:none;color:#fff;',
        'padding:8px 20px;border-radius:8px;cursor:pointer;font-size:.88rem">Close</button>',
        '</div>',
      ].join('');
      document.body.appendChild(modal);
    }
    modal.style.display = 'flex';

    function rows(pairs) {
      return pairs.map(function (p) {
        return '<tr><td style="padding:5px 12px 5px 0;color:#9ca3af"><kbd style="' +
          'background:#1a1d23;border:1px solid #2a2d35;border-radius:5px;' +
          'padding:2px 7px;font-family:monospace">' + p[0] + '</kbd></td>' +
          '<td style="padding:5px 0">' + p[1] + '</td></tr>';
      }).join('');
    }
  }

  /* ── Key event handler ────────────────────────────────────── */
  document.addEventListener('keydown', function (e) {
    const ctrl  = e.ctrlKey || e.metaKey;
    const shift = e.shiftKey;
    const key   = e.key;

    /* Ctrl+K — search */
    if (ctrl && !shift && key === 'k') {
      e.preventDefault();
      triggerSearch();
      return;
    }

    /* Ctrl+N — new chat */
    if (ctrl && !shift && key === 'n') {
      e.preventDefault();
      newChat();
      return;
    }

    /* Ctrl+Shift+C — copy last AI message */
    if (ctrl && shift && key === 'C') {
      e.preventDefault();
      copyLastAIMessage();
      return;
    }

    /* Ctrl+Enter — send (only when textarea is focused) */
    if (ctrl && key === 'Enter') {
      sendMessage();
      return;
    }

    /* Ctrl+/ — shortcuts help */
    if (ctrl && key === '/') {
      e.preventDefault();
      showShortcutsHelp();
      return;
    }

    /* Escape — close modals */
    if (key === 'Escape') {
      closeOpenModals();
      return;
    }

    /* [ — toggle sidebar (only when not typing) */
    if (key === '[' && !isInputFocused()) {
      e.preventDefault();
      toggleSidebar();
      return;
    }
  });

  /* ── Expose toggle sidebar globally for sidebar.js ───────── */
  window.gizmoToggleSidebar = function () {
    const s = document.getElementById('gizmo-sidebar');
    if (!s) return;
    if (s.classList.contains('collapsed') || !s.classList.contains('open')) {
      s.classList.remove('collapsed');
      s.classList.add('open');
    } else {
      s.classList.remove('open');
      s.classList.add('collapsed');
    }
  };
})();
