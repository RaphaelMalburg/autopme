"""Scenario builder: composes a full demo scenario for a given niche.

Produces the system prompt (via app.prompts_pt_pt.build_system_prompt), the opening
messages, the capture fields, the booking flow and the knowledge block. The knowledge
block is built from the caller-provided `extra` (opening_hours, services, prices,
notes); when `extra` is empty, a realistic per-niche example is used so the demo can
start without any input.

This module does NOT load app.config.settings, so it can be imported and exercised
without a .env file (used by the smoke test).
"""
from __future__ import annotations

from typing import Any

from app.prompts_pt_pt import build_system_prompt

from .niches import NICHE_CONFIG, get_niche_config


def _format_knowledge_block(extra: dict[str, Any] | None, example: str) -> str:
    """Build a PT-PT knowledge block from `extra`, falling back to `example`."""
    if not extra:
        return example
    opening_hours = (extra.get("opening_hours") or "").strip()
    services = (extra.get("services") or "").strip()
    prices = (extra.get("prices") or "").strip()
    notes = (extra.get("notes") or "").strip()
    if not (opening_hours or services or prices or notes):
        return example
    lines = [
        "=== CONHECIMENTO DO NEGÓCIO ===",
        "Usa APENAS estas informações para responder. Se a pergunta não está coberta aqui, "
        "diz que vais verificar e alguém da equipa entrará em contacto.",
        "",
    ]
    if opening_hours:
        lines.append(f"Horários: {opening_hours}")
    if services:
        lines.append(f"Serviços: {services}")
    if prices:
        lines.append(f"Preços: {prices}")
    if notes:
        lines.append(f"Notas: {notes}")
    lines.append("=== FIM DO CONHECIMENTO ===")
    return "\n".join(lines)


def build_scenario(
    niche: str,
    business_name: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a complete demo scenario for a niche.

    Args:
        niche: niche id (one of NICHE_CONFIG keys).
        business_name: the business name to inject into the identity and opening lines.
        extra: optional dict with opening_hours / services / prices / notes. When empty
            or absent, a realistic per-niche example knowledge block is used.

    Returns:
        dict with keys: system_prompt, first_message_inbound, first_message_outbound,
        capture_fields, booking_flow, knowledge_block.

    Raises:
        ValueError: if `niche` is not a known niche id.
    """
    cfg = get_niche_config(niche)
    if cfg is None:
        raise ValueError(
            f"Nicho desconhecido: {niche!r}. Válidos: {list(NICHE_CONFIG.keys())}"
        )

    knowledge_block = _format_knowledge_block(extra, cfg["example_knowledge"])

    role = cfg["role"]
    identity = (
        f"Tu és a {role} de {business_name}. Falas sempre em português europeu (de Portugal) "
        "e comportas-te como uma pessoa real que trabalha no negócio."
    )

    system_prompt = build_system_prompt(
        identity=identity,
        knowledge_block=knowledge_block,
        what_you_do=cfg["what_you_do"],
        booking_flow=cfg["booking_flow"],
        include_acp=True,
    )

    return {
        "system_prompt": system_prompt,
        "first_message_inbound": cfg["first_message_inbound"].format(business_name=business_name),
        "first_message_outbound": cfg["first_message_outbound"].format(business_name=business_name),
        "capture_fields": dict(cfg["capture_fields"]),
        "booking_flow": cfg["booking_flow"],
        "knowledge_block": knowledge_block,
    }
