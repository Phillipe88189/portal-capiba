/* Service worker das notificações (OneSignal). Fica numa pasta própria para não interferir no sw.js do app. */
importScripts('https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js');

/* Número no ícone do app: soma 1 a cada aviso recebido com o app fechado.
   Quando o morador abre o app, o próprio app recalcula o número pelos comunicados não lidos. */
const CX = 'capiba-badge';
self.addEventListener('push', (e) => {
  e.waitUntil((async () => {
    try {
      const c = await caches.open(CX);
      const r = await c.match('n');
      const n = (r ? parseInt(await r.text(), 10) || 0 : 0) + 1;
      await c.put('n', new Response(String(n)));
      if (self.navigator && 'setAppBadge' in self.navigator) await self.navigator.setAppBadge(n);
    } catch (err) {}
  })());
});
