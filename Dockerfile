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

# Railway injeta PORT; a app le settings.port a partir de PORT (case-insensitive).
EXPOSE 8000

CMD ["python", "-m", "app.main"]
