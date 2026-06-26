"""Application configuration using Pydantic Settings.

Usa apenas chaves ja existentes no projeto agente-consultoria:
- OpenRouter (LLM)
- Resend (email)

LiveKit corre self-hosted em Docker e gera a sua propria key/secret local.
Baileys usa scan QR com numero dedicado (sem chave).
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Ambiente
    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000

    # LiveKit Server local (docker compose). O servidor gera key/secret;
    # ver docker-compose.yml e livekit.yaml. Em dev, usar os valores do yaml.
    livekit_url: str = "ws://localhost:7880"
    livekit_api_key: str = "devkey"
    livekit_api_secret: str = "secret"

    # OpenRouter LLM (chave ja existente)
    openrouter_api_key: str
    openrouter_default_model: str = "google/gemini-2.5-flash"

    # Resend email (chave ja existente)
    resend_api_key: str
    email_from: str = "AutoPME <noreply@caiporalabs.com>"
    demo_notify_email: str = "demo.consultoria@caiporalabs.com"

    # WhatsApp Baileys gateway (processo Node sidecar)
    baileys_gateway_url: str = "http://localhost:3001"

    # STT/TTS locais
    whisper_model: str = "large-v3"
    whisper_language: str = "pt"
    tts_engine: str = "piper"  # "piper" | "xtts"
    tts_voice: str = "pt-PT"   # voz Piper/XTTS pt-PT

    # Demo
    default_niche: str = "dental"

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
