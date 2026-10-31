/* Service worker do app Capiba: funciona sem internet e busca sempre a versão mais recente quando há conexão. */
const VERSAO = 'capiba-2026-10-31-2';
const BASE = ['./', 'index.html', 'manifest.webmanifest', 'vendor/d3.min.js', 'dados/chamados.json',
  'icones/icone-192.png', 'icones/icone-512.png', 'icones/apple-touch-icon.png', 'icones/favicon.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VERSAO).then((c) => c.addAll(BASE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== VERSAO).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const conteudo = req.mode === 'navigate' || url.pathname.endsWith('.json') || url.pathname.endsWith('.html');
  if (conteudo) {
    // rede primeiro: moradores veem a atualização assim que ela é publicada
    e.respondWith(fetch(req).then((r) => { const cp = r.clone(); caches.open(VERSAO).then((c) => c.put(req, cp)); return r; })
      .catch(() => caches.match(req).then((r) => r || caches.match('index.html'))));
    return;
  }
  // demais arquivos (ícones, fontes, biblioteca de gráficos): cache primeiro
  e.respondWith(caches.match(req).then((hit) => hit || fetch(req).then((r) => {
    if (r.ok || r.type === 'opaque') { const cp = r.clone(); caches.open(VERSAO).then((c) => c.put(req, cp)); }
    return r;
  })));
});
