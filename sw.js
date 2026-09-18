// J 工作台 Service Worker - 让网页可"安装"并支持离线
// v2：导航/HTML 改为 network-first，保证手机/平板安装的 PWA 始终拉取最新 index.html
const CACHE = 'j-workbench-v2';
const SHELL = [
  './',
  './index.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
  './icon-maskable-512.png',
  './apple-touch-icon.png'
];

self.addEventListener('install', (e) => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const isDoc =
    req.mode === 'navigate' ||
    url.pathname.endsWith('index.html') ||
    url.pathname === '/' ||
    url.pathname.endsWith('/');

  if (isDoc) {
    // 文档：network-first —— 在线时永远拉取最新，离线才回退缓存
    e.respondWith(
      fetch(req)
        .then((resp) => {
          if (resp && resp.status === 200 && url.origin === self.location.origin) {
            const copy = resp.clone();
            caches.open(CACHE).then((c) => c.put(req, copy));
          }
          return resp;
        })
        .catch(() => caches.match(req).then((c) => c || caches.match('./index.html')))
    );
    return;
  }

  // 静态资源：cache-first（命中即返回，未命中再走网络并缓存）
  e.respondWith(
    caches.match(req).then((cached) => {
      if (cached) return cached;
      return fetch(req).then((resp) => {
        if (resp && resp.status === 200 && url.origin === self.location.origin) {
          const copy = resp.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
        }
        return resp;
      }).catch(() => cached);
    })
  );
});
