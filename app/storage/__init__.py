"""Storage module — persistencia leve (sqlite3 stdlib) do historico de demos."""

from app.storage.router import router as sessions_router

__all__ = ["sessions_router"]
