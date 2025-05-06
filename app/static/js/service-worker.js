// Nome della cache
const CACHE_NAME = 'qr-access-cache-v1';

// Lista di risorse da mettere in cache
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/js/service-worker.js',
  '/static/manifest.json',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.1.1/css/all.min.css',
  'https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js',
  'https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js',
  '/auth/login',
  '/static/img/icons/icon-72x72.png',
  '/static/img/icons/icon-96x96.png',
  '/static/img/icons/icon-128x128.png',
  '/static/img/icons/icon-144x144.png',
  '/static/img/icons/icon-152x152.png',
  '/static/img/icons/icon-192x192.png',
  '/static/img/icons/icon-384x384.png',
  '/static/img/icons/icon-512x512.png'
];

// Installazione del Service Worker
self.addEventListener('install', event => {
  // Metti in pausa fino a quando la cache non è pronta
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Cache aperta');
        return cache.addAll(urlsToCache);
      })
  );
});

// Intercetta le richieste e servi dalla cache se disponibile
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Se la risposta è nella cache, restituiscila
        if (response) {
          return response;
        }
        
        // Altrimenti, vai a cercare la risorsa
        return fetch(event.request)
          .then(response => {
            // Non memorizzare nella cache se la risposta non è buona
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // Clona la risposta perché è un stream che può essere usato solo una volta
            var responseToCache = response.clone();
            
            caches.open(CACHE_NAME)
              .then(cache => {
                // Aggiungi la risposta alla cache
                cache.put(event.request, responseToCache);
              });
            
            return response;
          });
      })
  );
});

// Attivazione: pulisci le cache vecchie
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            // Se il nome della cache non è nella whitelist, eliminalo
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Gestione dei messaggi push
self.addEventListener('push', event => {
  const title = 'Sistema QR Access';
  const options = {
    body: event.data.text(),
    icon: '/static/img/icons/icon-192x192.png',
    badge: '/static/img/icons/icon-72x72.png'
  };
  
  event.waitUntil(self.registration.showNotification(title, options));
}); 