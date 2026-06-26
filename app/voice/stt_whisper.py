"""STT local com faster-whisper + plugin livekit-agents.

faster-whisper corre em CPU (WhisperModel, compute_type int8 para demo leve).
Como e batch (nao streaming nativo), implementamos _recognize_impl e envolvemos
com stt.StreamAdapter(stt=self, vad=vad) no agent.py — o padrao do livekit-agents
para STTs nao-streaming (o VAD segmenta o audio e chama recognize por segmento).

Runtime deps (instalar antes de correr; validacao runtime pelo orquestrador):
    pip install faster-whisper numpy
O modelo (settings.whisper_model) e descarregado automaticamente no 1o uso.
Para demo leve: WHISPER_MODEL=base ou small no .env (large-v3 e pesado).
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

WHISPER_SAMPLE_RATE = 16000

_model_cache: dict[str, Any] = {}


def _load_whisper_model(model_name: str):
    """Carrega faster-whisper sob demanda (import pesado)."""
    from faster_whisper import WhisperModel  # type: ignore

    # cpu + int8: o mais leve para demo em portatil sem GPU.
    return WhisperModel(model_name, device="cpu", compute_type="int8")


def _get_model(model_name: str):
    if model_name not in _model_cache:
        _model_cache[model_name] = _load_whisper_model(model_name)
    return _model_cache[model_name]


def _frames_to_float32(frames: list) -> Any:
    """Converte uma lista de rtc.AudioFrame em numpy float32 16kHz mono."""
    import numpy as np  # type: ignore
    from livekit import rtc  # type: ignore

    if not frames:
        return np.zeros(0, dtype=np.float32)
    merged = rtc.combine_audio_frames(frames) if len(frames) > 1 else frames[0]
    arr = np.frombuffer(merged.data, dtype=np.int16)
    if merged.num_channels > 1:
        arr = arr.reshape(-1, merged.num_channels).mean(axis=1)
    arr = arr.astype(np.float32) / 32768.0
    if merged.sample_rate != WHISPER_SAMPLE_RATE and len(arr) > 0:
        # resample simples por interpolacao de indices para 16k (demo, sem scipy)
        ratio = WHISPER_SAMPLE_RATE / float(merged.sample_rate)
        n = max(1, int(len(arr) * ratio))
        idx = np.linspace(0, len(arr) - 1, n).astype(int)
        arr = arr[idx]
    return arr


def _transcribe_sync(model: Any, audio: Any, language: str) -> str:
    segments, _info = model.transcribe(
        audio, language=language or None, beam_size=1, vad_filter=True
    )
    return " ".join(seg.text for seg in segments).strip()


async def transcribe_buffer(frames: list, *, language: str | None = None) -> str:
    """STT standalone (testavel): lista de AudioFrame -> texto."""
    if not frames:
        return ""
    lang = language or settings.whisper_language
    audio = _frames_to_float32(frames)
    if len(audio) == 0:
        return ""
    model = _get_model(settings.whisper_model)
    return await asyncio.to_thread(_transcribe_sync, model, audio, lang)


# --- Plugin nativo livekit-agents ------------------------------------------------

try:
    from livekit import rtc as _rtc
    from livekit.agents.stt import (
        STT,
        SpeechData,
        SpeechEvent,
        SpeechEventType,
        STTCapabilities,
    )
    from livekit.agents.types import NOT_GIVEN
    from livekit.agents.utils import is_given

    _LIVEKIT_AVAILABLE = True
except ImportError:
    _LIVEKIT_AVAILABLE = False
    STT = object  # type: ignore[assignment,misc]


if _LIVEKIT_AVAILABLE:

    async def _collect_frames(buffer: Any) -> list:
        if isinstance(buffer, _rtc.AudioFrame):
            return [buffer]
        if hasattr(buffer, "__aiter__"):
            out: list = []
            async for f in buffer:
                out.append(f)
            return out
        try:
            return list(buffer)
        except TypeError:
            return []

    def _speech_event(text: str, language: str) -> SpeechEvent:
        try:
            data = SpeechData(language=language, text=text, confidence=1.0)
        except Exception:
            data = SpeechData(language="pt", text=text, confidence=1.0)
        return SpeechEvent(type=SpeechEventType.FINAL_TRANSCRIPT, alternatives=[data])

    class WhisperSTT(STT):  # type: ignore[misc]
        """STT batch faster-whisper. Envolver com stt.StreamAdapter para streaming."""

        def __init__(
            self, *, model_name: str | None = None, language: str | None = None
        ) -> None:
            super().__init__(
                capabilities=STTCapabilities(
                    streaming=False, interim_results=False, offline_recognize=True
                )
            )
            self._model_name = model_name or settings.whisper_model
            self._language = language or settings.whisper_language
            self._model: Any = None

        @property
        def model(self) -> str:
            return self._model_name

        @property
        def provider(self) -> str:
            return "faster-whisper"

        def _ensure_model(self):
            if self._model is None:
                self._model = _get_model(self._model_name)
            return self._model

        async def _recognize_impl(
            self, buffer: Any, *, language: Any = NOT_GIVEN, conn_options: Any
        ) -> SpeechEvent:
            frames = await _collect_frames(buffer)
            if not frames:
                return _speech_event("", self._language)
            lang = language if is_given(language) else self._language
            lang = lang or self._language or "pt"
            audio = _frames_to_float32(frames)
            if len(audio) == 0:
                return _speech_event("", lang)
            model = self._ensure_model()
            text = await asyncio.to_thread(_transcribe_sync, model, audio, lang)
            return _speech_event(text, lang)

else:

    class WhisperSTT:  # type: ignore[no-redef]
        """Stub quando livekit-agents nao esta instalado."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError(
                "livekit-agents nao instalado; instale-o para usar WhisperSTT"
            )
