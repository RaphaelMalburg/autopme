"""FastAPI router — empurra o prospect da demo para a Pipeline do Notion."""
from __future__ import annotations

import logging
from typing import Any, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.crm.notion import (
    DEFAULT_STATE,
    build_pipeline_properties,
    create_pipeline_page,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crm", tags=["crm"])


class PipelinePushRequest(BaseModel):
    # O brief completo devolvido por POST /api/advisor/brief
    brief: dict[str, Any]
    # Dados de contacto (opcionais) recolhidos na demo
    email: str = ""
    phone: str = ""
    address: str = ""
    state: str = Field(default=DEFAULT_STATE)
    package: str = ""
    setup_value: Optional[float] = None
    retainer_value: Optional[float] = None
    next_contact_date: str = ""  # ISO date, ex: "2026-07-04"
    session_id: Optional[int] = None  # liga ao historico persistido (storage)


@router.get("/status")
async def crm_status() -> dict[str, Any]:
    """Indica se a integracao Notion esta configurada (para o dashboard mostrar/ocultar o botao)."""
    configured = bool((settings.notion_token or "").strip() and (settings.notion_pipeline_database_id or "").strip())
    return {"configured": configured, "target": "notion_pipeline"}


@router.post("/pipeline")
async def push_to_pipeline(req: PipelinePushRequest) -> dict[str, Any]:
    token = (settings.notion_token or "").strip()
    database_id = (settings.notion_pipeline_database_id or "").strip()
    if not token or not database_id:
        raise HTTPException(
            status_code=503,
            detail=(
                "Notion nao configurado. Define NOTION_TOKEN e NOTION_PIPELINE_DATABASE_ID "
                "e partilha a base 'Pipeline de Clientes' com a integracao."
            ),
        )

    properties = build_pipeline_properties(
        req.brief,
        email=req.email,
        phone=req.phone,
        address=req.address,
        state=req.state,
        package=req.package,
        setup_value=req.setup_value,
        retainer_value=req.retainer_value,
        next_contact_date=req.next_contact_date,
    )

    try:
        result = await create_pipeline_page(
            token=token, database_id=database_id, properties=properties
        )
    except httpx.HTTPStatusError as e:
        detail = ""
        try:
            detail = e.response.json().get("message", "")
        except Exception:
            detail = e.response.text[:300] if e.response is not None else ""
        logger.error("Notion pipeline push failed: %s %s", e, detail)
        raise HTTPException(status_code=502, detail=f"Notion recusou o pedido: {detail}") from e
    except httpx.HTTPError as e:
        logger.error("Notion pipeline push network error: %s", e)
        raise HTTPException(status_code=502, detail="Falha de rede ao contactar o Notion.") from e

    if req.session_id is not None:
        from app.storage import db as storage_db

        storage_db.mark_pushed(req.session_id, result.get("url", ""))

    return result
