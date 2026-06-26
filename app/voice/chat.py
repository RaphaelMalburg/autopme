"""Chat de voz simulado (LLM OpenRouter + PT-PT) para o dashboard.

Permite simular uma chamada de voz no dashboard SEM LiveKit/WebRTC: o backend
corre um turno de conversacao com o system prompt do cenario + o historico e
devolve a resposta do agente em PT-PT. O dashboard usa a Web Speech API do
browser para microfone (STT) e sintese (TTS), dando a ilusao de uma chamada.

So depende de httpx (via app.whatsapp.openrouter_vision). NAO importa livekit.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.whatsapp.openrouter_vision import openrouter_vision, OpenRouterVisionError

logger = logging.getLogger(__name__)


async def chat_turn(
    system_prompt: str,
    history: list[dict] | None,
    user_message: Optional[str] = None,
) -> str:
    """Corre um turno de conversacao com o LLM e devolve a resposta do agente.

    ``history`` e uma lista de {role: "user"|"assistant", content: str}. Se
    ``user_message`` for fornecido, e adicionado como a ultima mensagem do
    utilizador antes da chamada.
    """
    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    for h in history or []:
        role = h.get("role")
        content = h.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    if user_message:
        messages.append({"role": "user", "content": user_message})

    try:
        reply = await openrouter_vision.call_llm(
            messages, temperature=0.7, max_tokens=400
        )
    except OpenRouterVisionError as e:
        logger.error("voice chat_turn error: %s", e)
        raise
    return (reply or "").strip()
