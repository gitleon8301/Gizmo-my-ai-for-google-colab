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
            // If click is on the overlay (::after pseudo-element area, approximated by checking target)
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
    //  9.  INIT ON DOM READY
    // ==========================================================
    function init() {
        createSidebarToggle();
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
        }
    }, 500);

    // Clear interval after 15s max
    setTimeout(function () { clearInterval(gradioReadyInterval); }, 15000);
})();
