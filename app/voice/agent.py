"""Agente de voz LiveKit para a demo AutoPME.

Pipeline local: VAD Silero + STT faster-whisper + LLM OpenRouter + TTS Piper.
O agente junta-se a uma room criada pelo router POST /api/voice/call/start e
atende (inbound) ou inicia (outbound). Instrucoes e primeira mensagem vem de
app.scenarios.builder.build_scenario(niche, business_name), com fallback inline
PT-PT se o modulo scenarios ainda nao estiver fundido.

Transcript live: publica JSON {"type":"transcript","role","content","ts"} no
data channel da room (subscrito pelo dashboard via LiveKit Web SDK).

Como correr (apos instalar deps + arrancar LiveKit Server em Docker):
    python -m app.voice.main download-files   # 1x: descarrega Silero VAD
    python -m app.voice.main                  # arranca o worker (equivalente a 'start')

Runtime deps (instalar; validacao runtime pelo orquestrador):
    pip install livekit-agents livekit-api httpx faster-whisper numpy
    piper + modelo pt-PT  (ver app/voice/tts_piper.py)
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    room_io,
)
from livekit.agents.stt import StreamAdapter
try:
    from livekit.agents.voice import ConversationItemAddedEvent
except ImportError:  # fallback caso nao seja re-exportado do package voice
    from livekit.agents.voice.events import ConversationItemAddedEvent  # type: ignore
from livekit.plugins import silero

from app.config import settings
from app.voice.llm_openrouter import OpenRouterLLM
from app.voice.stt_whisper import WhisperSTT
from app.voice.tts_piper import PiperTTS

logger = logging.getLogger("autopme-voice")

AGENT_NAME = "autopme-voice"

server = AgentServer()


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


# --- Cenario (instrucoes + primeira mensagem) -----------------------------------

try:
    from app.scenarios.builder import build_scenario as _build_scenario  # type: ignore

    _SCENARIOS_AVAILABLE = True
except Exception:
    _SCENARIOS_AVAILABLE = False
    _build_scenario = None  # type: ignore

# Fallback inline PT-PT quando scenarios ainda nao esta fundido.
_FALLBACK_IDENTITY = (
    "Es a recepcionista virtual de {business_name}. Comporta-te como uma pessoa real "
    "que trabalha no negocio — nunca digas que es uma IA, um assistente virtual ou um "
    "bot. Falas sempre em portugues europeu (de Portugal)."
)
_FALLBACK_KNOWLEDGE = (
    "=== CONHECIMENTO DO NEGOCIO ===\n"
    "Usa APENAS as informacoes fornecidas pelo dashboard. Se nao souberes algo, "
    "diz que vais confirmar com a equipa e alguem ligara de volta.\n"
    "=== FIM DO CONHECIMENTO ==="
)
_FALLBACK_WHAT_YOU_DO = (
    "1. Responder perguntas sobre o negocio (horarios, servicos, precos, localizacao).\n"
    "2. Marcar / confirmar marcacoes: recolhe nome, telefone, data/hora e motivo, "
    "um dado de cada vez.\n"
    "3. Se o assunto for fora do teu alcance, diz que vais passar a mensagem a alguem "
    "da equipa."
)
_FALLBACK_BOOKING_FLOW = (
    "## FLUXO DE MARCACAO\n"
    "Passo 1: \"Claro, posso ajudar com isso. Qual e o seu nome?\"\n"
    "Passo 2: \"E um numero de telefone para contacto?\"\n"
    "Passo 3: \"Que dia e hora prefere?\"\n"
    "Passo 4: \"E qual o motivo?\"\n"
    "Passo 5: Confirma tudo e pergunta se pode ajudar com mais alguma coisa.\n"
    "Passo 6: Se a pessoa disser que nao, despede-te e encerra a chamada.\n"
    "Recolhe um dado de cada vez. Nao peças tudo ao mesmo tempo."
)


def _build_scenario_fallback(niche: str, business_name: str) -> dict:
    from app.prompts_pt_pt import build_system_prompt

    identity = _FALLBACK_IDENTITY.format(business_name=business_name)
    system_prompt = build_system_prompt(
        identity=identity,
        knowledge_block=_FALLBACK_KNOWLEDGE,
        what_you_do=_FALLBACK_WHAT_YOU_DO,
        booking_flow=_FALLBACK_BOOKING_FLOW,
    )
    return {
        "system_prompt": system_prompt,
        "first_message_inbound": f"Ola, {business_name}, em que posso ajudar?",
        "first_message_outbound": (
            f"Ola, falo de {business_name}, estou a ligar para confirmar a sua marcacao."
        ),
    }


def _resolve_scenario(niche: str, business_name: str) -> dict:
    if _SCENARIOS_AVAILABLE and _build_scenario is not None:
        try:
            return _build_scenario(niche, business_name)
        except Exception as e:
            logger.warning("build_scenario falhou (%s); a usar fallback inline", e)
    # TODO(integracao): garantir que app.scenarios.builder.build_scenario esta fundido.
    return _build_scenario_fallback(niche, business_name)


def _parse_metadata(ctx: JobContext) -> dict:
    """Extrai niche/business_name/direction do dispatch metadata (JSON)."""
    raw = ""
    job = getattr(ctx, "job", None)
    if job is not None:
        raw = getattr(job, "metadata", "") or ""
    if not raw and hasattr(ctx.room, "attributes"):
        raw = ctx.room.attributes.get("autopme.metadata", "") or ""
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        data = {}
    data.setdefault("niche", settings.default_niche)
    data.setdefault("business_name", "o negocio")
    data.setdefault("direction", "inbound")
    return data


class RecepcionistaAgent(Agent):
    def __init__(self, instructions: str, first_message: str) -> None:
        super().__init__(instructions=instructions)
        self._first_message = first_message

    async def on_enter(self) -> None:
        # Abertura controlada: o LLM diz exatamente a primeira mensagem.
        self.session.generate_reply(
            instructions=(
                f"Diz exatamente, em portugues europeu, esta frase de abertura e nada "
                f'mais: "{self._first_message}"'
            )
        )


async def _publish_transcript(ctx: JobContext, payload: bytes) -> None:
    """Publica JSON no data channel da room (transcript live para o dashboard)."""
    lp = ctx.room.local_participant
    await lp.publish_data(payload, reliable=True)


@server.rtc_session(agent_name=AGENT_NAME)
async def entrypoint(ctx: JobContext) -> None:
    ctx.log_context_fields = {"room": ctx.room.name}

    meta = _parse_metadata(ctx)
    niche: str = meta["niche"]
    business_name: str = meta["business_name"]
    direction: str = meta["direction"]

    scenario = _resolve_scenario(niche, business_name)
    instructions = scenario.get("system_prompt") or scenario.get("instructions", "")
    if direction == "outbound":
        first_message = scenario.get("first_message_outbound") or scenario.get(
            "first_message_inbound", f"Ola, falo de {business_name}."
        )
    else:
        first_message = scenario.get("first_message_inbound") or (
            f"Ola, {business_name}, em que posso ajudar?"
        )

    vad = ctx.proc.userdata["vad"]
    # STT batch envolvido com StreamAdapter para streaming via VAD.
    stt = StreamAdapter(stt=WhisperSTT(), vad=vad)
    llm = OpenRouterLLM()
    tts = PiperTTS()

    session = AgentSession(stt=stt, llm=llm, tts=tts, vad=vad)

    @session.on("conversation_item_added")
    def _on_item(ev: ConversationItemAddedEvent) -> None:
        try:
            item = getattr(ev, "item", ev)
            role_raw = getattr(item, "role", "assistant")
            role_val = getattr(role_raw, "value", role_raw)
            role_str = str(role_val).strip().lower()
            if role_str == "assistant":
                role = "agent"
            elif role_str == "user":
                role = "user"
            else:
                return  # system/tool: nao publicar como transcript
            content = getattr(item, "text_content", None)
            if not content:
                c = getattr(item, "content", "")
                if isinstance(c, str):
                    content = c
                elif isinstance(c, list):
                    content = " ".join(
                        p if isinstance(p, str) else getattr(p, "text", "") for p in c
                    )
                else:
                    content = str(c) if c else ""
            content = (content or "").strip()
            if not content:
                return
            payload = json.dumps(
                {"type": "transcript", "role": role, "content": content, "ts": time.time()},
                ensure_ascii=False,
            ).encode("utf-8")
            asyncio.ensure_future(_publish_transcript(ctx, payload))
        except Exception as e:
            logger.warning("transcript publish falhou: %s", e)

    await session.start(
        agent=RecepcionistaAgent(instructions=instructions, first_message=first_message),
        room=ctx.room,
        room_options=room_io.RoomOptions(),
    )
