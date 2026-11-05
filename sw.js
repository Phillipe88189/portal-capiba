/* Service worker do app Capiba: funciona sem internet e busca sempre a versão mais recente quando há conexão. */
const VERSAO = 'capiba-2026-11-05-12';
const BASE = ['./', 'index.html', 'manifest.webmanifest', 'vendor/d3.min.js', 'dados/chamados.json', 'dados/comunicados.json',
  'icones/icone-192.png', 'icones/icone-512.png', 'icones/apple-touch-icon.png', 'icones/favicon.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VERSAO).then((c) => c.addAll(BASE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== VERSAO && k !== 'capiba-badge').map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.hostname.endsWith('onesignal.com')) return; // notificações: sempre direto do OneSignal
  const conteudo = req.mode === 'navigate' || url.pathname.endsWith('.json') || url.pathname.endsWith('.html');
  if (url.pathname.endsWith('.json')) {
    // dados: sempre da rede, sem cache; a cópia guardada só serve sem internet
    const chave = url.origin + url.pathname;
    e.respondWith(fetch(url.href, {cache: 'no-store'}).then((r) => { if (r.ok) { const cp = r.clone(); caches.open(VERSAO).then((c) => c.put(chave, cp)); } return r; })
      .catch(() => caches.match(chave, {ignoreSearch: true})));
    return;
  }
  if (conteudo) {
    // rede primeiro, sempre conferindo com o servidor (ignora a cópia de 10 min do navegador)
    e.respondWith(fetch(req.mode === 'navigate' ? req.url : req, {cache: 'no-cache'}).then((r) => { if (r.ok) { const cp = r.clone(); caches.open(VERSAO).then((c) => c.put(req, cp)); } return r; })
      .catch(() => caches.match(req, {ignoreSearch: true}).then((r) => r || caches.match('index.html'))));
    return;
  }
  // demais arquivos (ícones, fontes, biblioteca de gráficos): cache primeiro
  e.respondWith(caches.match(req).then((hit) => hit || fetch(req).then((r) => {
    if (r.ok || r.type === 'opaque') { const cp = r.clone(); caches.open(VERSAO).then((c) => c.put(req, cp)); }
    return r;
  })));
});
