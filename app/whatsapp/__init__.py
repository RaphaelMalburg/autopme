"""WhatsApp module: Baileys gateway client, document ingestion, emailer, FastAPI router.

Exposes ``router`` lazily so that submodules (ingestion, emailer, client, openrouter_vision)
can be imported without requiring FastAPI/python-multipart to be installed. The orchestrator
integrates the router via::

    from app.whatsapp.router import router as whatsapp_router
    app.include_router(whatsapp_router)

or::

    from app.whatsapp import router as whatsapp_router
"""
__all__ = ["router"]


def __getattr__(name):
    if name == "router":
        from app.whatsapp.router import router as _router
        return _router
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
