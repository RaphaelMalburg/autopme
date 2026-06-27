"""Agente conversacional de WhatsApp para a demo.

Transforma o numero de WhatsApp num assistente AI ao vivo do negocio carregado
na demo: quando alguem envia uma mensagem de texto, o backend responde com o
LLM usando o system prompt do cenario ativo + o historico da conversa daquele
remetente (persistido). E exatamente a promessa de venda do Notion: "o cliente
manda mensagem como sempre, a diferenca e que responde automaticamente".

Reutiliza:
- `app.scenarios.builder.build_scenario` (system prompt por nicho/idioma)
- `app.voice.chat.chat_turn` (turno LLM via OpenRouter)
- `app.storage.db` (cenario ativo + historico por remetente)
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from app.scenarios.builder import build_scenario
from app.scenarios.niches import get_niche_config
from app.storage import db
from app.voice.chat import chat_turn

logger = logging.getLogger(__name__)

ACTIVE_SCENARIO_KEY = "whatsapp_active_scenario"
_MAX_TURNS = 12  # mantem o historico curto (ultimas 12 mensagens)


def set_active_scenario(
    niche: str,
    business_name: str,
    language: str = "pt-PT",
    extra: Optional[dict[str, Any]] = None,
    free_context: str = "",
) -> dict[str, Any]:
    """Define qual negocio o agente WhatsApp representa (chamado ao carregar a demo)."""
    scenario = {
        "niche": niche,
        "business_name": business_name,
        "language": language or "pt-PT",
        "extra": extra or {},
        "free_context": free_context or "",
    }
    db.set_state(ACTIVE_SCENARIO_KEY, scenario)
    return scenario


def get_active_scenario() -> Optional[dict[str, Any]]:
    return db.get_state(ACTIVE_SCENARIO_KEY)


def _help_text(business_name: str) -> str:
    return (
        f"Ola! Sou o assistente virtual de {business_name}. "
        "Pode perguntar-me sobre horarios, servicos, precos ou marcacoes. "
        "Para enviar um documento (foto/PDF), basta anexa-lo aqui.\n\n"
        "Comandos: \"ajuda\" mostra esta mensagem; \"reiniciar\" limpa a conversa."
    )


def _parse_command(text: str) -> Optional[str]:
    t = (text or "").strip().lower()
    if t in ("ajuda", "help", "/ajuda", "/help", "menu"):
        return "help"
    if t in ("reiniciar", "reset", "/reset", "limpar", "recomecar"):
        return "reset"
    return None


async def handle_text_message(sender: str, text: str) -> str:
    """Processa uma mensagem de texto e devolve a resposta a enviar ao remetente."""
    active = get_active_scenario()
    business_name = (active or {}).get("business_name") or "o negocio"

    command = _parse_command(text)
    if command == "help":
        return _help_text(business_name)
    if command == "reset":
        db.wa_reset(sender)
        return f"Conversa reiniciada. {_help_text(business_name)}"

    # Sem cenario carregado na demo: resposta segura, sem inventar.
    if not active or get_niche_config(active.get("niche")) is None:
        return (
            "Obrigado pela sua mensagem! De momento o assistente nao esta configurado. "
            "Pode enviar uma foto ou PDF do seu documento que tratamos da extracao."
        )

    try:
        scenario = build_scenario(
            active["niche"],
            business_name,
            extra=active.get("extra") or None,
            language=active.get("language") or "pt-PT",
            free_context=active.get("free_context") or "",
        )
    except ValueError as e:
        logger.error("WhatsApp agent: cenario invalido: %s", e)
        return "Obrigado pela sua mensagem. Em breve a equipa entra em contacto."

    history = db.wa_get_history(sender)
    try:
        reply = await chat_turn(scenario["system_prompt"], history, text)
    except Exception as e:
        logger.error("WhatsApp agent LLM falhou para %s: %s", sender, e)
        return "Obrigado pela sua mensagem. Em breve a equipa entra em contacto para o ajudar."

    history = history + [
        {"role": "user", "content": text},
        {"role": "assistant", "content": reply},
    ]
    db.wa_set_history(sender, history[-_MAX_TURNS:])
    return reply
