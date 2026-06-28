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
    find_pipeline_page_by_name,
    suggest_package,
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
    skip_if_exists: bool = True  # evita duplicados no funil


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

    business_name = str(req.brief.get("business_name") or "Negocio").strip() or "Negocio"

    # Evitar duplicados: se ja existe um cartao com este nome, devolve-o.
    if req.skip_if_exists:
        existing = await find_pipeline_page_by_name(
            token=token, database_id=database_id, business_name=business_name
        )
        if existing:
            if req.session_id is not None:
                from app.storage import db as storage_db

                storage_db.mark_pushed(req.session_id, existing)
            return {"ok": True, "url": existing, "duplicate": True}

    # Sugerir pacote + valores a partir do ROI quando nao foram fornecidos.
    monthly_gain = float((req.brief.get("roi_summary") or {}).get("monthly_gain") or 0)
    suggestion = suggest_package(monthly_gain)
    package = req.package or suggestion["package"]
    setup_value = req.setup_value if req.setup_value is not None else suggestion["setup_value"]
    retainer_value = req.retainer_value if req.retainer_value is not None else suggestion["retainer_value"]

    properties = build_pipeline_properties(
        req.brief,
        email=req.email,
        phone=req.phone,
        address=req.address,
        state=req.state,
        package=package,
        setup_value=setup_value,
        retainer_value=retainer_value,
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
