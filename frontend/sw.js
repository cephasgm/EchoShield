const CACHE_NAME = 'echoshield-v1';
const APP_SHELL = [
  '/',
  '/index.html',
  '/signin.html',
  '/signup.html',
  '/dashboard.html',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png'
];

// Install event – cache the app shell
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('Opened cache');
      return cache.addAll(APP_SHELL);
    })
  );
  self.skipWaiting(); // activate immediately
});

// Activate event – clean old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// Fetch strategy: network first, fall back to cache
self.addEventListener('fetch', event => {
  // Only handle navigation requests and same-origin GETs
  const { request } = event;
  if (request.method !== 'GET') return;

  event.respondWith(
    fetch(request)
      .then(networkResponse => {
        // Update cache with fresh copy
        const responseClone = networkResponse.clone();
        caches.open(CACHE_NAME).then(cache => {
          if (request.url.startsWith(self.location.origin)) {
            cache.put(request, responseClone);
          }
        });
        return networkResponse;
      })
      .catch(() => caches.match(request).then(cachedResponse => {
        // Offline fallback – if navigating, return index.html
        if (request.mode === 'navigate' && !cachedResponse) {
          return caches.match('/index.html');
        }
        return cachedResponse;
      }))
  );
});
