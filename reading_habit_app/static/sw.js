const CACHE_NAME = 'reading-habit-v1';
const STATIC_ASSETS = [
  '/',
  '/manifest.webmanifest',
  '/static/style.css',
  '/static/icons/icon-book.svg',
  '/static/icons/icon-180.png',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/scan',
  '/search',
  '/log',
  '/bookshelf'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys
        .filter((key) => key !== CACHE_NAME)
        .map((key) => caches.delete(key))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  // 문서 요청은 네트워크 우선, 실패 시 캐시 fallback
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copied = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, copied));
          return response;
        })
        .catch(() => caches.match(request).then((cached) => cached || caches.match('/')))
    );
    return;
  }

  // 정적 자원은 캐시 우선
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        if (!response || response.status !== 200 || response.type !== 'basic') {
          return response;
        }
        const copied = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, copied));
        return response;
      });
    })
  );
});
