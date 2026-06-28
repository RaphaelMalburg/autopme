# Instalação & Deploy do sistema

Como montar o sistema (demo + produção). O demo-studio é a tua arma de venda; o
mesmo backend serve para entregar a clientes.

## Componentes
- **web** (FastAPI): dashboard, cenários, diagnóstico, voz (Vapi), CRM Notion, histórico.
- **gateway** (Node/Baileys): WhatsApp para demo/piloto.
- **Voz:** Vapi (web call no browser, sem telefonia) — neural multi-idioma.
- **LLM:** OpenRouter. **Email:** Resend.

## Local (demo presencial no portátil)
```bash
cp .env.example .env   # preencher chaves (OpenRouter, Resend, Vapi)
pip install -r requirements.txt
python -m app.main      # http://localhost:8000
# Gateway WhatsApp (outro terminal):
cd app/whatsapp/gateway && npm install && node index.js   # ler QR no dashboard
```

## Cloud (Railway) — showcase online
- Serviço **web**: deploy da **raiz** (usa `railway.toml` raiz → uvicorn). `railway up --service web`.
- Serviço **gateway**: deploy da pasta do gateway:
  `railway up app/whatsapp/gateway --path-as-root --service gateway`
  ⚠️ Não fazer `railway up --service gateway` da raiz (arranca o Python e crasha).
- **Volume** no web em `/app/data` + `STORAGE_DIR=/app/data` → histórico persiste.
- **Gateway**: volume em `/data` + `AUTH_DIR=/data/baileys_auth` (sessão WhatsApp persistente).

## Variáveis essenciais (.env / Railway)
| Var | Para quê |
|---|---|
| `OPENROUTER_API_KEY` | LLM |
| `RESEND_API_KEY`, `EMAIL_FROM` | Email |
| `VAPI_API_KEY`, `VAPI_PUBLIC_KEY` | Voz (web call) |
| `VAPI_VOICE_PROVIDER`, `VAPI_VOICE_ID` | Motor de voz (azure pt-PT-RaquelNeural ou 11labs) |
| `VOICE_MULTILINGUAL` | `true` = uma voz multilingue; `false` = voz nativa por idioma |
| `NOTION_TOKEN`, `NOTION_PIPELINE_DATABASE_ID` | Enviar prospects para o funil |
| `STORAGE_DIR` | Histórico (apontar ao volume em prod) |
| `ADMIN_PASSWORD` | Proteger o dashboard |
| `BAILEYS_GATEWAY_URL` | web → gateway |

## Voz: qualidade
- pt-PT nativo: `VAPI_VOICE_PROVIDER=azure`, `VAPI_VOICE_ID=pt-PT-RaquelNeural` (europeu).
- Multilingue (muda de língua a meio): `VOICE_MULTILINGUAL=true`, `VAPI_VOICE_PROVIDER=11labs`, `VAPI_VOICE_ID=<voz 11labs>`.

## Carregar um nicho em 10s (demo)
Usa os [presets](../presets/): copia `extra` + `free_context` do JSON do nicho para
os campos do passo 1 do dashboard, ou usa-os via API `/api/scenarios/build`.

## Passar de demo a produção (WhatsApp)
Trocar o adaptador Baileys por Cloud API (Twilio/360dialog) mantendo o mesmo
backend. Ver [como-funciona-cloud-api](../whatsapp/como-funciona-cloud-api.md).
