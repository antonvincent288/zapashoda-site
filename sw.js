const CACHE = 'zh-sw-v2';
const TCACHE = 'zh-tiles-v1';
const TILE_RE = /(^|\.)basemaps\.cartocdn\.com|arcgisonline\.com|tile\.openstreetmap\.org/;
self.addEventListener('install', (e) => { e.waitUntil(caches.keys().then((keys) => Promise.all(keys.map((k) => k !== CACHE ? caches.delete(k) : null))).then(() => self.skipWaiting())); });
self.addEventListener('install', (e) => { self.skipWaiting(); });
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  if (TILE_RE.test(e.request.url)) {
    e.respondWith(caches.open(TCACHE).then(async (cch) => {
      const hit = await cch.match(e.request);
      if (hit) return hit;
      try {
        const r = await fetch(e.request);
        if (r && (r.ok || r.type === 'opaque')) {
          cch.put(e.request, r.clone());
          cch.keys().then((ks) => { if (ks.length > 700) for (let i = 0; i < 100; i++) cch.delete(ks[i]); });
        }
        return r;
      } catch (e2) { return hit || Response.error(); }
    }));
    return;
  }
  const url = new URL(e.request.url);
  if (url.origin !== location.origin) return;
  e.respondWith(fetch(e.request).then((r) => {
    if (r && r.ok) { const c = r.clone(); caches.open(CACHE).then((cch) => cch.put(e.request, c)); }
    return r;
  }).catch(() => caches.match(e.request)));
});
