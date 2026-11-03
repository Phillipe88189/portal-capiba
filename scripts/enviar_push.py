"""Envia avisos push (OneSignal) para as novidades do app entre duas versões do repositório.

Uso:
  python3 scripts/enviar_push.py <commit_anterior> <commit_atual> [mensagem_do_commit]
  python3 scripts/enviar_push.py --comunicado 2026-003        (reenvio manual)
  python3 scripts/enviar_push.py --simular <anterior> <atual> (só mostra, não envia)
  python3 scripts/enviar_push.py --teste                      (aviso de teste a todos os inscritos)

Novidades avisadas:
  - comunicado novo ou alterado (dados/comunicados.json), exceto "notificar": false.
    Na alteração, o aviso usa o campo "atualizacao" do comunicado, se houver; senão, o
    primeiro parágrafo novo do texto; senão, o resumo.
  - solicitação nova ou com qualquer alteração (dados/chamados.json): situação, resposta
    no histórico ou outro dado
  - nova prestação de contas mensal (mês novo em DADOS.resumo do index.html)
  - mudança no texto das Regras do prédio (seção #regras do index.html)
Se a mensagem do commit tiver "[sem aviso]", nada é enviado (correções e ajustes visuais).
Requer ONESIGNAL_APP_ID e ONESIGNAL_REST_API_KEY.
"""
import html, json, os, re, subprocess, sys, urllib.error, urllib.request

BASE = 'https://phillipe88189.github.io/portal-capiba/'
ICONE = BASE + 'icones/icone-192.png'
MAX_AVISOS = 4  # acima disso, manda um aviso único com o resumo
MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto',
         'setembro', 'outubro', 'novembro', 'dezembro']


def ler(commit, caminho):
    if not commit or set(commit) == {'0'}:
        return ''
    r = subprocess.run(['git', 'show', f'{commit}:{caminho}'], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ''


def js(txt, padrao=None):
    try:
        return json.loads(txt) if txt.strip() else padrao
    except ValueError:
        return padrao


def corta(t, n=170):
    t = re.sub(r'\s+', ' ', str(t or '')).strip()
    return t if len(t) <= n else t[:n - 1].rstrip() + '…'


def meses_contas(html_txt):
    m = re.search(r'const DADOS = (\{.*?\});\s*$', html_txt, re.M)
    d = js(m.group(1), {}) if m else {}
    return {r['mes'] for r in (d or {}).get('resumo', []) if r.get('mes')}


def texto_regras(html_txt):
    m = re.search(r'<div class="wrap view" id="regras"[^>]*>(.*?)<div class="wrap view"', html_txt, re.S)
    if not m:
        return ''
    t = re.sub(r'<(script|style)\b.*?</\1>', ' ', m.group(1), flags=re.S)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', t))
    return re.sub(r'\s+', ' ', t).strip()


def novidades(antes, depois):
    av = []
    # 1) Comunicados: novos e alterados
    campos = ('titulo', 'resumo', 'texto', 'atualizacao', 'categoria', 'base', 'anexo', 'encerrado')
    ca = {c['numero']: c for c in (js(ler(antes, 'dados/comunicados.json'), {}) or {}).get('comunicados', [])}
    for c in sorted((js(ler(depois, 'dados/comunicados.json'), {}) or {}).get('comunicados', []),
                    key=lambda c: c.get('publicado_em', '')):
        if c.get('notificar', True) is False:
            continue
        rot = 'Regimento em dia' if c.get('tipo') == 'educativo' else 'Comunica Capiba'
        link = 'index.html#comunica/' + c['numero']
        velho = ca.get(c['numero'])
        if velho is None:
            av.append((f"{rot} · {c['titulo']}", corta(c.get('resumo') or 'Novo comunicado da administração.'), link))
            continue
        if all(c.get(k) == velho.get(k) for k in campos):
            continue
        novos = [t for t in (c.get('texto') or []) if t not in (velho.get('texto') or [])]
        if c.get('atualizacao') and c.get('atualizacao') != velho.get('atualizacao'):
            corpo = c['atualizacao']
        elif novos:
            corpo = novos[0]
        else:
            corpo = c.get('resumo') or 'O comunicado foi atualizado. Confira no app.'
        av.append((f"Atualização · {c['titulo']}", corta(corpo), link))
    # 2) Solicitações (sem nome nem unidade — LGPD)
    ant = {c['numero']: c for c in (js(ler(antes, 'dados/chamados.json'), {}) or {}).get('chamados', [])}
    for c in (js(ler(depois, 'dados/chamados.json'), {}) or {}).get('chamados', []):
        n, velho = c['numero'], ant.get(c['numero'])
        onde = ' – '.join(x for x in (c.get('assunto'), c.get('local')) if x)
        if velho is None:
            av.append((f'Nova solicitação nº {n}', corta(f"{onde}. Situação: {c.get('status', 'Aberto')}."), 'index.html#chamados'))
            continue
        if c == velho:
            continue
        mudou_status = c.get('status') != velho.get('status')
        nova_resp = len(c.get('historico') or []) > len(velho.get('historico') or [])
        if mudou_status or nova_resp:
            ult = (c.get('historico') or [{}])[-1].get('texto', '')
            corpo = ult or onde
        else:
            corpo = f'{onde}. Os dados da solicitação foram atualizados.' if onde else 'Os dados da solicitação foram atualizados.'
        av.append((f"Solicitação nº {n} · {c.get('status', '')}".rstrip(' ·'), corta(corpo), 'index.html#chamados'))
    # 3) Prestação de contas
    ia, idep = ler(antes, 'index.html'), ler(depois, 'index.html')
    for mes in sorted(meses_contas(idep) - meses_contas(ia)):
        a, m = mes.split('-')
        av.append((f'Prestação de contas de {MESES[int(m) - 1]}/{a}',
                   'Já está no app: receitas, despesas e saldo do mês.', 'index.html#contas'))
    # 4) Regras do prédio
    ra, rd = texto_regras(ia), texto_regras(idep)
    # compara as palavras (sem ordem): mudar um bloco de lugar ou ajustar o layout não gera aviso
    if ra and rd and sorted(ra.split()) != sorted(rd.split()):
        av.append(('Regras do prédio atualizadas', 'Confira no app o que mudou nas regras do Capiba.', 'index.html#regras'))
    if len(av) > MAX_AVISOS:
        av = [(f'{len(av)} novidades no app do Capiba',
               corta('; '.join(t for t, _, _ in av)), 'index.html')]
    return av


def enviar(titulo, texto, link, app_id, chave):
    corpo = json.dumps({
        'app_id': app_id, 'target_channel': 'push', 'included_segments': ['Total Subscriptions'],
        'headings': {'en': titulo, 'pt': titulo}, 'contents': {'en': texto, 'pt': texto},
        'web_url': BASE + link, 'chrome_web_icon': ICONE, 'firefox_icon': ICONE,
    }).encode()
    for esquema in ('Key', 'Basic'):  # App API Key nova usa "Key"; chave antiga usa "Basic"
        req = urllib.request.Request('https://api.onesignal.com/notifications?c=push', data=corpo, method='POST',
                                     headers={'Content-Type': 'application/json; charset=utf-8',
                                              'Authorization': f'{esquema} {chave}'})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                resp = json.loads(r.read() or b'{}')
                print(f'OK  {titulo} (id {resp.get("id")}, erros: {resp.get("errors")})')
                return True
        except urllib.error.HTTPError as e:
            if e.code in (401, 403) and esquema == 'Key':
                continue
            print(f'ERRO {titulo}: HTTP {e.code} – {e.read().decode(errors="replace")[:300]}')
            return False
    print(f'ERRO {titulo}: chave recusada (confira o secret ONESIGNAL_REST_API_KEY)')
    return False


def main():
    a = sys.argv[1:]
    if a and a[0] == '--simular':
        for t in novidades(a[1], a[2]):
            print(' | '.join(t))
        return
    if a and a[0] == '--teste':
        av = [('Teste · Avisos do app Capiba',
               'Este é um aviso de teste da administração. Se você recebeu, os avisos do app estão funcionando. Pode ignorar.',
               'index.html#comunica')]
    elif a and a[0] == '--comunicado':
        lista = (js(open('dados/comunicados.json', encoding='utf-8').read(), {}) or {}).get('comunicados', [])
        c = next((x for x in lista if x['numero'] == a[1]), None)
        if not c:
            sys.exit(f'Comunicado {a[1]} não encontrado.')
        if c.get('atualizacao'):
            av = [(f"Atualização · {c['titulo']}", corta(c['atualizacao']), 'index.html#comunica/' + c['numero'])]
        else:
            av = [(f"Comunica Capiba · {c['titulo']}", corta(c.get('resumo')), 'index.html#comunica/' + c['numero'])]
    else:
        if len(a) > 2 and '[sem aviso]' in a[2].lower():
            print('Commit marcado com [sem aviso]: nada enviado.')
            return
        av = novidades(a[0], a[1])
    if not av:
        print('Nenhuma novidade para avisar.')
        return
    app_id, chave = os.environ.get('ONESIGNAL_APP_ID'), os.environ.get('ONESIGNAL_REST_API_KEY')
    if not app_id or not chave:
        sys.exit('Faltam ONESIGNAL_APP_ID ou ONESIGNAL_REST_API_KEY (secret do repositório).')
    falhas = [t for t, x, l in av if not enviar(t, x, l, app_id, chave)]
    if falhas:
        sys.exit('Falha no envio de: ' + '; '.join(falhas))


if __name__ == '__main__':
    main()
