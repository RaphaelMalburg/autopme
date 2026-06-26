# AutoPME Demo Studio — imagem slim do control-plane para Railway.
# Contem so o necessario para servir o dashboard, cenarios, calculadora ROI,
# ingestao de documentos (OpenRouter vision + Resend) e mint de tokens LiveKit.
# O worker de voz (livekit-agents + faster-whisper + Piper) e o gateway Baileys
# nao correm aqui — correm localmente no portatil da demo (ver README).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements-deploy.txt ./
RUN pip install -r requirements-deploy.txt

COPY app ./app

# Railway injeta PORT e faz routing para essa porta. Bind explicito a 0.0.0.0
# (nao a settings.host, que pode ficar vazio/127.0.0.1 se o env HOST falhar).
# Shell form para expandir ${PORT} em runtime.
EXPOSE 8000

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
