"""Dashboard UI router for the AutoPME Demo Studio.

Serves the single-page demo UI. The orchestrator mounts this router at the
app root (no /api prefix) in app/main.py, e.g.:

    from app.dashboard import dashboard_router
    app.include_router(dashboard_router)

Routes:
- GET /                 -> app/dashboard/static/index.html
- GET /static/{path}    -> static assets from app/dashboard/static/

The page is self-contained (inline CSS/JS; LiveKit Web SDK via CDN) and calls
the shared API routers under /api/* on the same origin.
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

_STATIC_DIR = Path(__file__).resolve().parent / "static"
_INDEX = _STATIC_DIR / "index.html"

router = APIRouter(tags=["dashboard"])


@router.get("/", include_in_schema=False)
async def index() -> FileResponse:
    """Serve the single-page dashboard."""
    return FileResponse(str(_INDEX))


@router.get("/static/{file_path:path}", include_in_schema=False)
async def static_file(file_path: str) -> FileResponse:
    """Serve a static asset from app/dashboard/static/ (path-traversal safe)."""
    base = _STATIC_DIR
    try:
        full = (base / file_path).resolve()
    except (ValueError, OSError):
        raise HTTPException(status_code=404)
    # Garantir que o alvo fica dentro do diretório static.
    if full != base and base not in full.parents:
        raise HTTPException(status_code=404)
    if not full.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(str(full))
