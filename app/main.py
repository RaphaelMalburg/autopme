"""AutoPME Demo Studio — FastAPI entrypoint.

Monta todos os routers:
- /api/scenarios  (cenario por nicho)        — app.scenarios
- /api/voice      (LiveKit call/start)        — app.voice   (lazy: pesado)
- /api/whatsapp   (Baileys + ingestao)       — app.whatsapp
- /               (dashboard single-page)    — app.dashboard

O agente de voz corre como WORKER SEPARADO: `python -m app.voice.main`
(precisa de livekit-agents + livekit-api instalados). O FastAPI so expoe
o endpoint /api/voice/call/start, importado de forma lazy para nao partir
o arranque se as deps pesadas ainda nao estiverem instaladas.
"""
import logging

from fastapi import FastAPI

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AutoPME Demo Studio", version="0.1.0")


@app.get("/api/health")
async def health():
    return {"status": "ok", "env": settings.app_env}


# --- Routers leves (sempre disponiveis) ---
from app.scenarios.router import router as scenarios_router  # noqa: E402

app.include_router(scenarios_router)

from app.whatsapp.router import router as whatsapp_router  # noqa: E402

app.include_router(whatsapp_router)

from app.dashboard import dashboard_router  # noqa: E402

app.include_router(dashboard_router)  # sem prefix: GET / serve o UI

# --- Router de voz (lazy: livekit-agents/livekit-api podem nao estar instalados) ---
try:
    from app.voice import voice_router  # noqa: E402

    app.include_router(voice_router)
    logger.info("Voice router montado em /api/voice")
except Exception as e:  # deps pesadas em falta
    logger.warning("Voice router NAO montado (deps em falta): %s", e)
    logger.warning("Instala: pip install livekit-agents livekit-api ; e arranca o worker: python -m app.voice.main")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.app_env == "development",
    )
