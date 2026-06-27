"""Provider Vapi — voz neural real via Vapi Web SDK.

Usa as chaves Vapi JA EXISTENTES (agente-consultoria/.env). Para a demo
presencial usa *web call* (transport: web): chamada no browser via Vapi Web SDK,
com pipeline de voz real (Azure Neural TTS + Deepgram STT + LLM), sem telefonar.

Modular: para remover o Vapi depois, mudar VOICE_PROVIDER=browser — o router
delega no provider browser (LLM + Web Speech API). Sem chaves Vapi configuradas,
o factory auto-fallback para browser.

API: o backend devolve um assistant transiente completo para o dashboard iniciar
via Vapi Web SDK. Isto garante que a voz efetiva usada na demo e a configurada
dinamicamente aqui, sem depender de um assistantId salvo com voz desatualizada.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from app.config import settings
from app.voice.providers.base import VoiceProvider, VoiceProviderError

logger = logging.getLogger(__name__)

VAPI_API_URL = "https://api.vapi.ai"

# Mapeamento idioma -> voz Azure Neural (natural, multi-idioma).
AZURE_VOICE_BY_LANG: dict[str, str] = {
    "pt-PT": "pt-PT-RaquelNeural",   # RaquelNeural(F) | pt-PT-DuarteNeural(M) | pt-PT-FernandaNeural(F)
    "pt-BR": "pt-BR-FranciscaNeural",
    "en-US": "en-US-JennyNeural",
    "en-GB": "en-GB-SoniaNeural",
    "es-ES": "es-ES-ElviraNeural",
    "es-US": "es-US-PalomaNeural",
    "fr-FR": "fr-FR-DeniseNeural",
    "de-DE": "de-DE-KatjaNeural",
    "it-IT": "it-IT-ElsaNeural",
    "nl-NL": "nl-NL-ColetteNeural",
}

# Mapeamento idioma -> lingua do transcriber Deepgram.
DEEPGRAM_LANG_BY_LANG: dict[str, str] = {
    "pt-PT": "pt-PT",
    "pt-BR": "pt-BR",
    "en-US": "en-US",
    "en-GB": "en-GB",
    "es-ES": "es-ES",
    "es-US": "es-US",
    "fr-FR": "fr-FR",
    "de-DE": "de",
    "it-IT": "it",
    "nl-NL": "nl",
}

SUPPORTED_LANGUAGES = sorted(set(AZURE_VOICE_BY_LANG.keys()))


def _voice_config_for(language: str) -> dict[str, str]:
    """Escolhe o motor de voz (dentro do Vapi) para o idioma.

    Por idioma usamos a voz Azure Neural correta (pt-PT -> portugues europeu
    real, NAO uma voz nativa inglesa do Vapi). Para o idioma default (pt-PT)
    respeitamos um override explicito do .env (VAPI_VOICE_PROVIDER+VAPI_VOICE_ID),
    o que permite trocar a voz pt-PT (ex.: Raquel/Duarte/Fernanda ou 11labs) sem
    mexer no codigo. Para os restantes idiomas usamos sempre o mapa por idioma,
    para um voiceId fixo de pt-PT nao "contaminar" en-US, es-ES, etc.
    """
    normalized = (language or "").strip()
    default_lang = (settings.voice_default_language or "pt-PT").strip()
    explicit_provider = (settings.vapi_voice_provider or "azure").strip().lower()
    explicit_voice_id = (settings.vapi_voice_id or "").strip()

    # Modo multilingue: uma unica voz para TODOS os idiomas (muda de lingua a
    # meio da chamada). Ideal com 11labs multilingue.
    if settings.voice_multilingual and explicit_voice_id:
        return _with_11labs_model({"provider": explicit_provider or "11labs", "voiceId": explicit_voice_id})

    # Override do .env para o idioma default (ex.: trocar a voz pt-PT).
    if explicit_voice_id and normalized == default_lang:
        return _with_11labs_model({"provider": explicit_provider or "azure", "voiceId": explicit_voice_id})

    # Default por idioma: voz Azure Neural nativa (sotaque correto por lingua).
    return {
        "provider": "azure",
        "voiceId": AZURE_VOICE_BY_LANG.get(normalized) or "en-US-JennyNeural",
    }


def _with_11labs_model(voice: dict[str, str]) -> dict[str, str]:
    """Acrescenta o modelo multilingue quando a voz e ElevenLabs (11labs)."""
    if voice.get("provider") == "11labs":
        voice.setdefault("model", settings.vapi_11labs_model or "eleven_turbo_v2_5")
    return voice


def _deepgram_lang_for(language: str) -> str:
    return DEEPGRAM_LANG_BY_LANG.get(language, "multi")


class VapiVoiceProvider(VoiceProvider):
    name = "vapi"

    def __init__(self):
        self.api_key = settings.vapi_api_key
        self.assistant_id_outbound = settings.vapi_assistant_id_outbound
        self.assistant_id_inbound = settings.vapi_assistant_id_inbound
        self.phone_number_id = settings.vapi_phone_number_id
        self.public_key = settings.vapi_public_key
        self.voice_provider = settings.vapi_voice_provider or "azure"

    def _configured(self) -> bool:
        # Para web calls so precisa da API key (server) + public key (browser Web SDK).
        return bool(self.api_key and self.public_key)

    def _headers(self) -> dict:
        if not self.api_key:
            raise VoiceProviderError("VAPI_API_KEY nao configurada")
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    async def status(self) -> dict[str, Any]:
        missing: list[str] = []
        if not settings.vapi_api_key:
            missing.append("VAPI_API_KEY")
        if not settings.vapi_public_key:
            missing.append("VAPI_PUBLIC_KEY (Web SDK no browser — dashboard Vapi → API Keys → public)")
        return {
            "provider": "vapi",
            "configured": self._configured(),
            "available": self._configured(),
            "public_key": self.public_key,
            "assistant_id_inbound": self.assistant_id_inbound,
            "assistant_id_outbound": self.assistant_id_outbound,
            "missing": missing,
            "languages": SUPPORTED_LANGUAGES,
            "web_call": True,
            "note": (
                "Voz neural real via Vapi Web SDK (browser). "
                + ("Pronto." if self._configured() else "Faltam chaves — auto-fallback para browser.")
            ),
        }

    async def start_call(
        self,
        *,
        niche: str,
        business_name: str,
        direction: str,
        language: str,
        system_prompt: str,
        first_message: str,
        extra: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise VoiceProviderError("VAPI_API_KEY nao configurada")
        if not self.public_key:
            raise VoiceProviderError("VAPI_PUBLIC_KEY nao configurada (necessaria para web call no browser)")

        direction = (direction or "inbound").lower()
        voice = _voice_config_for(language)
        # Em modo multilingue, o transcriber deteta qualquer idioma ("multi").
        deepgram_lang = "multi" if settings.voice_multilingual else _deepgram_lang_for(language)

        assistant: dict[str, Any] = {
            "name": f"AutoPME Demo {direction.title()}",
            "firstMessage": first_message,
            "model": {
                "provider": "google",
                "model": "gemini-2.5-flash",
                "messages": [{"role": "system", "content": system_prompt}],
                "temperature": 0.55,
                "knowledge": None,
            },
            "voice": voice,
            "transcriber": {
                "provider": "deepgram",
                "model": "nova-3",
                "language": deepgram_lang,
                "endpointing": 250,
            },
            "silenceTimeoutSeconds": 30,
            "responseDelaySeconds": 0.4,
            "backgroundDenoisingEnabled": True,
            "firstMessageInterruptionsEnabled": True,
            "endCallPhrases": [
                "adeus", "ate logo", "ate breve", "xau",
                "goodbye", "bye", "adios", "ciao", "auf wiedersehen", "au revoir",
            ],
            "metadata": {
                "niche": niche,
                "business_name": business_name,
                "direction": direction,
                "language": language,
            },
        }

        logger.info(
            "Vapi assistant transiente preparado: niche=%s lang=%s direction=%s voice=%s/%s",
            niche,
            language,
            direction,
            voice.get("provider"),
            voice.get("voiceId"),
        )
        return {
            "provider": "vapi",
            "call_ref": None,
            "call_id": None,
            "public_key": self.public_key,
            "assistant": assistant,
            "direction": direction,
            "language": language,
            "voice": voice.get("voiceId"),
            "voice_provider": voice.get("provider"),
            "web_call": True,
        }

    async def end_call(self, call_ref: str) -> dict[str, Any]:
        if not self.api_key or not call_ref:
            return {"provider": "vapi", "ended": False, "reason": "no call_ref"}
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    f"{VAPI_API_URL}/call/{call_ref}/end",
                    headers=self._headers(),
                )
                ok = resp.status_code in (200, 204)
                return {"provider": "vapi", "ended": ok, "status_code": resp.status_code}
        except httpx.HTTPError as e:
            logger.warning("Vapi end_call: %s", e)
            return {"provider": "vapi", "ended": False, "error": str(e)}
