"""FastAPI router for commercial diagnostics and sales follow-up."""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.advisor.service import build_commercial_brief

router = APIRouter(prefix="/api/advisor", tags=["advisor"])


class RoiInput(BaseModel):
    consultations_per_day: float = 0
    current_no_show_rate: float = 0
    target_no_show_rate: float = 0
    revenue_per_consultation: float = 0
    monthly_gain: float = 0


class CommercialBriefRequest(BaseModel):
    business_name: str = Field(default="Negocio")
    niche: str = Field(default="dental")
    language: str = Field(default="pt-PT")
    research_query: str = Field(default="")
    extracted: Optional[dict[str, Any]] = None
    extra: Optional[dict[str, Any]] = None
    roi: Optional[RoiInput] = None


@router.post("/brief")
async def commercial_brief(req: CommercialBriefRequest) -> dict[str, Any]:
    payload = req.model_dump()
    roi = payload.get("roi")
    if isinstance(roi, dict):
        payload["roi"] = roi
    return build_commercial_brief(payload)
