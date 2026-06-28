"""FastAPI router for scenario building endpoints.

- GET  /api/scenarios/niches -> list of niche summaries (id, label, role, booking_term).
- POST /api/scenarios/build  -> build a full scenario for a niche.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .builder import build_scenario
from .niches import NICHE_CONFIG, get_niche_config, list_niches
from .presets import get_preset, list_presets

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


class BuildExtra(BaseModel):
    """Optional business knowledge provided by the dashboard."""

    opening_hours: str = ""
    services: str = ""
    prices: str = ""
    notes: str = ""


class BuildRequest(BaseModel):
    niche: str
    business_name: str
    extra: BuildExtra | None = None
    language: str = "pt-PT"
    free_context: str = ""


@router.get("/niches")
async def get_niches_endpoint() -> list[dict[str, str]]:
    """List the available niches for the dashboard selector."""
    return list_niches()


@router.get("/presets")
async def list_presets_endpoint() -> list[dict[str, str]]:
    """Lista os exemplos de negocio prontos a carregar (1 por nicho)."""
    return list_presets()


@router.get("/presets/{niche}")
async def get_preset_endpoint(niche: str) -> dict[str, Any]:
    """Devolve o preset de contexto de um nicho (para preencher a demo)."""
    preset = get_preset(niche)
    if preset is None:
        raise HTTPException(status_code=404, detail=f"Sem preset para o nicho: {niche}")
    return preset


@router.post("/build")
async def build_endpoint(req: BuildRequest) -> dict[str, Any]:
    """Build a full scenario (system prompt, opening messages, capture fields, ...)."""
    if get_niche_config(req.niche) is None:
        raise HTTPException(
            status_code=400,
            detail=f"Nicho desconhecido: {req.niche}. Válidos: {list(NICHE_CONFIG.keys())}",
        )
    extra = req.extra.model_dump() if req.extra else None
    return build_scenario(
        req.niche, req.business_name, extra=extra,
        language=req.language or "pt-PT", free_context=req.free_context or "",
    )
