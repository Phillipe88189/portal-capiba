# App do Morador – Edifício Capiba (GitHub Pages)

## Avisos push (OneSignal)
- A cada push na branch main que mexe em `dados/**` ou `index.html`, o workflow
  `.github/workflows/push-comunicados.yml` roda `scripts/enviar_push.py` e envia aviso de:
  comunicado novo ou alterado (texto, título, resumo etc.); solicitação nova ou com qualquer alteração
  (situação, resposta no histórico ou outro dado);
  ato da gestão novo ou alterado (`dados/atos.json`: assembleias e reuniões dos Conselhos);
  mês novo na prestação de contas (`DADOS.resumo` no index.html); mudança no texto das Regras do prédio.
- **Ajustes visuais, correções de digitação e mudanças sem novidade para o morador: incluir
  `[sem aviso]` na mensagem do commit.** Sem isso, mudança de texto na aba Regras gera aviso.
- Comunicado que não deve gerar aviso: `"notificar": false` no item de `dados/comunicados.json`.
- Ao alterar um comunicado, preencher `"atualizacao"` com a frase do aviso (ex.: "A equipe técnica já está no prédio"). Sem ele, o aviso usa o primeiro parágrafo novo do texto.
- Antes de publicar, simular: `python3 scripts/enviar_push.py --simular <commit_anterior> HEAD`.
- Os avisos nunca trazem nome, unidade ou telefone de morador (LGPD).
- App ID OneSignal: 409b77e2-8002-4409-80d6-816e93f5c787; chave no secret `ONESIGNAL_REST_API_KEY`.

## Publicação
- Incrementar `VERSAO` em `sw.js` (capiba-AAAA-MM-DD-N) e a "Versão do app" no rodapé do index.html a cada mudança.
- Antes do push: `git fetch origin main && git rebase origin/main`.

## Atos da gestão
- `dados/atos.json`: resumo bem curto das assembleias e reuniões dos Conselhos (aba Prestação de contas, quadro "Atos da gestão").
- Reuniões dos Conselhos: só a lista de tópicos (sem o que foi decidido), com a nota para o morador falar com a gestão e pedir cópia da ata, se for o caso.
- Só o que está na ata assinada; sem dados pessoais além de nome e unidade de quem ocupa cargo; sem valores individuais, pró-labore em discussão ou detalhes de processos.
