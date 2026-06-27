# AutoPME Demo Studio

Demo presencial open-source para a consultoria AutoPME Porto. Mostra agentes de voz (PT-PT) e automação de processos (WhatsApp) a prospectos, por nicho, sem depender de dashboards de terceiros.

## Stack (zero novos registos/chaves para alem das ja existentes)

- **Voz**: browser fallback por defeito; opcionalmente Vapi web call (Azure Neural) ou worker local LiveKit + faster-whisper + Piper
- **LLM**: OpenRouter Gemini Flash (chave ja existente)
- **WhatsApp**: Baileys (scan QR com numero dedicado)
- **Email**: Resend (chave ja existente)
- **Backend**: FastAPI (Python)
- **Frontend**: pagina unica HTML + JS vanilla servida pelo proprio FastAPI (Vapi Web SDK + browser APIs)

## Como arrancar — demo completa local (in-person)

A demo pensada para visitas presenciais corre 100% local no portatil (voz em tempo real precisa de WebRTC/UDP, que nao existe em PaaS como o Railway).

1. `docker compose up livekit` — sobe o LiveKit Server local (porta 7880 + RTC)
2. `cp .env.example .env` e preencher com as chaves ja existentes (OpenRouter, Resend)
3. Backend + dashboard: `pip install -r requirements.txt` e `python -m app.main` (porta 8000)
4. Worker de voz (noutro terminal, opcional): `pip install -r requirements-voice.txt` + Piper pt-PT, depois `python -m app.voice.main download-files` e `python -m app.voice.main`
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

## Funcionalidades da demo (nuvem + local)

- **Pesquisar prospect na web**: no passo 1, escreve o nome do negocio (+ localizacao) e prime «Pesquisar e preencher». O backend usa o plugin `web` do OpenRouter (pesquisa Google via Exa, chave ja existente, ~$0.005/pesquisa) e preenche automaticamente nome, horarios, servicos, precos, notas e sugere o nicho. Depois «Carregar demo» adapta o agente a esse negocio.
- **Diagnostico comercial automatico**: depois de carregar o prospect, a demo gera resumo executivo, dores detetadas, quick wins, plano de 30 dias, follow-up por email/WhatsApp e export em Markdown para apoiar o fecho comercial.
- **Chamada de voz simulada**: «Ligar para o agente» (inbound) ou «Agente liga para mim» (outbound) inicia uma chamada no browser — o agente fala (Web Speech API, voz pt-PT) e ouve o microfone (SpeechRecognition pt-PT). Respostas geradas pelo LLM com o system prompt do cenario. Sem LiveKit/WebRTC — funciona na nuvem. Fallback: escrever a resposta. (Para voz em tempo real com STT/TTS locais, usar a demo local com LiveKit.)
- **Ingestao de documentos**: upload de foto/PDF -> OpenRouter vision -> email Resend (real).
- **Calculadora de ROI**: recalc ao vivo.
- **WhatsApp ao vivo**: gateway Baileys + scan QR (sessao persistente em volume /data).

## Estrutura

- `app/prompts_pt_pt.py` — constantes de prompt PT-PT partilhadas (voz + cenarios)
- `app/config.py` — settings (env vars)
- `app/scenarios/` — construtor de cenarios por nicho (7 nichos)
- `app/research/` — pesquisa de prospect na web (OpenRouter plugin web) -> contexto 'mastigado'
- `app/advisor/` — diagnostico comercial, plano de 30 dias e follow-up de venda
- `app/voice/` — agente LiveKit (inbound + outbound) + chat simulado (/api/voice/chat)
- `app/whatsapp/` — gateway Baileys + ingestao de documentos
- `app/dashboard/` — UI single-page servida pelo FastAPI
- `docker-compose.yml` — LiveKit Server local

## Aviso WhatsApp

O Baileys e uma biblioteca nao-oficial que viola os ToS da Meta. Usar numero dedicado descartavel, baixo volume, padroes humanos. Para producao/comercial a via compliant e o WhatsApp Cloud API.
