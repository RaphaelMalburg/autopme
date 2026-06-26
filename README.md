# AutoPME Demo Studio

Demo presencial open-source para a consultoria AutoPME Porto. Mostra agentes de voz (PT-PT) e automação de processos (WhatsApp) a prospectos, por nicho, sem depender de dashboards de terceiros.

## Stack (zero novos registos/chaves para alem das ja existentes)

- **Voz**: LiveKit Agents (self-hosted em Docker) + faster-whisper (STT) + Piper/XTTS pt-PT (TTS) + Silero VAD
- **LLM**: OpenRouter Gemini Flash (chave ja existente)
- **WhatsApp**: Baileys (scan QR com numero dedicado)
- **Email**: Resend (chave ja existente)
- **Backend**: FastAPI (Python)
- **Frontend**: pagina unica HTML + JS vanilla servida pelo proprio FastAPI (LiveKit Web SDK via CDN)

## Como arrancar — demo completa local (in-person)

A demo pensada para visitas presenciais corre 100% local no portatil (voz em tempo real precisa de WebRTC/UDP, que nao existe em PaaS como o Railway).

1. `docker compose up livekit` — sobe o LiveKit Server local (porta 7880 + RTC)
2. `cp .env.example .env` e preencher com as chaves ja existentes (OpenRouter, Resend)
3. Backend + dashboard: `pip install -r requirements.txt` e `python -m app.main` (porta 8000)
4. Worker de voz (noutro terminal): `pip install livekit-agents livekit-api httpx faster-whisper numpy` + Piper pt-PT, depois `python -m app.voice.main download-files` e `python -m app.voice.main`
5. Gateway WhatsApp (noutro terminal): `cd app/whatsapp/gateway && npm install && node index.js` — scanner o QR com o telefone
6. Abrir `http://localhost:8000` — escolher nicho + cenario + nome do negocio e correr a demo

## Deploy na nuvem (Railway) — showcase online

O que e implantavel em cloud (PaaS) sem WebRTC/UDP:
- Dashboard, cenarios por nicho, calculadora de ROI
- Ingestao de documentos (foto/PDF -> OpenRouter vision -> email Resend) — real
- WhatsApp ao vivo via gateway Baileys (servico Node + volume persistente + scan QR no browser)
- Mint de tokens LiveKit (o browser do portatil liga-se ao LiveKit **local**)

O que **nao** corre na cloud: o LiveKit Server (UDP/RTC) e o worker de voz (faster-whisper/Piper). Para a chamada de voz em tempo real, usar a demo local acima.

### Control-plane (FastAPI)
- Imagem: `Dockerfile` (Python 3.12-slim, deps em `requirements-deploy.txt`)
- Railway injeta `PORT`; a app le `settings.port` do env `PORT`
- Vars obrigatórias: `OPENROUTER_API_KEY`, `RESEND_API_KEY` (chaves existentes). Resto ver `.env.example`
- `BAILEYS_GATEWAY_URL` deve apontar para o dominio publico do servico gateway

### Gateway WhatsApp (Baileys)
- Servico Node (Nixpacks deteta `app/whatsapp/gateway/package.json`, start `npm start`)
- Montar volume em `/data` e definir `AUTH_DIR=/data/baileys_auth` (sessao persistente entre deploys)
- `APP_WEBHOOK_URL=https://<dominio-control-plane>/api/whatsapp/webhook`
- QR disponivel em `GET /qr` (mostrado no dashboard) — scan uma vez com WhatsApp > Linked devices

## Estrutura

- `app/prompts_pt_pt.py` — constantes de prompt PT-PT partilhadas (voz + cenarios)
- `app/config.py` — settings (env vars)
- `app/scenarios/` — construtor de cenarios por nicho (7 nichos)
- `app/voice/` — agente LiveKit (inbound + outbound)
- `app/whatsapp/` — gateway Baileys + ingestao de documentos
- `app/dashboard/` — UI single-page servida pelo FastAPI
- `docker-compose.yml` — LiveKit Server local

## Aviso WhatsApp

O Baileys e uma biblioteca nao-oficial que viola os ToS da Meta. Usar numero dedicado descartavel, baixo volume, padroes humanos. Para producao/comercial a via compliant e o WhatsApp Cloud API.
