"""Providers de voz modulares (AutoPME Demo Studio).

Interface abstraida + implementacoes intercambiaveis:
- vapi    : voz neural Azure real via Vapi web calls (precisa de chaves existentes)
- browser : fallback simulado (LLM + Web Speech API do browser)

Selecao por VOICE_PROVIDER (auto-fallback se faltar config). Para trocar/remover
o Vapi depois, basta mudar a var de env — sem tocar no resto do codigo.

    from app.voice.providers import get_voice_provider
    provider = get_voice_provider()
    result = await provider.start_call(niche="dental", business_name="X", direction="inbound",
                                       language="pt-PT", system_prompt=..., first_message=...)
"""
from app.voice.providers.base import VoiceProvider, VoiceProviderError
from app.voice.providers.factory import get_voice_provider

__all__ = ["VoiceProvider", "VoiceProviderError", "get_voice_provider"]
