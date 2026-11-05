// TV Hub Progressive Web App (PWA) Service Worker v7.1.0
const CACHE_NAME = 'tvhub-pwa-v7.9.0';

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Bypass cache for APIs, WebSockets, video streams, and APK downloads
  if (
    url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/proxy') ||
    url.pathname.startsWith('/ws') ||
    url.pathname.endsWith('.m3u8') ||
    url.pathname.endsWith('.ts') ||
    url.pathname.endsWith('.apk') ||
    event.request.method !== 'GET'
  ) {
    return;
  }

  // Network-first strategy: always fetch fresh assets from the server, fallback to cache only if network drops
  event.respondWith(
    fetch(event.request)
      .then((networkRes) => {
        if (networkRes && networkRes.status === 200) {
          const resClone = networkRes.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, resClone));
        }
        return networkRes;
      })
      .catch(() => caches.match(event.request))
  );
});
