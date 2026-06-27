"""Provider Vapi — voz neural Azure real via web calls.

Usa as chaves Vapi JA EXISTENTES (agente-consultoria/.env). Para a demo
presencial usa *web call* (transport: web): chamada no browser via Vapi Web SDK,
com pipeline de voz real (Azure Neural TTS + Deepgram STT + LLM), sem telefonar.

Modular: para remover o Vapi depois, mudar VOICE_PROVIDER=browser — o router
delega no provider browser (LLM + Web Speech API). Sem chaves Vapi configuradas,
o factory auto-fallback para browser.

API: POST https://api.vapi.ai/call/web com assistant transiente + assistantOverrides
a injetar o system_prompt dinamico (por nicho/idioma), a voz Azure mapeada por
idioma e o transcriber Deepgram.
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


def _voice_for(language: str) -> str:
    return AZURE_VOICE_BY_LANG.get(language) or settings.vapi_voice_id or "pt-PT-RaquelNeural"


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
                "Voz neural Azure real via Vapi web call (browser). "
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
        voice_id = _voice_for(language)
        deepgram_lang = _deepgram_lang_for(language)

        # Assistant transiente com o system_prompt dinamico injetado via overrides.
        # Reusa o assistant salvo (inbound/outbound) se existir, senao transient total.
        payload: dict[str, Any] = {
            "transport": {"type": "web"},
            "assistantOverrides": {
                "firstMessage": first_message,
                "model": {
                    "provider": "google",
                    "model": "gemini-2.5-flash",
                    "messages": [{"role": "system", "content": system_prompt}],
                    "temperature": 0.55,
                    "knowledge": None,
                },
                "voice": {
                    "provider": self.voice_provider,
                    "voiceId": voice_id,
                },
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
            },
            "metadata": {
                "niche": niche,
                "business_name": business_name,
                "direction": direction,
                "language": language,
            },
        }
        # Preferir assistantId salvo (inbound/outbound) para herdar config base.
        if direction == "outbound" and self.assistant_id_outbound:
            payload["assistantId"] = self.assistant_id_outbound
        elif direction == "inbound" and self.assistant_id_inbound:
            payload["assistantId"] = self.assistant_id_inbound

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{VAPI_API_URL}/call/web",
                    headers=self._headers(),
                    json=payload,
                )
                if resp.status_code not in (200, 201):
                    raise VoiceProviderError(f"Vapi /call/web HTTP {resp.status_code}: {resp.text[:300]}")
                data = resp.json()
        except httpx.HTTPError as e:
            raise VoiceProviderError(f"Vapi rede: {e}") from e

        call_id = data.get("id") or data.get("callId")
        logger.info("Vapi web call criada: id=%s niche=%s lang=%s", call_id, niche, language)
        return {
            "provider": "vapi",
            "call_ref": call_id,
            "call_id": call_id,
            "public_key": self.public_key,
            "assistant_id": payload.get("assistantId"),
            "direction": direction,
            "language": language,
            "voice": voice_id,
            "web_call": True,
            "raw": data,
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
