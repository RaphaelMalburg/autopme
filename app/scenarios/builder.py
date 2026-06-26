"""Scenario builder: composes a full demo scenario for a given niche (multi-idioma).

Produces the system prompt (via app.prompts.build_system_prompt), the opening
messages (per language), the capture fields, the booking flow and the knowledge
block. The knowledge block is built from the caller-provided `extra` (opening_hours,
services, prices, notes) plus an optional `free_context` text block; when `extra`
is empty, a realistic per-niche example is used so the demo can start without input.

Incorporates per-niche `niche_expertise` (industry knowledge, common questions,
objections, upsell, tone) into the system prompt to make the agent domain-savvy.

This module does NOT load app.config.settings, so it can be imported and exercised
without a .env file (used by the smoke test).
"""
from __future__ import annotations

from typing import Any

from app.prompts import build_system_prompt

from .niches import NICHE_CONFIG, get_niche_config


def _format_knowledge_block(
    extra: dict[str, Any] | None,
    example: str,
    free_context: str = "",
    language: str = "pt-PT",
) -> str:
    """Build a knowledge block from `extra` + `free_context`, falling back to `example`."""
    has_extra = False
    lines = [
        "=== KNOWLEDGE / CONHECIMENTO ===",
        "Use ONLY this information to answer. If a question isn't covered here, "
        "say you'll check and someone from the team will get in touch.",
        "",
    ]
    if extra:
        opening_hours = (extra.get("opening_hours") or "").strip()
        services = (extra.get("services") or "").strip()
        prices = (extra.get("prices") or "").strip()
        notes = (extra.get("notes") or "").strip()
        if opening_hours or services or prices or notes:
            has_extra = True
            if opening_hours:
                lines.append(f"Hours / Horários: {opening_hours}")
            if services:
                lines.append(f"Services / Serviços: {services}")
            if prices:
                lines.append(f"Prices / Preços: {prices}")
            if notes:
                lines.append(f"Notes / Notas: {notes}")
    if free_context and free_context.strip():
        has_extra = True
        lines.append("")
        lines.append("--- Additional context / Contexto adicional (consultor) ---")
        lines.append(free_context.strip())
    lines.append("=== END / FIM ===")
    return "\n".join(lines) if has_extra else example


def _first_messages(cfg: dict[str, Any], language: str) -> dict[str, str]:
    """Resolve first messages for a language, with PT-PT fallback.

    Supports both the new `first_messages` dict and the legacy
    `first_message_inbound`/`first_message_outbound` strings (auto-wrapped).
    """
    fm = cfg.get("first_messages")
    if isinstance(fm, dict) and fm:
        lang = language if language in fm else "pt-PT"
        entry = fm.get(lang) or fm.get("pt-PT") or {}
        return {"inbound": entry.get("inbound", ""), "outbound": entry.get("outbound", "")}
    # legacy fallback
    return {
        "inbound": cfg.get("first_message_inbound", "Olá, {business_name}, em que posso ajudar?"),
        "outbound": cfg.get("first_message_outbound", "Olá, falo de {business_name}, estou a ligar para confirmar."),
    }


def _identity(role: str, business_name: str, language: str) -> str:
    if language.startswith("en"):
        return (
            f"You are the {role} at {business_name}. You always speak English and behave "
            "like a real person who works at the business."
        )
    if language.startswith("es"):
        return (
            f"Eres el/la {role} de {business_name}. Hablas siempre espanol y te comportas "
            "como una persona real que trabaja en el negocio."
        )
    if language.startswith("fr"):
        return (
            f"Tu es le/la {role} de {business_name}. Tu parles toujours francais et te "
            "comportes comme une personne reelle qui travaille dans l'entreprise."
        )
    if language.startswith("de"):
        return (
            f"Du bist der/die {role} bei {business_name}. Du sprichst immer Deutsch und "
            "verhaltest dich wie eine echte Person, die im Geschaft arbeitet."
        )
    if language.startswith("it"):
        return (
            f"Sei il/la {role} di {business_name}. Parli sempre italiano e ti comporti "
            "come una persona reale che lavora nell'attivita."
        )
    # pt-PT / pt-BR default
    return (
        f"Tu és a {role} de {business_name}. Falas sempre em portugues europeu (de Portugal) "
        "e comportas-te como uma pessoa real que trabalha no negocio."
    )


def build_scenario(
    niche: str,
    business_name: str,
    extra: dict[str, Any] | None = None,
    language: str = "pt-PT",
    free_context: str = "",
) -> dict[str, Any]:
    """Build a complete demo scenario for a niche in a given language.

    Args:
        niche: niche id (one of NICHE_CONFIG keys).
        business_name: the business name to inject into identity and opening lines.
        extra: optional dict with opening_hours / services / prices / notes. When empty
            or absent, a realistic per-niche example knowledge block is used.
        language: BCP-47 language tag (pt-PT, en-US, es-ES, fr-FR, de-DE, it-IT).
        free_context: optional free-text block added to the knowledge base (consultor notes).

    Returns:
        dict with keys: system_prompt, first_message_inbound, first_message_outbound,
        first_messages, capture_fields, booking_flow, knowledge_block, language, niche_expertise.

    Raises:
        ValueError: if `niche` is not a known niche id.
    """
    cfg = get_niche_config(niche)
    if cfg is None:
        raise ValueError(
            f"Nicho desconhecido: {niche!r}. Válidos: {list(NICHE_CONFIG.keys())}"
        )

    knowledge_block = _format_knowledge_block(
        extra, cfg["example_knowledge"], free_context=free_context, language=language
    )

    role = cfg["role"]
    identity = _identity(role, business_name, language)
    niche_expertise = cfg.get("niche_expertise", "")

    system_prompt = build_system_prompt(
        identity=identity,
        knowledge_block=knowledge_block,
        what_you_do=cfg["what_you_do"],
        booking_flow=cfg["booking_flow"],
        include_acp=True,
        language=language,
        niche_expertise=niche_expertise,
    )

    fm = _first_messages(cfg, language)
    inbound = fm["inbound"].format(business_name=business_name)
    outbound = fm["outbound"].format(business_name=business_name)

    return {
        "system_prompt": system_prompt,
        "first_message_inbound": inbound,
        "first_message_outbound": outbound,
        "first_messages": {"inbound": inbound, "outbound": outbound},
        "capture_fields": dict(cfg["capture_fields"]),
        "booking_flow": cfg["booking_flow"],
        "knowledge_block": knowledge_block,
        "language": language,
        "niche_expertise": niche_expertise,
    }
