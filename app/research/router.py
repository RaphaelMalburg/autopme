"""FastAPI router: POST /api/research/prospect.

Pesquisa um prospect na web (OpenRouter plugin `web`) e devolve dados estruturados
+ um `extra` pronto a alimentar o construtor de cenarios. PT-PT nas mensagens.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.research.prospect_research import research_prospect

logger = logging.getLogger(__name__)

research_router = APIRouter(prefix="/api/research", tags=["research"])


class ProspectResearchRequest(BaseModel):
    query: str = Field(..., description="Nome do negocio + localizacao/website, ex.: 'Clinica Dentaria Sorriso Porto'")
    niche: Optional[str] = Field(default=None, description="Nicho sugerido (opcional)")


@research_router.post("/prospect")
async def research_prospect_endpoint(req: ProspectResearchRequest) -> dict[str, Any]:
    """Pesquisa um prospect na web e devolve contexto 'mastigado' para a demo."""
    query = (req.query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Indique um termo de pesquisa (nome do negocio).")
    try:
        result = await research_prospect(query=query, niche_hint=req.niche)
    except Exception as e:
        logger.error("research_prospect unexpected error: %s", e)
        raise HTTPException(status_code=502, detail=f"falha na pesquisa: {e}") from e
    return result
