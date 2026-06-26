"""Provider browser — fallback simulado (LLM + Web Speech API).

Usado quando o Vapi nao tem config (sem VAPI_PUBLIC_KEY) ou VOICE_PROVIDER=browser.
A chamada "decorre" no browser: o backend devolve o provider=browser e o dashboard
usa /api/voice/chat (LLM) + Web Speech API (speechSynthesis/SpeechRecognition).
Este provider nao cria nada no servidor; so sinaliza o modo.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from app.voice.providers.base import VoiceProvider

logger = logging.getLogger(__name__)


SUPPORTED_LANGUAGES = ["pt-PT", "pt-BR", "en-US", "en-GB", "es-ES", "fr-FR", "de-DE", "it-IT"]


class BrowserVoiceProvider(VoiceProvider):
    name = "browser"

    async def status(self) -> dict[str, Any]:
        return {
            "provider": "browser",
            "configured": True,
            "available": True,
            "missing": [],
            "languages": SUPPORTED_LANGUAGES,
            "web_call": False,
            "note": (
                "Voz simulada no browser (LLM + Web Speech API). "
                "Sem Vapi: funciona sempre, mas a voz e a do sistema operativo "
                "(menos natural). Para voz neural Azure, configurar Vapi (ver /api/voice/providers)."
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
        # O browser inicia a "chamada" chamando /api/voice/chat (abertura) e usando
        # a Web Speech API. Aqui so devolvemos o modo + a primeira mensagem para o
        # dashboard comecar imediatamente.
        direction = (direction or "inbound").lower()
        logger.info("Browser voice start: niche=%s lang=%s direction=%s", niche, language, direction)
        return {
            "provider": "browser",
            "call_ref": None,
            "call_id": None,
            "direction": direction,
            "language": language,
            "first_message": first_message,
            "system_prompt": system_prompt,
            "web_call": False,
        }

    async def end_call(self, call_ref: str) -> dict[str, Any]:
        return {"provider": "browser", "ended": True}
