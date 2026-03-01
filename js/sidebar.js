/* ============================================================
   Gizmo MY-AI — Sidebar Navigation  (vanilla JS, no frameworks)
   js/sidebar.js
   ============================================================ */

(function () {
  'use strict';

  /* ── Section definitions ──────────────────────────────────── */
  const NAV_SECTIONS = [
    {
      label: 'Main',
      items: [
        { icon: '💬', label: 'Chat',        tab: 'chat' },
        { icon: '📝', label: 'Notebook',    tab: 'notebook' },
        { icon: '🤖', label: 'Models',      tab: 'model' },
      ],
    },
    {
      label: 'Learning',
      items: [
        { icon: '🎓', label: 'Training',    tab: 'training' },
        { icon: '🔌', label: 'Connectors',  tab: 'connectors' },
        { icon: '📚', label: 'Learning',    tab: 'learning' },
        { icon: '🛠', label: 'Tools',       tab: 'tools' },
      ],
    },
    {
      label: 'Insights',
      items: [
        { icon: '📊', label: 'Analytics',   tab: 'analytics' },
        { icon: '⚙️', label: 'Settings',    tab: 'session' },
      ],
    },
  ];

  /* ── Build sidebar HTML ───────────────────────────────────── */
  function buildSidebar() {
    const sidebar = document.getElementById('gizmo-sidebar');
    if (!sidebar) return;

    /* Logo */
    const logo = document.createElement('div');
    logo.className = 'sidebar-logo';
    logo.innerHTML = '🤖 <span>Gizmo MY&#8209;AI</span>';
    sidebar.appendChild(logo);

    /* Nav */
    const nav = document.createElement('nav');
    nav.className = 'sidebar-nav';
    nav.setAttribute('aria-label', 'Main navigation');

    NAV_SECTIONS.forEach(function (section) {
      const label = document.createElement('div');
      label.className = 'sidebar-section-label';
      label.textContent = section.label;
      nav.appendChild(label);

      section.items.forEach(function (item) {
        const a = document.createElement('a');
        a.href = '#';
        a.dataset.tab = item.tab;
        a.innerHTML = '<span aria-hidden="true">' + item.icon + '</span>' +
                      '<span>' + item.label + '</span>';
        a.addEventListener('click', function (e) {
          e.preventDefault();
          setActiveTab(item.tab);
          switchGradioTab(item.tab);
          if (window.innerWidth < 768) closeSidebar();
        });
        nav.appendChild(a);
      });
    });

    sidebar.appendChild(nav);

    /* Footer (profile) */
    const footer = document.createElement('div');
    footer.className = 'sidebar-footer';
    footer.id = 'sidebar-footer';
    footer.innerHTML =
      '<img class="sidebar-avatar" src="" alt="avatar" id="sidebar-avatar">' +
      '<span class="sidebar-user-email" id="sidebar-email">—</span>' +
      '<a href="/logout" class="sidebar-logout" title="Sign out">↩</a>';
    sidebar.appendChild(footer);

    /* Populate profile from meta tag if present */
    populateProfile();
  }

  /* ── Active tab ───────────────────────────────────────────── */
  function setActiveTab(tabName) {
    document.querySelectorAll('#gizmo-sidebar .sidebar-nav a').forEach(function (a) {
      a.classList.toggle('active', a.dataset.tab === tabName);
    });
    sessionStorage.setItem('gizmo-active-tab', tabName);
  }

  /* ── Switch the underlying Gradio tab ────────────────────── */
  function switchGradioTab(tabName) {
    /* Gradio renders tab buttons as elements with data-testid or role=tab */
    const allTabBtns = document.querySelectorAll('[role="tab"]');
    const target = tabName.toLowerCase();
    for (let i = 0; i < allTabBtns.length; i++) {
      const btn = allTabBtns[i];
      const text = (btn.textContent || '').toLowerCase().trim();
      if (text.includes(target)) {
        btn.click();
        return;
      }
    }
  }

  /* ── Sidebar open / close ─────────────────────────────────── */
  function openSidebar() {
    const s = document.getElementById('gizmo-sidebar');
    if (s) {
      s.classList.remove('collapsed');
      s.classList.add('open');
    }
  }

  function closeSidebar() {
    const s = document.getElementById('gizmo-sidebar');
    if (s) {
      s.classList.remove('open');
      if (window.innerWidth < 768) s.classList.add('collapsed');
    }
  }

  function toggleSidebar() {
    const s = document.getElementById('gizmo-sidebar');
    if (!s) return;
    if (s.classList.contains('collapsed') || !s.classList.contains('open')) {
      openSidebar();
    } else {
      closeSidebar();
    }
  }

  /* ── Hamburger button ─────────────────────────────────────── */
  function setupHamburger() {
    const btn = document.querySelector('.topbar-hamburger');
    if (btn) btn.addEventListener('click', toggleSidebar);
  }

  /* ── User profile ─────────────────────────────────────────── */
  function populateProfile() {
    /* Server can inject <meta name="gizmo-user-email" content="...">
       and <meta name="gizmo-user-avatar" content="url"> */
    const emailMeta  = document.querySelector('meta[name="gizmo-user-email"]');
    const avatarMeta = document.querySelector('meta[name="gizmo-user-avatar"]');

    const emailEl  = document.getElementById('sidebar-email');
    const avatarEl = document.getElementById('sidebar-avatar');

    if (emailMeta  && emailEl)  emailEl.textContent = emailMeta.content;
    if (avatarMeta && avatarEl) avatarEl.src = avatarMeta.content;
  }

  /* ── Restore active tab on load ───────────────────────────── */
  function restoreActiveTab() {
    const saved = sessionStorage.getItem('gizmo-active-tab');
    if (saved) setActiveTab(saved);
    else setActiveTab('chat');
  }

  /* ── Init ─────────────────────────────────────────────────── */
  function init() {
    buildSidebar();
    setupHamburger();
    restoreActiveTab();

    /* Collapse on mobile by default */
    if (window.innerWidth < 768) closeSidebar();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
