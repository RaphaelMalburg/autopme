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

    # Azure Speech TTS (chave JA EXISTENTE — usada antes via Vapi).
    # Opcional: se definido, o endpoint /api/voice/tts usa vozes neurais pt-PT
    # (RaquelNeural/DuarteNeural) — muito melhor que a voz do browser.
    # 500K chars/mes gratis. Se vazio, o dashboard usa a voz do browser.
    azure_speech_key: Optional[str] = None
    azure_speech_region: str = "westeurope"
    azure_speech_voice: str = "pt-PT-RaquelNeural"  # RaquelNeural(F) | DuarteNeural(M) | FernandaNeural(F)

    # Voz modular — provider abstraído (app/voice/providers/).
    # VOICE_PROVIDER=vapi usa Vapi (voz neural Azure real); browser = fallback simulado.
    # As chaves Vapi JA EXISTEM no agente-consultoria/.env (sem novos registos).
    voice_provider: str = "vapi"  # "vapi" | "browser" (auto-fallback se faltar config)
    voice_default_language: str = "pt-PT"
    vapi_api_key: Optional[str] = None
    vapi_public_key: Optional[str] = None  # Web SDK no browser (dashboard Vapi → API Keys → public)
    vapi_assistant_id_outbound: Optional[str] = None
    vapi_assistant_id_inbound: Optional[str] = None
    vapi_phone_number_id: Optional[str] = None
    vapi_webhook_secret: Optional[str] = None
    vapi_voice_provider: str = "azure"  # provedor de voz dentro do Vapi (azure)
    vapi_voice_id: str = "pt-PT-RaquelNeural"  # default; por idioma via provider

    # Demo
    default_niche: str = "dental"
    admin_password: Optional[str] = None
    auth_cookie_name: str = "autopme_demo_auth"

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
