"""OpenRouter LLM: cliente streaming standalone + plugin livekit-agents.

Usa a chave OPENROUTER_API_KEY ja existente (ver app/config.py).
Endpoint: https://openrouter.ai/api/v1/chat/completions (compativel OpenAI),
com streaming SSE. NAO usa o plugin OpenAI do livekit-agents.

Duas camadas:
- chat_stream(): cliente standalone, testavel, sem dependencias do livekit.
  Devolve um AsyncIterator[str] com os deltas de texto (SSE).
- OpenRouterLLM(llm.LLM): plugin nativo para o AgentSession do livekit-agents,
  que envolve chat_stream() e emite llm.ChatChunk.

NOTA (demo): o plugin reencaminha apenas deltas de *conteudo* (texto). Reencaminhar
tool_calls em streaming (acumulacao por index) fica como TODO; o agente fecha a
chamada por instrucao (nao por tool endCall). Ver app/voice/agent.py.
"""
from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterError(Exception):
    """Erro de comunicacao com a OpenRouter."""


async def chat_stream(
    messages: list[dict[str, Any]],
    model: str | None = None,
    *,
    temperature: float = 0.55,
    max_tokens: int | None = None,
    timeout: float = 60.0,
) -> AsyncIterator[str]:
    """Streaming SSE de completions da OpenRouter.

    Cede (yield) os deltas de conteudo a medida que chegam. Formato OpenAI:
    cada linha de evento e `data: {"choices":[{"delta":{"content":"..."}}]}`.
    """
    model = model or settings.openrouter_default_model
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://autopme.demo",
        "X-Title": "AutoPME Demo Studio",
    }
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream(
            "POST", OPENROUTER_CHAT_URL, headers=headers, json=payload
        ) as resp:
            if resp.status_code >= 400:
                body = await resp.aread()
                raise OpenRouterError(
                    f"OpenRouter HTTP {resp.status_code}: "
                    f"{body.decode(errors='replace')[:500]}"
                )
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except json.JSONDecodeError:
                    continue
                choices = obj.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                content = delta.get("content")
                if content:
                    yield content


async def chat_once(
    messages: list[dict[str, Any]],
    model: str | None = None,
    *,
    temperature: float = 0.55,
    max_tokens: int | None = None,
    timeout: float = 60.0,
) -> str:
    """Chamada nao-streaming utilitaria: junta todos os deltas numa string."""
    chunks: list[str] = []
    async for delta in chat_stream(
        messages, model, temperature=temperature, max_tokens=max_tokens, timeout=timeout
    ):
        chunks.append(delta)
    return "".join(chunks)


# --- Plugin nativo livekit-agents ------------------------------------------------

try:
    from livekit.agents.llm import ChatChunk, ChoiceDelta, LLM, LLMStream
    from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS, NOT_GIVEN

    _LIVEKIT_AVAILABLE = True
except ImportError:  # livekit-agents nao instalado (validacao sintatica)
    _LIVEKIT_AVAILABLE = False
    LLM = LLMStream = ChatChunk = ChoiceDelta = None  # type: ignore[assignment]


def _chat_ctx_to_messages(chat_ctx: Any) -> list[dict[str, Any]]:
    """Converte um llm.ChatContext numa lista de mensagens OpenRouter/OpenAI."""
    messages: list[dict[str, Any]] = []
    for item in getattr(chat_ctx, "items", []):
        role_raw = getattr(item, "role", "user")
        role = getattr(role_raw, "value", role_raw)
        role = str(role).strip().lower()
        if role not in ("system", "user", "assistant", "tool"):
            role = "user"
        text = getattr(item, "text_content", None)
        if not text:
            content = getattr(item, "content", "")
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                text = " ".join(
                    p if isinstance(p, str) else getattr(p, "text", "")
                    for p in content
                )
            else:
                text = str(content) if content else ""
        text = (text or "").strip()
        if text:
            messages.append({"role": role, "content": text})
    return messages


if _LIVEKIT_AVAILABLE:

    class _OpenRouterLLMStream(LLMStream):  # type: ignore[misc]
        """Stream de chat que poe deltas da OpenRouter no canal de eventos."""

        def __init__(
            self,
            llm_plugin: "OpenRouterLLM",
            *,
            chat_ctx: Any,
            tools: list,
            conn_options: Any,
            model: str,
            temperature: float,
        ) -> None:
            super().__init__(
                llm_plugin, chat_ctx=chat_ctx, tools=tools, conn_options=conn_options
            )
            self._model = model
            self._temperature = temperature

        async def _run(self) -> None:
            import uuid

            request_id = uuid.uuid4().hex
            try:
                messages = _chat_ctx_to_messages(self._chat_ctx)
                async for delta in chat_stream(messages, self._model, temperature=self._temperature):
                    self._event_ch.send_nowait(
                        ChatChunk(
                            id=request_id,
                            delta=ChoiceDelta(content=delta),
                        )
                    )
            except Exception as e:  # repassado para o retry/error do LLMStream
                logger.error("OpenRouterLLM stream error: %s", e)
                raise

    class OpenRouterLLM(LLM):  # type: ignore[misc]
        """Plugin LLM que chama a OpenRouter via httpx (streaming SSE)."""

        def __init__(
            self, *, model: str | None = None, temperature: float = 0.55
        ) -> None:
            super().__init__()
            self._model = model or settings.openrouter_default_model
            self._temperature = temperature

        @property
        def model(self) -> str:
            return self._model

        @property
        def provider(self) -> str:
            return "openrouter"

        def chat(
            self,
            *,
            chat_ctx: Any,
            tools: list | None = None,
            conn_options: Any = DEFAULT_API_CONNECT_OPTIONS,
            parallel_tool_calls: Any = NOT_GIVEN,
            tool_choice: Any = NOT_GIVEN,
            extra_kwargs: Any = NOT_GIVEN,
        ) -> "_OpenRouterLLMStream":
            return _OpenRouterLLMStream(
                self,
                chat_ctx=chat_ctx,
                tools=tools or [],
                conn_options=conn_options,
                model=self._model,
                temperature=self._temperature,
            )

else:

    class OpenRouterLLM:  # type: ignore[no-redef]
        """Stub quando livekit-agents nao esta instalado."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError(
                "livekit-agents nao instalado; instale-o para usar OpenRouterLLM"
            )
