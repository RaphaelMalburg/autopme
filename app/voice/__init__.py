"""Modulo de voz (LiveKit) da demo AutoPME.

Expoe `voice_router` (FastAPI APIRouter prefix /api/voice) para integracao em
app/main.py:

    from app.voice import voice_router
    app.include_router(voice_router)

Componentes:
- agent.py        : agente LiveKit (VAD Silero + STT faster-whisper + LLM
                    OpenRouter + TTS Piper) + worker entrypoint (server).
- llm_openrouter  : cliente OpenRouter (SSE) + plugin LLM.
- stt_whisper     : STT faster-whisper + plugin STT.
- tts_piper       : TTS Piper pt-PT + plugin TTS.
- router.py       : POST /api/voice/call/start (cria room + dispatch + token).
- main.py         : arranca o worker (python -m app.voice.main).
- smoke_token.py  : testa a geracao de token (python -m app.voice.smoke_token).
"""
from app.voice.router import voice_router

__all__ = ["voice_router"]
