"""AutoPME Demo Studio — FastAPI entrypoint.

Monta todos os routers:
- /api/scenarios  (cenario por nicho, multi-idioma)  — app.scenarios
- /api/research   (pesquisa prospect na web)          — app.research
- /api/voice      (voz modular: Vapi | browser)       — app.voice (providers)
- /api/whatsapp   (Baileys + ingestao)               — app.whatsapp
- /               (dashboard single-page)            — app.dashboard

Voz: provider abstraido em app/voice/providers/. Vapi (web call, voz neural
Azure) e ativo se VOICE_PROVIDER=vapi + chaves configuradas; senao browser
(LLM + Web Speech API). Sem deps pesadas (livekit) no control-plane.
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

from app.research import research_router  # noqa: E402

app.include_router(research_router)  # POST /api/research/prospect (pesquisa web)

from app.advisor import advisor_router  # noqa: E402

app.include_router(advisor_router)  # POST /api/advisor/brief

# Chat de voz (LLM multi-idioma) — usado pelo provider browser e como fallback.
from app.voice.chat_router import chat_router  # noqa: E402

app.include_router(chat_router)  # POST /api/voice/chat

from app.dashboard import dashboard_router  # noqa: E402

app.include_router(dashboard_router)  # sem prefix: GET / serve o UI

# --- Router de voz modular (Vapi | browser; sem deps pesadas) ---
from app.voice import voice_router  # noqa: E402

app.include_router(voice_router)  # /api/voice/call/start, /api/voice/providers, /api/voice/call/end
logger.info("Voice router montado em /api/voice (provider: %s)", (settings.voice_provider or "vapi"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.app_env == "development",
    )
