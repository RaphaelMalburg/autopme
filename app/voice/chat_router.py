"""Router FastAPI leve: POST /api/voice/chat (chamada de voz simulada).

NAO depende de livekit — so de httpx (OpenRouter) + app.scenarios. Montado em
app/main.py FORA do try/except do livekit, para a chamada simulada funcionar
mesmo sem livekit-api instalado (ex.: imagem slim de deploy).

Fluxo:
- Recebe {niche, business_name, direction, history, user_message?}.
- Constroi o cenario (system_prompt + first_message_inbound/outbound).
- Se sem historico e sem user_message -> devolve a abertura (inbound/outbound).
- Caso contrario -> corre um turno LLM com o system_prompt + historico + user_message.
- Devolve {reply, history (atualizado), direction}.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.scenarios.builder import build_scenario
from app.scenarios.niches import get_niche_config
from app.voice.chat import chat_turn

logger = logging.getLogger(__name__)

chat_router = APIRouter(prefix="/api/voice", tags=["voice"])


class ChatMessage(BaseModel):
    role: str = Field(..., description="user | assistant")
    content: str


class VoiceChatRequest(BaseModel):
    niche: str = Field(default="dental")
    business_name: str = Field(default="Negocio")
    direction: str = Field(default="inbound", description="inbound | outbound")
    history: list[ChatMessage] = Field(default_factory=list)
    user_message: Optional[str] = None


@chat_router.post("/chat")
async def voice_chat(req: VoiceChatRequest) -> dict[str, Any]:
    """Simula um turno de chamada de voz (LLM PT-PT) ou devolve a abertura."""
    direction = (req.direction or "inbound").lower()
    if direction not in ("inbound", "outbound"):
        raise HTTPException(status_code=400, detail="direction deve ser 'inbound' ou 'outbound'")
    if get_niche_config(req.niche) is None:
        raise HTTPException(status_code=400, detail=f"Nicho desconhecido: {req.niche}")

    try:
        scenario = build_scenario(req.niche, req.business_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    system_prompt = scenario["system_prompt"]
    history_raw = [m.model_dump() for m in req.history]
    user_message = (req.user_message or "").strip() or None

    # Abertura: sem historico e sem user_message -> o agente fala primeiro.
    if not history_raw and not user_message:
        opening = (
            scenario["first_message_outbound"] if direction == "outbound"
            else scenario["first_message_inbound"]
        )
        return {
            "reply": opening,
            "history": [{"role": "assistant", "content": opening}],
            "direction": direction,
            "opening": True,
        }

    try:
        reply = await chat_turn(system_prompt, history_raw, user_message)
    except Exception as e:
        logger.error("voice_chat falhou: %s", e)
        raise HTTPException(status_code=502, detail=f"falha no agente: {e}") from e

    # Atualizar historico: acrescentar a mensagem do utilizador (se houver) e a resposta.
    updated = list(history_raw)
    if user_message:
        updated.append({"role": "user", "content": user_message})
    updated.append({"role": "assistant", "content": reply})

    return {
        "reply": reply,
        "history": updated,
        "direction": direction,
        "opening": False,
    }
