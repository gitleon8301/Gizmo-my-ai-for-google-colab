/* ============================================================
   Gizmo MY-AI — Service Worker
   static/sw.js
   ============================================================ */

const CACHE_NAME = 'gizmo-v1';

/* Static assets to cache for offline use */
const PRECACHE_URLS = [
  '/',
  '/static/manifest.json',
];

/* ── Install ──────────────────────────────────────────────── */
self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.addAll(PRECACHE_URLS).catch(function () {
        /* Ignore pre-cache failures — server may not be fully up */
      });
    })
  );
  self.skipWaiting();
});

/* ── Activate ─────────────────────────────────────────────── */
self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys
          .filter(function (key) { return key !== CACHE_NAME; })
          .map(function (key) { return caches.delete(key); })
      );
    })
  );
  self.clients.claim();
});

/* ── Fetch ────────────────────────────────────────────────── */
self.addEventListener('fetch', function (event) {
  const url = new URL(event.request.url);

  /* Never intercept API calls, WebSocket upgrades, or OAuth flows */
  if (
    url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/oauth/') ||
    url.pathname.startsWith('/queue/') ||
    event.request.headers.get('upgrade') === 'websocket'
  ) {
    return;
  }

  /* Network-first strategy — fall back to cache, then offline page */
  event.respondWith(
    fetch(event.request)
      .then(function (response) {
        /* Cache successful GET responses for static assets */
        if (
          event.request.method === 'GET' &&
          response.status === 200 &&
          (url.pathname.endsWith('.css') ||
           url.pathname.endsWith('.js')  ||
           url.pathname.endsWith('.png') ||
           url.pathname.endsWith('.ico'))
        ) {
          const copy = response.clone();
          caches.open(CACHE_NAME).then(function (cache) {
            cache.put(event.request, copy);
          });
        }
        return response;
      })
      .catch(function () {
        /* Try cache */
        return caches.match(event.request).then(function (cached) {
          if (cached) return cached;

          /* Offline page for navigation requests */
          if (event.request.mode === 'navigate') {
            return new Response(
              '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">' +
              '<title>Gizmo — Offline</title>' +
              '<style>body{background:#0d0f12;color:#e6e8ec;font-family:sans-serif;' +
              'display:flex;align-items:center;justify-content:center;height:100vh;margin:0}' +
              '.card{text-align:center;padding:40px;background:#111318;' +
              'border-radius:12px;border:1px solid #2a2d35}' +
              'h1{color:#6C63FF}p{color:#9ca3af}</style></head>' +
              '<body><div class="card">' +
              '<h1>🤖 Gizmo MY-AI</h1>' +
              '<p>You appear to be offline or the server is unreachable.</p>' +
              '<p>Please check that the server is running and try again.</p>' +
              '</div></body></html>',
              { headers: { 'Content-Type': 'text/html' } }
            );
          }
          return new Response('Offline', { status: 503 });
        });
      })
  );
});
