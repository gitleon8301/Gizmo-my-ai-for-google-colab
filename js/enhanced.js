(function () {
    'use strict';

    // ==========================================================
    //  1.  SIDEBAR TOGGLE
    // ==========================================================
    function createSidebarToggle() {
        if (document.getElementById('sidebar-toggle-btn')) return;

        const btn = document.createElement('button');
        btn.id = 'sidebar-toggle-btn';
        btn.title = 'Toggle sidebar';
        btn.innerHTML = '☰';
        btn.addEventListener('click', toggleSidebar);
        document.body.appendChild(btn);

        // Brand label at top of sidebar
        const brand = document.createElement('div');
        brand.id = 'gizmo-sidebar-brand';
        brand.innerHTML = '<span>Gizmo AI</span>';
        document.body.appendChild(brand);

        // Restore saved state
        if (localStorage.getItem('gizmo-sidebar') === 'collapsed') {
            document.body.classList.add('sidebar-collapsed');
            btn.innerHTML = '☰';
        }
    }

    function toggleSidebar() {
        const isMobile = window.innerWidth <= 768;
        const btn = document.getElementById('sidebar-toggle-btn');

        if (isMobile) {
            document.body.classList.toggle('sidebar-open');
            btn.innerHTML = document.body.classList.contains('sidebar-open') ? '✕' : '☰';
        } else {
            document.body.classList.toggle('sidebar-collapsed');
            const collapsed = document.body.classList.contains('sidebar-collapsed');
            localStorage.setItem('gizmo-sidebar', collapsed ? 'collapsed' : 'open');
            btn.innerHTML = '☰';
        }
    }

    // Close mobile sidebar on overlay click
    document.addEventListener('click', function (e) {
        if (window.innerWidth <= 768 && document.body.classList.contains('sidebar-open')) {
            const sidebar = document.querySelector('.tabs > .tab-nav');
            const btn = document.getElementById('sidebar-toggle-btn');
            if (e.target !== sidebar && !sidebar?.contains(e.target) && e.target !== btn) {
                document.body.classList.remove('sidebar-open');
                btn.innerHTML = '☰';
            }
        }
    });

    // ==========================================================
    //  2.  BUTTON RIPPLE EFFECT
    // ==========================================================
    document.addEventListener('click', function (e) {
        const button = e.target.closest('button');
        if (!button) return;

        const ripple = document.createElement('span');
        ripple.className = 'gizmo-ripple';
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
        ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
        button.style.position = button.style.position || 'relative';
        button.style.overflow = 'hidden';
        button.appendChild(ripple);

        ripple.addEventListener('animationend', function () {
            ripple.remove();
        });
    });

    // ==========================================================
    //  3.  SMOOTH ANCHOR SCROLLING
    // ==========================================================
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            var targetSelector = this.getAttribute('href');
            var target = targetSelector ? document.querySelector(targetSelector) : null;
            if (!target) return;
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth' });
        });
    });

    // ==========================================================
    //  4.  CHAT AUTO-SCROLL
    // ==========================================================
    var chatbot = document.getElementById('chatbot') || document.getElementById('chatbot-enhanced');
    if (chatbot) {
        var obs = new MutationObserver(function () {
            chatbot.scrollTop = chatbot.scrollHeight;
        });
        obs.observe(chatbot, { childList: true, subtree: true });
    }

    // ==========================================================
    //  5.  KEYBOARD SHORTCUTS
    // ==========================================================
    document.addEventListener('keydown', function (e) {
        // Ctrl+Enter to send
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            var sendBtn = document.querySelector('#Generate, #send-btn');
            if (sendBtn) sendBtn.click();
        }

        // Ctrl+K to focus search
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            var search = document.querySelector('#search_chat, #search-input');
            if (search) search.focus();
        }

        // Ctrl+B to toggle sidebar
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
            e.preventDefault();
            toggleSidebar();
        }
    });

    // ==========================================================
    //  6.  TOAST NOTIFICATIONS (improved)
    // ==========================================================
    window.showToast = function showToast(message, type) {
        type = type || 'info';
        var toast = document.createElement('div');
        var colors = {
            success: 'linear-gradient(135deg, #23c97d, #1db06c)',
            error:   'linear-gradient(135deg, #ef4444, #dc2626)',
            info:    'linear-gradient(135deg, #6c63ff, #5a52e0)',
            warning: 'linear-gradient(135deg, #f5a623, #e09310)'
        };
        toast.className = 'toast toast-' + type;
        toast.textContent = message;
        toast.style.cssText = [
            'position:fixed',
            'bottom:20px',
            'right:20px',
            'padding:12px 20px',
            'background:' + (colors[type] || colors.info),
            'color:#fff',
            'border-radius:10px',
            'box-shadow:0 8px 24px rgba(0,0,0,.25)',
            'z-index:10000',
            'font-family:Inter,sans-serif',
            'font-size:14px',
            'font-weight:500',
            'backdrop-filter:blur(8px)',
            'animation:gizmo-toastIn .35s ease-out'
        ].join(';');
        document.body.appendChild(toast);

        setTimeout(function () {
            toast.style.transition = 'opacity .3s, transform .3s';
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(8px)';
            setTimeout(function () { toast.remove(); }, 300);
        }, 3000);
    };

    // ==========================================================
    //  7.  CLIPBOARD HELPER
    // ==========================================================
    window.copyToClipboard = function copyToClipboard(text) {
        if (!navigator.clipboard) {
            window.showToast('Clipboard API unavailable', 'error');
            return;
        }
        navigator.clipboard.writeText(text)
            .then(function () { window.showToast('Copied to clipboard!', 'success'); })
            .catch(function () { window.showToast('Copy failed', 'error'); });
    };

    // ==========================================================
    //  8.  LOADING STATE HELPER
    // ==========================================================
    window.setLoading = function setLoading(element, isLoading) {
        if (!element) return;
        if (isLoading) {
            element.classList.add('generating');
            element.setAttribute('disabled', 'true');
        } else {
            element.classList.remove('generating');
            element.removeAttribute('disabled');
        }
    };

    // ==========================================================
    //  9.  CODE BLOCK COPY BUTTON
    //      Adds a "Copy" button to every <pre> block in the chat.
    //      Changes to "Copied ✓" for 2 seconds after click.
    // ==========================================================
    function addCodeCopyButtons() {
        document.querySelectorAll('pre:not([data-copy-added])').forEach(function (pre) {
            pre.setAttribute('data-copy-added', '1');
            pre.style.position = 'relative';

            var btn = document.createElement('button');
            btn.className = 'code-copy-btn';
            btn.textContent = 'Copy';
            btn.setAttribute('aria-label', 'Copy code');
            btn.addEventListener('click', function () {
                var code = pre.querySelector('code');
                var text = code ? (code.innerText || code.textContent) : (pre.innerText || pre.textContent);
                navigator.clipboard.writeText(text.trim()).then(function () {
                    btn.textContent = 'Copied ✓';
                    setTimeout(function () { btn.textContent = 'Copy'; }, 2000);
                }).catch(function () {
                    btn.textContent = 'Error';
                    setTimeout(function () { btn.textContent = 'Copy'; }, 2000);
                });
            });
            pre.appendChild(btn);
        });
    }

    // ==========================================================
    //  10. MESSAGE ACTIONS ON HOVER (Edit, Regenerate, Copy, Branch)
    // ==========================================================
    function addMessageActions() {
        document.querySelectorAll('.message:not([data-actions-added])').forEach(function (msg) {
            msg.setAttribute('data-actions-added', '1');

            var actions = document.createElement('div');
            actions.className = 'gizmo-msg-actions';
            actions.innerHTML =
                '<button title="Edit" class="gizmo-msg-action-btn">✏️</button>' +
                '<button title="Regenerate" class="gizmo-msg-action-btn">🔄</button>' +
                '<button title="Copy" class="gizmo-msg-action-btn gizmo-copy-msg">📋</button>' +
                '<button title="Branch" class="gizmo-msg-action-btn">🌿</button>';

            /* Copy action */
            var copyBtn = actions.querySelector('.gizmo-copy-msg');
            copyBtn.addEventListener('click', function () {
                var text = msg.innerText || msg.textContent || '';
                navigator.clipboard.writeText(text.trim()).then(function () {
                    copyBtn.textContent = '✅';
                    setTimeout(function () { copyBtn.textContent = '📋'; }, 2000);
                });
            });

            msg.style.position = 'relative';
            msg.appendChild(actions);
        });
    }

    // ==========================================================
    //  11. WELCOME SCREEN
    //      Shown when no conversation is loaded.
    // ==========================================================
    function maybeShowWelcome() {
        if (document.getElementById('gizmo-welcome')) return;

        var chatArea = document.querySelector('#chatbot .wrap, .chatbot .wrap, #chatbot');
        if (!chatArea) return;

        /* Only show if chat is empty */
        var messages = chatArea.querySelectorAll('.message');
        if (messages.length > 0) return;

        var MORNING_HOUR_END = 12;
        var AFTERNOON_HOUR_END = 18;
        var hour = new Date().getHours();
        var greeting = hour < MORNING_HOUR_END ? 'Good morning' : hour < AFTERNOON_HOUR_END ? 'Good afternoon' : 'Good evening';

        var emailMeta = document.querySelector('meta[name="gizmo-user-email"]');
        var name = emailMeta ? emailMeta.content.split('@')[0] : '';

        var welcome = document.createElement('div');
        welcome.id = 'gizmo-welcome';
        welcome.className = 'welcome-screen';
        welcome.innerHTML =
            '<div style="font-size:2.4rem">🤖</div>' +
            '<h1>' + greeting + (name ? ', ' + name : '') + '</h1>' +
            '<p style="color:var(--text-secondary);font-size:.95rem">What can I help you with today?</p>' +
            '<div class="prompt-cards">' +
            '<div class="prompt-card" data-prompt="Write a Python function that sorts a list of objects">💻 Help me write code</div>' +
            '<div class="prompt-card" data-prompt="Explain the concept of machine learning in simple terms">📚 Explain a concept</div>' +
            '<div class="prompt-card" data-prompt="Help me outline an essay about climate change">✍️ Help me write</div>' +
            '<div class="prompt-card" data-prompt="What are some best practices for study and learning?">🧠 Study tips</div>' +
            '</div>';

        /* Clicking a prompt card fills the chat input */
        welcome.querySelectorAll('.prompt-card').forEach(function (card) {
            card.addEventListener('click', function () {
                var prompt = card.dataset.prompt;
                var input = document.querySelector('#chat-input textarea, textarea[placeholder]');
                if (input) {
                    input.value = prompt;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.focus();
                }
                welcome.remove();
            });
        });

        chatArea.appendChild(welcome);

        /* Remove welcome when messages appear */
        var welcomeObs = new MutationObserver(function () {
            if (chatArea.querySelectorAll('.message').length > 0) {
                var w = document.getElementById('gizmo-welcome');
                if (w) w.remove();
                welcomeObs.disconnect();
            }
        });
        welcomeObs.observe(chatArea, { childList: true, subtree: true });
    }

    // ==========================================================
    //  12. MODEL PICKER MODAL
    // ==========================================================
    function createModelPickerModal() {
        if (document.getElementById('gizmo-model-picker')) return;

        var modal = document.createElement('div');
        modal.id = 'gizmo-model-picker';
        modal.className = 'model-picker-modal hidden';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        modal.setAttribute('aria-label', 'Select model');
        modal.innerHTML =
            '<div class="model-picker-inner">' +
            '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">' +
            '<h2 style="margin:0;font-size:1.1rem;color:var(--text-primary)">Select Model</h2>' +
            '<button id="gizmo-model-picker-close" aria-label="Close" style="background:transparent;border:none;cursor:pointer;color:var(--text-muted);font-size:1.3rem">✕</button>' +
            '</div>' +
            '<input id="gizmo-model-search" type="text" placeholder="Search models…" ' +
            'style="width:100%;box-sizing:border-box;padding:8px 12px;background:var(--bg-primary);' +
            'border:1px solid var(--border);border-radius:var(--radius-sm);color:var(--text-primary);' +
            'font-size:.9rem;margin-bottom:14px;outline:none">' +
            '<div id="gizmo-model-list"></div>' +
            '</div>';

        document.body.appendChild(modal);

        /* Close button */
        modal.querySelector('#gizmo-model-picker-close').addEventListener('click', closeModelPicker);

        /* Click outside */
        modal.addEventListener('click', function (e) {
            if (e.target === modal) closeModelPicker();
        });

        /* Search filter */
        modal.querySelector('#gizmo-model-search').addEventListener('input', function () {
            var query = this.value.toLowerCase();
            modal.querySelectorAll('.model-card').forEach(function (card) {
                var label = (card.dataset.name || '').toLowerCase();
                card.style.display = label.includes(query) ? '' : 'none';
            });
        });
    }

    function openModelPicker() {
        var modal = document.getElementById('gizmo-model-picker');
        if (!modal) {
            createModelPickerModal();
            modal = document.getElementById('gizmo-model-picker');
        }
        populateModelList();
        modal.classList.remove('hidden');
        var search = modal.querySelector('#gizmo-model-search');
        if (search) { search.value = ''; search.focus(); }
    }

    function closeModelPicker() {
        var modal = document.getElementById('gizmo-model-picker');
        if (modal) modal.classList.add('hidden');
    }

    function populateModelList() {
        var list = document.getElementById('gizmo-model-list');
        if (!list) return;
        list.innerHTML = '';

        /* Try to read available models from Gradio dropdown */
        var modelDropdown = document.querySelector('#model_menu select, select[data-testid*="model"]');
        var options = modelDropdown ? Array.from(modelDropdown.options) : [];

        if (options.length === 0) {
            list.innerHTML = '<p style="color:var(--text-muted);font-size:.9rem;text-align:center">No models found. Load models via the Models tab.</p>';
            return;
        }

        options.forEach(function (opt) {
            var card = document.createElement('div');
            card.className = 'model-card';
            card.dataset.name = opt.text;
            card.innerHTML =
                '<div style="flex:1">' +
                '<div style="font-weight:600;color:var(--text-primary);font-size:.92rem">' + opt.text + '</div>' +
                '</div>' +
                '<span class="model-badge downloaded">Loaded</span>';
            card.addEventListener('click', function () {
                if (modelDropdown) {
                    modelDropdown.value = opt.value;
                    modelDropdown.dispatchEvent(new Event('change', { bubbles: true }));
                }
                closeModelPicker();
            });
            list.appendChild(card);
        });
    }

    /* Wire top-bar model name click to open picker */
    function setupModelPickerTrigger() {
        var trigger = document.querySelector('#gizmo-model-name, .topbar-model-name');
        if (trigger) {
            trigger.style.cursor = 'pointer';
            trigger.addEventListener('click', openModelPicker);
        }
    }

    /* Expose globally */
    window.gizmoOpenModelPicker = openModelPicker;

    // ==========================================================
    //  13. INIT ON DOM READY
    // ==========================================================
    function init() {
        createSidebarToggle();
        createModelPickerModal();
        setupModelPickerTrigger();
        maybeShowWelcome();
        addCodeCopyButtons();
        addMessageActions();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Also re-init after Gradio fully loads (it can replace DOM)
    var gradioReadyInterval = setInterval(function () {
        var tabs = document.querySelector('.tabs > .tab-nav');
        if (tabs) {
            clearInterval(gradioReadyInterval);
            createSidebarToggle();
            addCodeCopyButtons();
            addMessageActions();
            maybeShowWelcome();
            setupModelPickerTrigger();
        }
    }, 500);

    // Clear interval after 15s max
    setTimeout(function () { clearInterval(gradioReadyInterval); }, 15000);

    // Re-scan for new code blocks and messages using MutationObserver
    var domObserver = new MutationObserver(function () {
        addCodeCopyButtons();
        addMessageActions();
    });
    domObserver.observe(document.body, { childList: true, subtree: true });
})();
