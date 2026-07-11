// Service worker for Korea Trip 2026 map.
// Strategy:
//   - Precache the app shell (icons, manifest) for offline launch.
//   - Network-first for HTML + places_data.js so deploys land on next page-load when online.
//   - Cache-first for Leaflet CDN + map tiles (rarely change; offline reuse limited to visited areas).

const VERSION = 'v4';
const SHELL_CACHE = `korea2026-shell-${VERSION}`;
const RUNTIME_CACHE = `korea2026-runtime-${VERSION}`;

// Pre-cache only the static, rarely-changing assets. HTML + places_data.js are network-first
// (precaching them would just put us right back in the "stale on iOS PWA" trap).
const SHELL_ASSETS = [
  './manifest.webmanifest',
  './icon-192.png',
  './icon-512.png',
  './favicon.svg',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
  'https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css',
  'https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css',
  'https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) =>
      Promise.allSettled(SHELL_ASSETS.map((url) => cache.add(url).catch(() => null)))
    ).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== SHELL_CACHE && k !== RUNTIME_CACHE)
          .map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// Listen for a SKIP_WAITING message from the page so users can tap "refresh" to activate
// a freshly-installed waiting SW immediately, instead of waiting for the next launch.
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  const isNavigation = req.mode === 'navigate' ||
    (req.method === 'GET' && req.headers.get('accept')?.includes('text/html'));

  // 1) Page navigations / HTML — network-first so new deploys land immediately when online
  if (isNavigation) {
    event.respondWith(networkFirst(req, RUNTIME_CACHE, './index.html'));
    return;
  }

  // 2) places_data.js — network-first so itinerary updates show up
  if (url.pathname.endsWith('/places_data.js')) {
    event.respondWith(networkFirst(req, RUNTIME_CACHE));
    return;
  }

  // 3) Map tiles — cache-first, store opportunistically
  if (url.hostname.endsWith('.tile.openstreetmap.org')) {
    event.respondWith(cacheFirst(req, RUNTIME_CACHE));
    return;
  }

  // 4) Same-origin shell assets (icons, manifest, sw.js) — cache-first
  if (url.origin === self.location.origin) {
    event.respondWith(cacheFirst(req, SHELL_CACHE));
    return;
  }

  // 5) Everything else (CDN) — stale-while-revalidate
  event.respondWith(staleWhileRevalidate(req, RUNTIME_CACHE));
});

async function networkFirst(req, cacheName, fallbackUrl) {
  try {
    const res = await fetch(req);
    if (res && res.ok) {
      const cache = await caches.open(cacheName);
      cache.put(req, res.clone());
    }
    return res;
  } catch (e) {
    const cached = await caches.match(req);
    if (cached) return cached;
    if (fallbackUrl) {
      const fb = await caches.match(fallbackUrl);
      if (fb) return fb;
    }
    throw e;
  }
}

async function cacheFirst(req, cacheName) {
  const cached = await caches.match(req);
  if (cached) return cached;
  try {
    const res = await fetch(req);
    if (res && res.ok) {
      const cache = await caches.open(cacheName);
      cache.put(req, res.clone());
    }
    return res;
  } catch (e) {
    if (cached) return cached;
    throw e;
  }
}

async function staleWhileRevalidate(req, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(req);
  const fetchPromise = fetch(req)
    .then((res) => {
      if (res && res.ok) cache.put(req, res.clone());
      return res;
    })
    .catch(() => cached);
  return cached || fetchPromise;
}
