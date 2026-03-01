/* ============================================================
   Gizmo MY-AI — Sidebar Navigation  (vanilla JS, no frameworks)
   js/sidebar.js
   ============================================================ */

(function () {
  'use strict';

  /* ── Section definitions (accordion style) ────────────────── */
  var NAV_SECTIONS = [
    {
      id: 'chat',
      icon: '💬',
      label: 'Chat',
      items: [
        { icon: '💬', label: 'Chat',        tab: 'chat' },
      ],
    },
    {
      id: 'notebook',
      icon: '📓',
      label: 'Notebook',
      items: [
        { icon: '📓', label: 'Notebook',    tab: 'notebook' },
      ],
    },
    {
      id: 'models',
      icon: '🧠',
      label: 'Models',
      items: [
        { icon: '🧠', label: 'Model',       tab: 'model' },
        { icon: '⚖️',  label: 'Compare',    tab: 'compare' },
      ],
    },
    {
      id: 'training',
      icon: '🎓',
      label: 'Training',
      items: [
        { icon: '🎓', label: 'Training',    tab: 'training' },
        { icon: '📦', label: 'LoRA',        tab: 'lora' },
      ],
    },
    {
      id: 'connectors',
      icon: '🔌',
      label: 'Connectors',
      items: [
        { icon: '🔌', label: 'Connectors',  tab: 'connections' },
        { icon: '📄', label: 'Google Docs', tab: 'docs' },
        { icon: '📊', label: 'Sheets',      tab: 'sheets' },
        { icon: '📑', label: 'Slides',      tab: 'slides' },
        { icon: '📁', label: 'Drive',       tab: 'drive' },
        { icon: '📅', label: 'Calendar',    tab: 'calendar' },
        { icon: '📧', label: 'Gmail',       tab: 'gmail' },
        { icon: '📝', label: 'Notion',      tab: 'notion' },
        { icon: '🐙', label: 'GitHub',      tab: 'github' },
      ],
    },
    {
      id: 'learning',
      icon: '📚',
      label: 'Learning',
      items: [
        { icon: '📚', label: 'Lessons',     tab: 'lessons' },
        { icon: '🃏', label: 'Flashcards',  tab: 'flashcards' },
        { icon: '🧩', label: 'Quiz',        tab: 'quiz' },
        { icon: '📆', label: 'Study Planner', tab: 'planner' },
        { icon: '📖', label: 'Reading List', tab: 'reading' },
        { icon: '📋', label: 'Assignments', tab: 'assignments' },
      ],
    },
    {
      id: 'tools',
      icon: '🛠',
      label: 'Tools',
      items: [
        { icon: '🔍', label: 'Web Search',  tab: 'search' },
        { icon: '🖼️', label: 'Image Gen',   tab: 'image' },
        { icon: '📄', label: 'PDF Reader',  tab: 'pdf' },
        { icon: '🎙️', label: 'Voice Chat',  tab: 'voice' },
        { icon: '💻', label: 'Code Tutor',  tab: 'code' },
        { icon: '∑',  label: 'Math Solver', tab: 'math' },
        { icon: '🌐', label: 'Translation', tab: 'translation' },
        { icon: '🔊', label: 'TTS',         tab: 'tts' },
        { icon: '✍️', label: 'Essay Writer', tab: 'essay' },
        { icon: '📬', label: 'Email Drafter', tab: 'email' },
      ],
    },
    {
      id: 'analytics',
      icon: '📊',
      label: 'Analytics',
      items: [
        { icon: '📊', label: 'Dashboard',   tab: 'dashboard' },
        { icon: '🏆', label: 'Gamification', tab: 'gamification' },
        { icon: '📅', label: 'Weekly Planner', tab: 'weekly' },
      ],
    },
    {
      id: 'settings',
      icon: '⚙️',
      label: 'Settings',
      items: [
        { icon: '⚙️', label: 'Settings',    tab: 'session' },
        { icon: '🔑', label: 'API Keys',    tab: 'api' },
        { icon: '🎨', label: 'Appearance',  tab: 'theme' },
        { icon: 'ℹ️',  label: 'About',       tab: 'about' },
      ],
    },
  ];

  /* ── Build sidebar HTML ───────────────────────────────────── */
  function buildSidebar() {
    var sidebar = document.getElementById('gizmo-sidebar');
    if (!sidebar) return;

    /* Logo */
    var logo = document.createElement('div');
    logo.className = 'sidebar-logo';
    logo.innerHTML = '🤖 <span>Gizmo MY&#8209;AI</span>';
    sidebar.appendChild(logo);

    /* Nav */
    var nav = document.createElement('nav');
    nav.className = 'sidebar-nav';
    nav.setAttribute('aria-label', 'Main navigation');

    NAV_SECTIONS.forEach(function (section) {
      /* Accordion wrapper */
      var accordion = document.createElement('div');
      accordion.className = 'sidebar-accordion';
      accordion.dataset.section = section.id;

      /* Header (toggle) */
      var header = document.createElement('button');
      header.className = 'sidebar-accordion-header';
      header.setAttribute('aria-expanded', 'false');
      header.innerHTML =
        '<span class="sidebar-acc-icon" aria-hidden="true">' + section.icon + '</span>' +
        '<span class="sidebar-acc-label">' + section.label + '</span>' +
        '<span class="sidebar-acc-chevron" aria-hidden="true">›</span>';
      header.addEventListener('click', function () {
        toggleAccordion(accordion);
      });
      accordion.appendChild(header);

      /* Body */
      var body = document.createElement('div');
      body.className = 'sidebar-accordion-body';
      body.hidden = true;

      section.items.forEach(function (item) {
        var a = document.createElement('a');
        a.href = '#';
        a.className = 'sidebar-nav-item';
        a.dataset.tab = item.tab;
        a.innerHTML =
          '<span aria-hidden="true">' + item.icon + '</span>' +
          '<span>' + item.label + '</span>';
        a.addEventListener('click', function (e) {
          e.preventDefault();
          setActiveTab(item.tab);
          switchGradioTab(item.tab);
          if (window.innerWidth < 768) closeSidebar();
        });
        body.appendChild(a);
      });

      accordion.appendChild(body);
      nav.appendChild(accordion);
    });

    sidebar.appendChild(nav);

    /* Footer (profile) */
    var footer = document.createElement('div');
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

  /* ── Accordion toggle ─────────────────────────────────────── */
  function toggleAccordion(accordion) {
    var body = accordion.querySelector('.sidebar-accordion-body');
    var header = accordion.querySelector('.sidebar-accordion-header');
    var isOpen = !body.hidden;
    body.hidden = isOpen;
    header.setAttribute('aria-expanded', String(!isOpen));
    accordion.classList.toggle('open', !isOpen);
  }

  function openAccordionForTab(tabName) {
    document.querySelectorAll('#gizmo-sidebar .sidebar-accordion').forEach(function (acc) {
      var links = acc.querySelectorAll('.sidebar-nav-item');
      for (var i = 0; i < links.length; i++) {
        if (links[i].dataset.tab === tabName) {
          var body = acc.querySelector('.sidebar-accordion-body');
          var header = acc.querySelector('.sidebar-accordion-header');
          if (body && body.hidden) {
            body.hidden = false;
            header.setAttribute('aria-expanded', 'true');
            acc.classList.add('open');
          }
          return;
        }
      }
    });
  }

  /* ── Active tab ───────────────────────────────────────────── */
  function setActiveTab(tabName) {
    document.querySelectorAll('#gizmo-sidebar .sidebar-nav-item').forEach(function (a) {
      a.classList.toggle('active', a.dataset.tab === tabName);
    });
    sessionStorage.setItem('gizmo-active-tab', tabName);
    openAccordionForTab(tabName);
  }

  /* ── Switch the underlying Gradio tab ────────────────────── */
  function switchGradioTab(tabName) {
    var allTabBtns = document.querySelectorAll('[role="tab"]');
    var target = tabName.toLowerCase();
    for (var i = 0; i < allTabBtns.length; i++) {
      var btn = allTabBtns[i];
      var text = (btn.textContent || '').toLowerCase().trim();
      if (text.includes(target)) {
        btn.click();
        return;
      }
    }
  }

  /* ── Sidebar open / close ─────────────────────────────────── */
  function openSidebar() {
    var s = document.getElementById('gizmo-sidebar');
    if (s) {
      s.classList.remove('collapsed');
      s.classList.add('open');
    }
  }

  function closeSidebar() {
    var s = document.getElementById('gizmo-sidebar');
    if (s) {
      s.classList.remove('open');
      if (window.innerWidth < 768) s.classList.add('collapsed');
    }
  }

  function toggleSidebar() {
    var s = document.getElementById('gizmo-sidebar');
    if (!s) return;
    if (s.classList.contains('collapsed') || !s.classList.contains('open')) {
      openSidebar();
    } else {
      closeSidebar();
    }
  }

  /* ── Hamburger button ─────────────────────────────────────── */
  function setupHamburger() {
    var btn = document.querySelector('.topbar-hamburger');
    if (btn) btn.addEventListener('click', toggleSidebar);
  }

  /* ── User profile ─────────────────────────────────────────── */
  function populateProfile() {
    var emailMeta  = document.querySelector('meta[name="gizmo-user-email"]');
    var avatarMeta = document.querySelector('meta[name="gizmo-user-avatar"]');

    var emailEl  = document.getElementById('sidebar-email');
    var avatarEl = document.getElementById('sidebar-avatar');

    if (emailMeta  && emailEl)  emailEl.textContent = emailMeta.content;
    if (avatarMeta && avatarEl) avatarEl.src = avatarMeta.content;
  }

  /* ── Restore active tab on load ───────────────────────────── */
  function restoreActiveTab() {
    var saved = sessionStorage.getItem('gizmo-active-tab');
    if (saved) setActiveTab(saved);
    else setActiveTab('chat');
  }

  /* ── Expose toggle sidebar globally for shortcuts.js ──────── */
  window.gizmoToggleSidebar = toggleSidebar;

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
