"""Constantes leves do modulo de voz (sem deps pesadas).

O `AGENT_NAME` vive aqui (e nao em agent.py) para que o router
``app.voice.router`` possa ser importado apenas com `livekit-api` (leve),
sem arrastar `livekit-agents` / `faster-whisper` / `piper`. Isto permite
mintar tokens LiveKit no control-plane hospedado em cloud, enquanto o
worker pesado (agent.py) so corre localmente.
"""
from __future__ import annotations

AGENT_NAME = "autopme-voice"
