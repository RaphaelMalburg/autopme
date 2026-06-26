"""Dashboard UI module for AutoPME Demo Studio.

Exposes ``dashboard_router`` for the orchestrator to mount in app/main.py:

    from app.dashboard import dashboard_router
    app.include_router(dashboard_router)
"""
from app.dashboard.router import router as dashboard_router

__all__ = ["dashboard_router"]
