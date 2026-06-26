# AutoPME Demo Studio

Demo presencial open-source para a consultoria AutoPME Porto. Mostra agentes de voz (PT-PT) e automação de processos (WhatsApp) a prospectos, por nicho, sem depender de dashboards de terceiros.

## Stack (zero novos registos/chaves para alem das ja existentes)

- **Voz**: LiveKit Agents (self-hosted em Docker) + faster-whisper (STT) + Piper/XTTS pt-PT (TTS) + Silero VAD
- **LLM**: OpenRouter Gemini Flash (chave ja existente)
- **WhatsApp**: Baileys (scan QR com numero dedicado)
- **Email**: Resend (chave ja existente)
- **Backend**: FastAPI (Python)
- **Frontend**: pagina unica HTML + JS vanilla servida pelo proprio FastAPI (LiveKit Web SDK via CDN)

## Como arrancar (rascunho)

1. `docker compose up livekit` — sobe o LiveKit Server local
2. `cp .env.example .env` e preencher com as chaves ja existentes (OpenRouter, Resend)
3. `pip install -r requirements.txt`
4. `python -m app.main` — sobe FastAPI + agente LiveKit + gateway Baileys
5. Abrir `http://localhost:8000` — escolher nicho + cenario + nome do negocio e correr a demo

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
