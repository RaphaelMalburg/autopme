"""FastAPI router — historico e metricas de demos persistidos."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.storage import db

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class SaveSessionRequest(BaseModel):
    brief: dict[str, Any]
    research_query: str = ""
    language: str = ""


@router.post("")
async def save_session(req: SaveSessionRequest) -> dict[str, Any]:
    session_id = db.save_session(
        req.brief, research_query=req.research_query, language=req.language
    )
    return {"ok": session_id is not None, "session_id": session_id}


@router.get("")
async def list_sessions(limit: int = 50) -> dict[str, Any]:
    return {"sessions": db.list_sessions(limit=limit)}


@router.get("/stats")
async def session_stats() -> dict[str, Any]:
    return db.stats()
