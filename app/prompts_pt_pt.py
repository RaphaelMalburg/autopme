"""Alias de compatibilidade PT-PT para o modulo multi-idioma app/prompts.py.

As regras de fala e o build_system_prompt foram movidos para app/prompts.py com
suporte a varios idiomas. Este modulo re-exporta a funcao PT-PT para nao partir
importers existentes (app/voice/agent.py, app/voice/chat_router.py, builder).
Para multi-idioma, importar diretamente de app.prompts.
"""
from app.prompts import build_system_prompt as _build_system_prompt_multi

# Re-exporta constantes PT-PT para compatibilidade.
from app.prompts import (
    VOICE_BEHAVIOR_RULES as _VR,
    REPAIR_RULES as _RR,
    ACP_PATTERN as _ACP,
    LANGUAGE_AND_CLOSING_RULES as _LC,
    IDENTITY_LOCK,
)

VOICE_BEHAVIOR_RULES = _VR["pt-PT"]
REPAIR_RULES = _RR["pt-PT"]
ACP_PATTERN = _ACP["pt-PT"]
LANGUAGE_AND_CLOSING_RULES = _LC["pt-PT"]


def build_system_prompt(
    identity: str,
    knowledge_block: str,
    what_you_do: str,
    booking_flow: str = "",
    include_acp: bool = True,
) -> str:
    """Alias PT-PT do build_system_prompt multi-idioma."""
    return _build_system_prompt_multi(
        identity=identity,
        knowledge_block=knowledge_block,
        what_you_do=what_you_do,
        booking_flow=booking_flow,
        include_acp=include_acp,
        language="pt-PT",
    )
