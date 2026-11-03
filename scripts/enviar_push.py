"""Envia notificação push (OneSignal) para cada comunicado NOVO em dados/comunicados.json.

Uso: python3 scripts/enviar_push.py <json_anterior|-> <json_atual> [numero_forcado]
- Compara a versão anterior com a atual e avisa só os números que não existiam antes.
- Comunicados com "notificar": false não geram aviso.
- numero_forcado: reenvia um comunicado específico (disparo manual / teste).
Requer as variáveis ONESIGNAL_APP_ID e ONESIGNAL_REST_API_KEY.
"""
import json, os, sys, urllib.request, urllib.error

BASE = 'https://phillipe88189.github.io/portal-capiba/'
ICONE = BASE + 'icones/icone-192.png'


def numeros(caminho):
    if caminho == '-' or not os.path.exists(caminho) or os.path.getsize(caminho) == 0:
        return set()
    return {c['numero'] for c in json.load(open(caminho, encoding='utf-8')).get('comunicados', [])}


def enviar(c, app_id, chave):
    titulo = c['titulo'].strip()
    resumo = (c.get('resumo') or '').strip() or 'Novo comunicado da administração do Capiba.'
    if len(resumo) > 170:
        resumo = resumo[:167].rstrip() + '…'
    cabeca = ('Regimento em dia · ' if c.get('tipo') == 'educativo' else 'Comunica Capiba · ') + titulo
    corpo = {
        'app_id': app_id,
        'target_channel': 'push',
        'included_segments': ['Total Subscriptions'],
        'headings': {'en': cabeca, 'pt': cabeca},
        'contents': {'en': resumo, 'pt': resumo},
        'web_url': BASE + 'index.html#comunica/' + c['numero'],
        'chrome_web_icon': ICONE,
        'firefox_icon': ICONE,
        'web_push_topic': 'comunicado-' + c['numero'],
    }
    dados = json.dumps(corpo).encode()
    for esquema in ('Key', 'Basic'):  # chave nova ("App API Key") usa Key; chave antiga usa Basic
        req = urllib.request.Request('https://api.onesignal.com/notifications?c=push', data=dados, method='POST',
                                     headers={'Content-Type': 'application/json; charset=utf-8',
                                              'Authorization': f'{esquema} {chave}'})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                resp = json.loads(r.read() or b'{}')
                print(f"{c['numero']}: enviado (id {resp.get('id')}, erros: {resp.get('errors')})")
                return True
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors='replace')[:300]
            if e.code in (401, 403) and esquema == 'Key':
                continue
            print(f"{c['numero']}: falhou HTTP {e.code} – {msg}")
            return False
    print(f"{c['numero']}: chave recusada pelo OneSignal (confira o secret ONESIGNAL_REST_API_KEY)")
    return False


def main():
    anterior, atual = sys.argv[1], sys.argv[2]
    forcado = sys.argv[3].strip() if len(sys.argv) > 3 else ''
    app_id, chave = os.environ.get('ONESIGNAL_APP_ID'), os.environ.get('ONESIGNAL_REST_API_KEY')
    if not app_id or not chave:
        sys.exit('Faltam ONESIGNAL_APP_ID ou ONESIGNAL_REST_API_KEY (secret do repositório).')
    lista = json.load(open(atual, encoding='utf-8')).get('comunicados', [])
    if forcado:
        alvo = [c for c in lista if c['numero'] == forcado]
        if not alvo:
            sys.exit(f'Comunicado {forcado} não encontrado.')
    else:
        antes = numeros(anterior)
        alvo = [c for c in lista if c['numero'] not in antes and c.get('notificar', True) is not False]
        alvo = sorted(alvo, key=lambda c: c.get('publicado_em', ''))[-3:]  # trava: no máximo 3 por publicação
    if not alvo:
        print('Nenhum comunicado novo para avisar.')
        return
    falhas = [c['numero'] for c in alvo if not enviar(c, app_id, chave)]
    if falhas:
        sys.exit('Falha no envio de: ' + ', '.join(falhas))


if __name__ == '__main__':
    main()
