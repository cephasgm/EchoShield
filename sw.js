// sw.js - EchoShield Service Worker
const CACHE_NAME = 'echoshield-v1';
const ASSETS_TO_CACHE = [
  '/index.html',
  '/signup.html',
  '/signin.html',
  '/dashboard.html',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
  'https://www.gstatic.com/firebasejs/10.11.0/firebase-app-compat.js',
  'https://www.gstatic.com/firebasejs/10.11.0/firebase-auth-compat.js'
];

// Install event – cache app shell
self.addEventListener('install', (event) => {
  console.log('[SW] Install');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Caching app shell');
      return cache.addAll(ASSETS_TO_CACHE).catch((error) => {
        console.error('[SW] Cache addAll error:', error);
      });
    })
  );
  // Activate immediately
  self.skipWaiting();
});

// Activate event – clean old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activate');
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(
        keyList.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[SW] Removing old cache:', key);
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch event – serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  // Skip Firebase API calls
  if (event.request.url.includes('firebase') || event.request.url.includes('googleapis.com') || event.request.url.includes('gstatic.com')) {
    // For Firebase static resources, we already cached them above. For API calls, let them pass.
    return;
  }
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      // Return cached response if present, otherwise fetch from network
      return cachedResponse || fetch(event.request).then((networkResponse) => {
        // Optionally cache new responses (dynamic caching)
        if (networkResponse && networkResponse.status === 200 && event.request.method === 'GET') {
          const responseClone = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return networkResponse;
      });
    }).catch(() => {
      // Offline fallback for navigation requests
      if (event.request.mode === 'navigate') {
        return caches.match('/index.html');
      }
      return new Response('Offline - resource not available', { status: 503 });
    })
  );
});
