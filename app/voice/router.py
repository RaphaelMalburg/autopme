"""Router de voz modular — delega no provider ativo (vapi | browser).

Nao depende de livekit. POST /api/voice/call/start constroi o cenario por
niche/idioma e inicia a chamada no provider ativo. GET /api/voice/providers
expoe o estado (qual provider, o que falta). POST /api/voice/call/end termina.

Montado em app/main.py:
    from app.voice import voice_router
    app.include_router(voice_router)
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.scenarios.builder import build_scenario
from app.scenarios.niches import get_niche_config
from app.voice.providers import get_voice_provider, VoiceProviderError

logger = logging.getLogger(__name__)

voice_router = APIRouter(prefix="/api/voice", tags=["voice"])


class CallStartRequest(BaseModel):
    niche: str = Field(default="dental")
    business_name: str = Field(default="Negocio")
    direction: str = Field(default="inbound", description="inbound | outbound")
    language: str = Field(default="", description="idioma (pt-PT, en-US, ...). Vazio = default.")
    extra: Optional[dict[str, Any]] = None
    free_context: str = Field(default="", description="bloco de texto livre para o system prompt")


@voice_router.get("/providers")
async def providers_status() -> dict[str, Any]:
    """Estado do(s) provider(s) de voz + qual esta ativo + o que falta."""
    provider = get_voice_provider()
    st = await provider.status()
    st["requested"] = (settings.voice_provider or "vapi").lower()
    return st


@voice_router.post("/call/start")
async def call_start(req: CallStartRequest) -> dict[str, Any]:
    direction = (req.direction or "inbound").lower()
    if direction not in ("inbound", "outbound"):
        raise HTTPException(status_code=400, detail="direction deve ser 'inbound' ou 'outbound'")
    if get_niche_config(req.niche) is None:
        raise HTTPException(status_code=400, detail=f"Nicho desconhecido: {req.niche}")

    language = (req.language or settings.voice_default_language or "pt-PT").strip()

    try:
        scenario = build_scenario(
            req.niche, req.business_name, extra=req.extra, language=language,
            free_context=req.free_context,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    system_prompt = scenario["system_prompt"]
    first_message = (
        scenario["first_message_outbound"] if direction == "outbound"
        else scenario["first_message_inbound"]
    )

    provider = get_voice_provider()
    try:
        result = await provider.start_call(
            niche=req.niche,
            business_name=req.business_name,
            direction=direction,
            language=language,
            system_prompt=system_prompt,
            first_message=first_message,
            extra=req.extra,
        )
    except VoiceProviderError as e:
        logger.error("call_start provider %s falhou: %s", provider.name, e)
        raise HTTPException(status_code=502, detail=f"falha ao iniciar chamada: {e}") from e

    result["niche"] = req.niche
    result["business_name"] = req.business_name
    result["direction"] = direction
    result["language"] = language
    result["first_message"] = first_message
    return result


class CallEndRequest(BaseModel):
    call_ref: str = ""


@voice_router.post("/call/end")
async def call_end(req: CallEndRequest) -> dict[str, Any]:
    """Termina uma chamada em curso (best-effort)."""
    provider = get_voice_provider()
    return await provider.end_call(req.call_ref)
