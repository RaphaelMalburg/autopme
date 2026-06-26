"""Entry point do worker do agente de voz.

Correr (depois de instalar deps e arrancar o LiveKit Server em Docker):
    python -m app.voice.main download-files   # 1x: descarrega o modelo Silero VAD
    python -m app.voice.main                  # arranca o worker (equivale a 'start')

Isto regista o agente 'autopme-voice' no LiveKit Server local
(ws://localhost:7880, devkey/secret) e fica a espera de dispatches criados por
POST /api/voice/call/start (ver app/voice/router.py).

Para uma chamada de demo: chamar /api/voice/call/start e abrir o token devolvido
no dashboard (LiveKit Web SDK) — o agente e dispatchado para a room.
"""
from __future__ import annotations

import logging
import os
import sys

from livekit.agents import cli

from app.config import settings
from app.voice.agent import server


def _export_livekit_env() -> None:
    """cli.run_app le LIVEKIT_* do env; garantir que usam os valores de settings."""
    os.environ.setdefault("LIVEKIT_URL", settings.livekit_url)
    os.environ.setdefault("LIVEKIT_API_KEY", settings.livekit_api_key)
    os.environ.setdefault("LIVEKIT_API_SECRET", settings.livekit_api_secret)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    _export_livekit_env()
    # cli.run_app espera um subcomando (start | dev | console | download-files...).
    # Sem argumentos, arrancar em modo 'start' (producao local / espera por jobs).
    if len(sys.argv) == 1:
        sys.argv = [sys.argv[0], "start"]
    cli.run_app(server)


if __name__ == "__main__":
    main()
