"""Factory: seleciona o provider de voz ativo (com auto-fallback).

- VOICE_PROVIDER=vapi -> Vapi, MAS se faltar VAPI_API_KEY/VAPI_PUBLIC_KEY cai para browser.
- VOICE_PROVIDER=browser -> browser.
- Default (nao definido) -> vapi com auto-fallback.
"""
from __future__ import annotations

from app.config import settings
from app.voice.providers.base import VoiceProvider
from app.voice.providers.browser import BrowserVoiceProvider
from app.voice.providers.vapi import VapiVoiceProvider


def _vapi_ready() -> bool:
    return bool(settings.vapi_api_key and settings.vapi_public_key)


def get_voice_provider() -> VoiceProvider:
    requested = (settings.voice_provider or "vapi").lower().strip()
    if requested == "vapi" and _vapi_ready():
        return VapiVoiceProvider()
    if requested == "vapi" and not _vapi_ready():
        # auto-fallback: config incompleta
        return BrowserVoiceProvider()
    return BrowserVoiceProvider()


def active_provider_name() -> str:
    return get_voice_provider().name
