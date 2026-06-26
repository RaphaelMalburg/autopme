"""Router FastAPI: POST /api/voice/call/start.

Cria uma room no LiveKit Server local, faz dispatch do agente 'autopme-voice'
para essa room (metadata JSON niche/business_name/direction) e devolve um token
JWT para o dashboard se juntar como participante.

direction=inbound : o dashboard e o 'chamador'; ao juntar-se, o agente e
  dispatchado e atende (abertura inbound).
direction=outbound: o agente e dispatchado e inicia (abertura outbound); o
  dashboard junta-se para 'atender'.

Integracao em app/main.py (orquestrador):
    from app.voice import voice_router
    app.include_router(voice_router)
"""
from __future__ import annotations

import json
import logging
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from livekit import api

from app.config import settings
from app.voice.agent import AGENT_NAME

logger = logging.getLogger(__name__)

voice_router = APIRouter(prefix="/api/voice", tags=["voice"])


class CallStartRequest(BaseModel):
    niche: str = Field(default="dental", description="Nicho (ex: dental, restaurant, spa...)")
    business_name: str = Field(default="Clinica Exemplo")
    direction: str = Field(default="inbound", description="inbound | outbound")


class CallStartResponse(BaseModel):
    room_name: str
    token: str
    ws_url: str


def _http_api_url() -> str:
    """livekit-api usa HTTP; settings.livekit_url usa ws://. Converter."""
    url = settings.livekit_url
    if url.startswith("ws://"):
        return "http://" + url[len("ws://"):]
    if url.startswith("wss://"):
        return "https://" + url[len("wss://"):]
    return url


@voice_router.post("/call/start", response_model=CallStartResponse)
async def call_start(req: CallStartRequest) -> CallStartResponse:
    direction = req.direction.lower()
    if direction not in ("inbound", "outbound"):
        raise HTTPException(
            status_code=400, detail="direction deve ser 'inbound' ou 'outbound'"
        )

    room_name = f"demo-{req.niche}-{uuid.uuid4().hex[:8]}"
    metadata = json.dumps(
        {
            "niche": req.niche,
            "business_name": req.business_name,
            "direction": direction,
        },
        ensure_ascii=False,
    )

    lkapi = api.LiveKitAPI(
        url=_http_api_url(),
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret,
    )
    try:
        try:
            await lkapi.room.create_room(
                api.CreateRoomRequest(name=room_name, empty_timeout=600)
            )
        except Exception as e:
            # room pode ja existir; nao e fatal para o dispatch.
            logger.warning("create_room (%s): %s", room_name, e)

        # dispatch explicito do agente nomeado para a room.
        await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=AGENT_NAME,
                room=room_name,
                metadata=metadata,
            )
        )

        # token para o dashboard se juntar como participante.
        token = (
            api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
            .with_identity("dashboard")
            .with_name("Dashboard")
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=True,
                    can_publish_data=True,
                    can_subscribe=True,
                )
            )
            .to_jwt()
        )
    except Exception as e:
        logger.error("call_start falhou: %s", e)
        raise HTTPException(status_code=502, detail=f"falha ao criar chamada: {e}") from e
    finally:
        await lkapi.aclose()

    return CallStartResponse(
        room_name=room_name, token=token, ws_url=settings.livekit_url
    )
