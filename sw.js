/* Mercado Garmendia — Service Worker. Solo cachea recursos estáticos, con límite. */
const CACHE = "mg-catalogo-v1";
const CORE = [
  "./",
  "styles.css",
  "app.js",
  "garmen-2.jpg",
  "manifest.json",
  "icon-192.png",
  "icon-512.png",
];
const MAX_RUNTIME = 60; // límite estricto de entradas en el cache runtime

async function trimCache(cache, max) {
  const keys = await cache.keys();
  if (keys.length <= max) return;
  const excess = keys.length - max;
  for (let i = 0; i < excess; i++) {
    await cache.delete(keys[i]);
  }
}

function isDocument(request) {
  if (request.destination === "document") return true;
  const path = new URL(request.url).pathname;
  return path.endsWith(".html") || path.endsWith("/");
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(CORE)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.origin !== location.origin) return;

  if (isDocument(event.request)) {
    // Páginas (producto/local): network-first, cache con límite (no acumulación indefinida).
    event.respondWith(
      fetch(event.request)
        .then((res) => {
          const clone = res.clone();
          caches.open(CACHE).then((c) =>
            c.put(event.request, clone).then(() => trimCache(c, MAX_RUNTIME))
          );
          return res;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // Estáticos: stale-while-revalidate con límite.
  event.respondWith(
    caches.match(event.request).then((cached) => {
      const network = fetch(event.request)
        .then((res) => {
          if (res && res.status === 200) {
            const clone = res.clone();
            caches.open(CACHE).then((c) =>
              c.put(event.request, clone).then(() => trimCache(c, MAX_RUNTIME))
            );
          }
          return res;
        })
        .catch(() => cached);
      return cached || network;
    })
  );
});
